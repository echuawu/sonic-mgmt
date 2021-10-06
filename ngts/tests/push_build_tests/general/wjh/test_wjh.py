import time
import pytest
import allure
import logging
import json
from infra.tools.validations.traffic_validations.iperf.iperf_runner import IperfChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
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


def check_if_channel_enabled(cli_object, engines, channel, channel_type):
    """
    A function that checks if the received channel is available in WJH
    :param engines: engines fixture
    :param channel: channel name
    :param channel_type: channel type
    :param cli_object: cli_object
    """

    if channel == "buffer" and SonicGeneralCli.is_spc1(cli_object, engines.dut):
        pytest.skip("buffer channel is not supported in SPC1.")

    if channel not in pytest.CHANNEL_CONF:
        pytest.fail("{} channel is not confiugred on WJH.".format(channel))
    if channel_type not in pytest.CHANNEL_CONF[channel]['type']:
        pytest.fail("{} {} channel type is not confiugred on WJH.".format(channel, channel_type))


def get_parsed_table(dut, cmd, table_type):
    output = dut.run_cmd(cmd)
    parser = table_parser_info[table_type]
    table = generic_sonic_output_parser(output, headers_ofset=parser['headers_ofset'],
                                        len_ofset=parser['len_ofset'],
                                        data_ofset_from_start=parser['data_ofset_from_start'],
                                        column_ofset=parser['column_ofset'],
                                        output_key=parser['output_key'])
    return table


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
        # If entry is a list, it means that the message is longer then one line,
        # but all rest of info is in the first entry
        if isinstance(entry, list):
            entry = entry[0]
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


def validate_wjh_table(engines, cmd, table_type, interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac):
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
    table = get_parsed_table(engines.dut, cmd, table_type)
    result = check_if_entry_exists(table, interface, dst_ip,
                                   src_ip, proto, drop_reason, dst_mac, src_mac)
    if result is not True:
        pytest.fail("Could not find drop in WJH {} table".format(table_type))


def do_raw_test(engines, cli_object, channel, channel_type, interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac, command):
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
    check_if_channel_enabled(cli_object, engines, channel, channel_type)

    retry_call(validate_wjh_table, fargs=[engines, command, 'raw', interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac],
               tries=3, delay=3, logger=logger)


