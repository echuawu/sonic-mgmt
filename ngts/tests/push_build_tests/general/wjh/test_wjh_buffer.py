import time
import pytest
import allure
import logging
import json
from infra.tools.validations.traffic_validations.iperf.iperf_runner import IperfChecker
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.constants.constants import SonicConst
from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


pytest.CHANNEL_CONF = None
logger = logging.getLogger()


table_parser_info = {
    'raw': {'headers_ofset': 0,
            'len_ofset': 2,
            'data_ofset_from_start': 3,
            'column_ofset': 1,
            'output_key': '#'
            },
    'agg': {'headers_ofset': 3,
            'len_ofset': 4,
            'data_ofset_from_start': 5,
            'column_ofset': 1,
            'output_key': '#'
            }
}


@pytest.fixture(scope='module', autouse=True)
def check_global_configuration(engines):
    """
    An autouse fixture to check the global configurations of WJH.
    :param engines: engines fixture
    """
    config_db = SonicGeneralCli.get_config_db(engines.dut)
    wjh = config_db.get('WJH', {})
    try:
        with allure.step('Validating debug mode in WJH'):
            wjh_global = wjh.get('global')
            if wjh_global.get('mode') != 'debug':
                pytest.fail("Debug mode is not enabled. Skipping test.")
    except Exception as e:
        pytest.fail("Could not fetch global configuration information.")


@pytest.fixture(scope='module', autouse=True)
def get_channel_configuration(engines):
    """
    An autouse fixture to check the channel configurations of WJH.
    :param engines: engines fixture
    """
    pytest.CHANNEL_CONF = SonicGeneralCli.get_config_db(engines.dut).get('WJH_CHANNEL', {})


@pytest.fixture(scope='module', autouse=True)
def check_feature_enabled(engines):
    """
    An autouse fixture to check if WJH fixture is enabled
    :param engines: engines fixture
    """
    with allure.step('Valdating WJH feature is installed and enabled on the DUT'):
        config_db = SonicGeneralCli.get_config_db(engines.dut)
        features = config_db.get('FEATURE', {})
        if 'what-just-happened' not in features or features['what-just-happened']['state'] != 'enabled':
            pytest.skip("what-just-happened feature is not available. Skipping the test.")


def check_if_buffer_enabled(cli_object, engines, channel_type):
    """
    A function that checks if buffer channel is available in WJH
    :param engines: engines fixture
    :param channel_type: channel type
    :param cli_object: cli_object
    """
    if SonicGeneralCli.is_spc1(cli_object, engines.dut):
        pytest.skip("buffer channel is not supported in SPC1.")
    # TODO: when we will have a supporting image, (e.g. 202012.Y),
    # the below statement should be changed to:
    # if "buffer" not in ... and version < 202012.Y
    # skip
    # else
    # fail
    if "buffer" not in pytest.CHANNEL_CONF:
        pytest.skip("buffer channel is not confiugred on WJH.")
    if pytest.CHANNEL_CONF['buffer']['type'].find(channel_type) == -1:
        pytest.fail("buffer {} channel type is not confiugred on WJH.".format(channel_type))