def do_agg_test(engines, cli_object, channel, channel_type, interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac, command):
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
    check_if_channel_enabled(cli_object, engines, channel, channel_type)

    retry_call(validate_wjh_table, fargs=[engines, command, 'agg', interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac],
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
        do_raw_test(engines=engines, cli_object=cli_object, channel='buffer', channel_type='raw', interface=interfaces.dut_hb_2, dst_ip=ha_ip, src_ip=hb_ip, proto=proto, drop_reason=drop_reason_message,
                    dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll buffer')

    with allure.step('Sending iPerf traffic'):
        logger.info('Sending iPerf traffic')
        IperfChecker(players, validation).run_validation()

    with allure.step('Validating WJH aggregated table output'):
        do_agg_test(engines=engines, cli_object=cli_object, channel='buffer', channel_type='aggregate', interface=interfaces.dut_hb_2, dst_ip=ha_ip, src_ip=hb_ip, proto=proto, drop_reason=drop_reason_message,
                    dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll buffer --aggregate')


@pytest.mark.wjh
@pytest.mark.build
@allure.title('WJH L1 Raw test case')
def test_l1_raw_drop(engines, topology_obj, interfaces):
    cli_object = topology_obj.players['dut']['cli']
    port = SonicInterfaceCli.get_active_phy_port(engines)
    if not port:
        pytest.skip("Could not find port in active state. Skipping the test.")
    try:
        with allure.step('Shutting down {} interface'.format(port)):
            SonicInterfaceCli.disable_interface(engines.dut, port)

        drop_reason_message = 'Generic L1 event - Check layer 1 aggregated information'
        na = 'N/A'
        with allure.step('Validating WJH raw table output'):
            do_raw_test(engines=engines, cli_object=cli_object, channel='layer-1', channel_type='raw', interface=port,
                        dst_ip=na, src_ip=na, proto=na, drop_reason=drop_reason_message,
                        dst_mac=na, src_mac=na, command='show what-just-happened poll layer-1')
    finally:
        SonicInterfaceCli.enable_interface(engines.dut, port)


@pytest.mark.wjh
@pytest.mark.build
@allure.title('WJH L1 Aggregated test case')
def test_l1_agg_drop(engines, topology_obj, players):
    cli_object = topology_obj.players['dut']['cli']
    check_if_channel_enabled(cli_object, engines, 'layer-1', 'aggregate')
    port = SonicInterfaceCli.get_active_phy_port(engines)
    if not port:
        pytest.skip("Could not find port in active state. Skipping the test.")
    with allure.step('Shutting down {} interface'.format(port)):
        SonicInterfaceCli.disable_interface(engines.dut, port)
    drop_reason_message = 'Port admin down - Validate port configuration'
    na = 'N/A'
    try:
        with allure.step('Validating WJH L1 Aggregated table output with down port'):
            table = get_parsed_table(engines.dut, 'show what-just-happened poll layer-1 --aggregate', 'agg')
            verify_l1_agg_drop_exists(table, port, 'Down', drop_reason_message)

        with allure.step('Starting up {} interface'.format(port)):
            SonicInterfaceCli.enable_interface(engines.dut, port)
            retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, [port]], tries=10, delay=5, logger=logger)
            time.sleep(3)

        with allure.step('Validating WJH L1 Aggregated table output with up port'):
            table = get_parsed_table(engines.dut, 'show what-just-happened poll layer-1 --aggregate', 'agg')
            verify_l1_agg_drop_exists(table, port, 'Up', drop_reason_message)

    finally:
        with allure.step('Starting up {} interface'.format(port)):
            SonicInterfaceCli.enable_interface(engines.dut, port)


def verify_l1_agg_drop_exists(table, port, state, drop_reason_message):
    entry_exists = False
    for entry in table:
        if (table[entry]['State'] == state and
            table[entry]['Port'] == port and
            table[entry]['Down Reason - Recommended Action'] and
                int(table[entry]['State Change']) > 0):
                entry_exists = True
                break
    if not entry_exists:
        pytest.fail("Could not find L1 drop on WJH aggregated table.")
    return entry


@pytest.mark.wjh
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('WJH L2 test case')
def test_l2_src_mac_equals_dst_mac(engines, topology_obj, players, interfaces, hb_dut_2_mac):
    cli_object = topology_obj.players['dut']['cli']
    src_ip = '1.1.1.1'
    dst_ip = '40.0.0.3'
    count = 50
    pkt = 'Ether(src="{}", dst="{}")/IP(dst="{}", src="{}")/TCP()'.format(hb_dut_2_mac, hb_dut_2_mac, dst_ip, src_ip)
    drop_reason_message = 'Source MAC equals destination MAC - Bad packet was received from peer'
    try:
        with allure.step('Sending packet with src mac = dst mac'):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2), 'packets': pkt, 'count': 1}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L2 raw table output'):
            do_raw_test(engines=engines, cli_object=cli_object, channel='forwarding', channel_type='raw', interface=interfaces.dut_ha_2, dst_ip=dst_ip, src_ip=src_ip, proto='tcp', drop_reason=drop_reason_message,
                        dst_mac=hb_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll forwarding')

        with allure.step('Sending {} packets with src mac = dst mac'.format(count)):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2), 'packets': pkt, 'count': count}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L2 aggregated table output'):
            do_agg_test(engines=engines, cli_object=cli_object, channel='forwarding', channel_type='aggregate', interface=interfaces.dut_ha_2, dst_ip=dst_ip, src_ip=src_ip, proto='tcp', drop_reason=drop_reason_message,
                        dst_mac=hb_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll forwarding --aggregate')

    except Exception as e:
        pytest.fail("Could not finish the test.\nAborting!.")


@pytest.mark.wjh
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('WJH L3 test case')
def test_l3_dst_ip_is_loopback(engines, topology_obj, players, interfaces):
    cli_object = topology_obj.players['dut']['cli']
    src_mac = '00:11:22:33:44:55'
    broadcast_mac = 'ff:ff:ff:ff:ff:ff'
    loopback_ip = '127.0.0.1'
    src_ip = '40.0.0.2'
    count = 50
    pkt = 'Ether(src="{}", dst="{}")/IP(dst="{}", src="{}")/TCP()'.format(src_mac, broadcast_mac, loopback_ip, src_ip)
    drop_reason_message = 'Destination IP is loopback address - Bad packet was received from the peer'
    try:
        with allure.step('Sending loopback dst ip packet'):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2), 'packets': pkt, 'count': 1}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L3 raw table output'):
            do_raw_test(engines=engines, cli_object=cli_object, channel='forwarding', channel_type='raw', interface=interfaces.dut_ha_2, dst_ip=loopback_ip, src_ip=src_ip, proto='tcp', drop_reason=drop_reason_message,
                        dst_mac=broadcast_mac, src_mac=src_mac, command='show what-just-happened poll forwarding')

        with allure.step('Sending {} loopback dst ip packets'.format(count)):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2), 'packets': pkt, 'count': 50}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L3 aggregated table output'):
            do_agg_test(engines=engines, cli_object=cli_object, channel='forwarding', channel_type='aggregate', interface=interfaces.dut_ha_2, dst_ip=loopback_ip, src_ip=src_ip, proto='tcp', drop_reason=drop_reason_message,
                        dst_mac=broadcast_mac, src_mac=src_mac, command='show what-just-happened poll forwarding --aggregate')

    except Exception as e:
        pytest.fail("Could not finish the test.\nAborting!.")