@pytest.fixture(scope='module')
def wjh_buffer_configuration(topology_obj, engines, interfaces):
    """
    Pytest fixture which is doing configuration fot WJH Buffer test case
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    """
    cli_object = topology_obj.players['dut']['cli']

    with allure.step('Check that links are in UP state'.format()):
        ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ports_list], tries=10, delay=10,
                   logger=logger)

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, [interfaces.dut_ha_1,
                                                                                          interfaces.dut_hb_2,
                                                                                          interfaces.dut_ha_2,
                                                                                          interfaces.dut_hb_1])
    with allure.step('Configuring dut_ha_2 speed to be 10G, and dut_hb_2 to be 25G'):
        interfaces_config_dict = {
            'dut': [{'iface': interfaces.dut_ha_2, 'speed': '10G',
                     'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_2, '10G')},
                    {'iface': interfaces.dut_hb_2, 'speed': '25G',
                     'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '25G')}
                    ]
        }

    logger.info('Starting WJH Buffer configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    logger.info('WJH Buffer configuration completed')

    with allure.step('Doing config save'):
        logger.info('Doing config save')
        cli_object.general.save_configuration(engines.dut)

    yield

    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
    logger.info('Doing config save after cleanup')
    cli_object.general.save_configuration(engines.dut)
    logger.info('WJH Buffer cleanup completed')


def check_if_entry_exists(table, interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac):
    """
    A function that checks if an entry with variables exists in the recieved table
    :param table: a table made of dictionary
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason: drop reason
    :param dst_mac: dst mac
    :param src_mac: src mac
    """
    for key in table:
        entry = table[key]
        if (entry['sPort'] == interface and
            entry['Src IP:Port'].split(':')[0] == src_ip and
            entry['Dst IP:Port'].split(':')[0] == dst_ip and
            # TODO: should be uncommented when issue is fixed:
            # in aggregate table the proto shown as 'ip' instaed of 'udp'
            # entry['IP Proto'] == proto and
            entry['dMAC'] == dst_mac and
            entry['sMAC'] == src_mac and
                entry['Drop reason - Recommended action'] in drop_reason):
            return True

    return False


def validate_wjh_table(engines, cmd, table_type, interfaces, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac):
    """
    A function that checks the WJH table
    :param engines: engines fixture
    :param cmd: command to execute on DUT
    :param table_type: table type
    :param interfaces: interfaces
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason: drop reason
    :param dst_mac: dst mac
    :param src_mac: src mac
    """
    output = engines.dut.run_cmd(cmd)
    parser = table_parser_info[table_type]
    table = generic_sonic_output_parser(output, parser['headers_ofset'],
                                        parser['len_ofset'],
                                        parser['data_ofset_from_start'],
                                        parser['column_ofset'],
                                        parser['output_key'])

    result = check_if_entry_exists(table, interfaces.dut_hb_2, dst_ip,
                                   src_ip, proto, drop_reason, dst_mac, src_mac)
    assert result == False, "Could not find drop in WJH {} table".format(table_type)


def do_raw_test(engines, cli_object, interfaces, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac, command):
    """
    A function that checks the WJH feature with raw channel type
    :param engines: engines fixture
    :param cli_object: cli_object
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason: drop reason
    :param dst_mac: dst mac
    :param src_mac: src mac
    :param command: raw command
    """
    check_if_buffer_enabled(cli_object, engines, 'raw')

    retry_call(validate_wjh_table, fargs=[engines, command, 'raw', interfaces, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac],
               tries=3, delay=3, logger=logger)


def do_agg_test(engines, cli_object, interfaces, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac, command):
    """
    A function that checks the WJH feature with aggregated channel type
    :param engines: engines fixture
    :param cli_object: cli_object
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason: drop reason
    :param dst_mac: dst mac
    :param src_mac: src mac
    :param command: aggregate command
    """
    check_if_buffer_enabled(cli_object, engines, 'aggregate')

    retry_call(validate_wjh_table, fargs=[engines, command, 'agg', interfaces, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac],
               tries=3, delay=3, logger=logger)


@pytest.mark.wjh
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('WJH Buffer test case')
def test_buffer_tail_drop(engines, topology_obj, players, interfaces, wjh_buffer_configuration, ha_dut_2_mac, hb_dut_2_mac):
    """
    This test will configure the DUT and hosts to generate buffer drops

        ha                  DUT                     hb
    __________          ____________             __________
    |         |         |           |            |         |
    |         |         |           |            |         |
    |         |---------| TD        |------------|         |
    |_________|   10G   |___________|    25G     |_________|

    """

    validation = {
        'server': 'ha',
        'client': 'hb',
        'client_args': {
            'server_address': '40.0.0.2',
            'duration': '30',
            'bandwidth': '20G',
            'protocol': 'UDP',
            'length': '65507',
            'window': '415k'
        },
        'expect': [
            {
                'parameter': 'loss_packets',
                'operator': '>=',
                'type': 'int',
                'value': '0'
            }
        ]
    }

    ping_validation = {'sender': 'hb', 'args': {'count': 3, 'dst': '40.0.0.2'}}
    ping_checker = PingChecker(players, ping_validation)
    retry_call(ping_checker.run_validation, fargs=[], tries=5, delay=5, logger=logger)

    with allure.step('Sending iPerf traffic'):
        logger.info('Sending iPerf traffic')
        IperfChecker(players, validation).run_validation()

    ha_ip = '40.0.0.2'
    hb_ip = '40.0.0.3'
    proto = 'udp'
    drop_reason_message = 'Tail drop - Monitor network congestion'

    cli_object = topology_obj.players['dut']['cli']
    with allure.step('Validating WJH raw table output'):
        do_raw_test(engines=engines, cli_object=cli_object, interfaces=interfaces, dst_ip=ha_ip, src_ip=hb_ip, proto=proto, drop_reason=drop_reason_message,
                    dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll buffer')

    with allure.step('Sending iPerf traffic'):
        logger.info('Sending iPerf traffic')
        IperfChecker(players, validation).run_validation()

    with allure.step('Validating WJH aggregated table output'):
        do_agg_test(engines=engines, cli_object=cli_object, interfaces=interfaces, dst_ip=ha_ip, src_ip=hb_ip, proto=proto, drop_reason=drop_reason_message,
                    dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll buffer --aggregate')
