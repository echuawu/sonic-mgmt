import time
import pytest
import allure
import logging
from infra.tools.validations.traffic_validations.iperf.iperf_runner import IperfChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from retry.api import retry_call
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.wjh_buffer_config_template import WjhBufferConfigTemplate
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.common.checkers import is_feature_ready
from ngts.constants.constants import SonicConst


pytest.CHANNEL_CONF = None
logger = logging.getLogger()

drop_reason_dict = {"tail_drop": "Tail drop - Monitor network congestion",
                    "buffer_congestion": "Port TC Congestion Threshold Crossed - Monitor network congestion",
                    "buffer_latency": "Packet Latency Threshold Crossed - Monitor network congestion"}

table_parser_info = {
    'raw':
        {'headers_ofset': 0,
         'header_len': 2,
         'len_ofset': 2,
         'data_ofset_from_start': 3,
         'column_ofset': 1,
         'output_key': '#'
         },
    'raw_buffer_info':
        {'headers_ofset': 1,
         'header_len': 1,
         'len_ofset': 2,
         'data_ofset_from_start': 3,
         'column_ofset': 1,
         'output_key': '#'
         },
    'agg':
        {'headers_ofset': 2,
         'header_len': 1,
         'len_ofset': 3,
         'data_ofset_from_start': 4,
         'column_ofset': 1,
         'output_key': '#'
         },
    'agg_buffer_info':
        {'headers_ofset': 1,
         'header_len': 1,
         'len_ofset': 2,
         'data_ofset_from_start': 3,
         'column_ofset': 1,
         'output_key': '#'
         }
}


@pytest.fixture(scope='module', autouse=True)
def disable_doroce(cli_objects):
    """
    Disable doroce before test in case when doroce enabled and enable back after test
    :param cli_objects: cli_objects fixture
    """
    is_doroce_enabled = cli_objects.dut.doroce.is_doroce_configuration_enabled()

    if is_doroce_enabled:
        cli_objects.dut.doroce.disable_doroce()

    yield

    if is_doroce_enabled:
        cli_objects.dut.doroce.config_doroce_lossless_double_ipool()


@pytest.fixture(scope='module', autouse=True)
def check_global_configuration(engines, check_feature_enabled):
    """
    An autouse fixture to check the global configurations of WJH.
    :param engines: engines fixture
    :param check_feature_enabled: check_feature_enabled fixture
    """
    global_config = engines.dut.run_cmd('show what-just-happened configuration global')
    wjh_global = generic_sonic_output_parser(global_config)[0]
    try:
        with allure.step('Validating debug mode in WJH'):
            if wjh_global.get('Mode') != 'debug':
                pytest.fail("Debug mode is not enabled. Skipping test.")
    except Exception as e:
        pytest.fail("Could not fetch global configuration information.")


@pytest.fixture(scope='module', autouse=True)
def get_channel_configuration(engines, check_feature_enabled):
    """
    An autouse fixture to check the channel configurations of WJH.
    :param engines: engines fixture
    :param check_feature_enabled: check_feature_enabled fixture
    """
    channels_config = engines.dut.run_cmd('show what-just-happened configuration channels')
    pytest.CHANNEL_CONF = generic_sonic_output_parser(channels_config, output_key="Channel")


@pytest.fixture(scope='module')
def check_feature_enabled(cli_objects):
    """
    An autouse fixture to check if WJH fixture is enabled
    :param cli_objects: cli_objects fixture
    """
    with allure.step('Validating WJH feature is installed and enabled on the DUT'):
        status, msg = is_feature_ready(cli_objects, feature_name='what-just-happened',
                                       docker_name='what-just-happened')
        if not status:
            pytest.skip(f"{msg} Skipping the test.")

    with allure.step('Validating WJH docker is UP'):
        cli_objects.dut.general.verify_dockers_are_up(dockers_list=['what-just-happened'])


def check_if_channel_enabled(cli_object, engines, channel, channel_type):
    """
    A function that checks if the received channel is available in WJH
    :param engines: engines fixture
    :param channel: channel name
    :param channel_type: channel type
    :param cli_object: cli_object
    """

    if channel == "buffer" and cli_object.general.is_spc1(cli_object):
        pytest.skip("buffer channel is not supported in SPC1.")

    if channel not in pytest.CHANNEL_CONF:
        pytest.fail("{} channel is not confiugred on WJH.".format(channel))
    if channel_type not in pytest.CHANNEL_CONF[channel]['Type']:
        pytest.fail("{} {} channel type is not confiugred on WJH.".format(channel, channel_type))


def get_parsed_table(dut, cmd, table_type):
    output = dut.run_cmd(cmd)
    parser = table_parser_info[table_type]
    table = generic_sonic_output_parser(output, headers_ofset=parser['headers_ofset'],
                                        len_ofset=parser['len_ofset'],
                                        data_ofset_from_start=parser['data_ofset_from_start'],
                                        column_ofset=parser['column_ofset'],
                                        output_key=parser['output_key'],
                                        header_line_number=parser['header_len'])
    return table


@pytest.fixture(scope='module')
def wjh_buffer_configuration(topology_obj, cli_objects, interfaces):
    """
    Pytest fixture which is doing configuration fot WJH Buffer test case
    :param topology_obj: topology object fixture
    :param cli_objects: cli_objects fixture
    :param interfaces: interfaces fixture
    """
    with allure.step('Check that links are in UP state'):
        ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
        retry_call(cli_objects.dut.interface.check_ports_status, fargs=[ports_list], tries=10, delay=10,
                   logger=logger)

    with allure.step(f"Configuring port {interfaces.dut_ha_2}, pg 0, congestion threshold = 10%, "
                     f"latency threshold = 100ns"):
        thresholds_config_dict = {
            'dut': [{'iface': interfaces.dut_ha_2, 'queue_type': 'queue', 'threshold': 10},
                    {'iface': interfaces.dut_ha_2, 'queue_type': 'latency', 'threshold': 100}
                    ]
        }
    with allure.step(f"Config the shaper of the port {interfaces.dut_ha_2}"):
        port_scheduler = "port_scheduler"
        cli_objects.dut.interface.config_port_scheduler(port_scheduler, SonicConst.MIN_SHAPER_RATE_BPS)
        cli_objects.dut.interface.config_port_qos_map(interfaces.dut_ha_2, port_scheduler)
    logger.info('Starting WJH Buffer configuration')
    cli_objects.dut.interface.disable_interfaces([interfaces.dut_ha_2, interfaces.dut_hb_2])
    WjhBufferConfigTemplate.configuration(topology_obj, thresholds_config_dict)
    cli_objects.dut.interface.enable_interfaces([interfaces.dut_ha_2, interfaces.dut_hb_2])
    cli_objects.dut.interface.check_link_state([interfaces.dut_ha_2, interfaces.dut_hb_2])
    logger.info('WJH Buffer configuration completed')

    with allure.step('Doing config save'):
        logger.info('Doing config save')
        cli_objects.dut.general.save_configuration()

    yield
    cli_objects.dut.interface.config_port_scheduler(port_scheduler, SonicConst.MAX_SHAPER_RATE_BPS)
    WjhBufferConfigTemplate.cleanup(topology_obj, thresholds_config_dict)
    logger.info('Doing config save after cleanup')
    cli_objects.dut.general.save_configuration()
    logger.info('WJH Buffer cleanup completed')


def check_if_entry_exists(table, interface, dst_ip, src_ip, proto, drop_reason, dst_mac, src_mac):
    """
    A function that checks if an entry with variables exists in the recieved table
    If found, the entry is returned as well
    :param table: a table made of dictionary
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason: drop reason
    :param dst_mac: dst mac
    :param src_mac: src mac
    """
    result = {'result': False, 'entry': None}
    for key in table:
        entry = table[key]
        # If entry is a list, it means that the message is longer than one line,
        # but all rest of info is in the first entry
        if isinstance(entry, list):
            entry = entry[0]
        format_wjh_entry_data(entry)
        if (entry['sPort'] == interface and
            entry['Src IP:Port'].split(':')[0] == src_ip and
            entry['Dst IP:Port'].split(':')[0] == dst_ip and
            entry['IP Proto'] == proto and
            entry['dMAC'] == dst_mac and
            entry['sMAC'] == src_mac and
                entry['Drop reason - Recommended action'] in drop_reason):
            result['result'] = True
            result['entry'] = entry
            break

    return result


def format_wjh_entry_data(entry):
    """
    Some column data of the entry may take more than one line, for this case, the entry data will be a list,
    need to convert it to string
    :param entry: the wjh entry data, in dict format
    :return: None
        for example:
            entry before format:
            {'#': '4',
            'Timestamp': '22/01/19 07:22:15.525',
            'sPort': 'Ethernet248', 'dPort': 'N/A', 'VLAN': 'N/A',
            'sMAC': '98:03:9b:9b:3b:22', 'dMAC': '33:33:00:00:00:16',
            'EthType': 'IPv6', 'Src IP:Port': ['fe80::9a03:9bff:fe9b:', '3b22'],
            'Dst IP:Port': 'ff02::16', 'IP Proto': 'ip', 'Drop Group': 'L2', 'Severity': 'Warn',
            'Drop reason - Recommended action': ['Multicast egress port list is empty - Validate',
                                                'why IGMP join or multicast router port does not', 'exist']}
            entry after format:
            {'#': '4',
            'Timestamp': '22/01/19 07:22:15.525',
            'sPort': 'Ethernet248', 'dPort': 'N/A', 'VLAN': 'N/A',
            'sMAC': '98:03:9b:9b:3b:22', 'dMAC': '33:33:00:00:00:16',
            'EthType': 'IPv6', 'Src IP:Port': 'fe80::9a03:9bff:fe9b:3b22'],
            'Dst IP:Port': 'ff02::16', 'IP Proto': 'ip', 'Drop Group': 'L2', 'Severity': 'Warn',
            'Drop reason - Recommended action': 'Multicast egress port list is empty - Validate why IGMP
                                                join or multicast router port does not exist'}
    """
    for column_header in ['sPort', 'Src IP:Port', 'Dst IP:Port', 'dMAC', 'sMAC',
                          'Drop reason - Recommended action']:
        if isinstance(entry[column_header], list):
            if column_header == 'Drop reason - Recommended action':
                entry[column_header] = " ".join(entry[column_header])
            else:
                entry[column_header] = "".join(entry[column_header])


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
    if not result['result']:
        pytest.fail("Could not find drop in WJH {} table".format(table_type))


def validate_wjh_buffer_table(engines, cmd, table_types, interface, dst_ip, src_ip, proto, drop_reason_message, dst_mac,
                              src_mac, drop_reason):
    """
    A function that checks the WJH buffer tables (raw/agg + second page)
    :param engines: engines fixture
    :param cmd: command to execute on DUT
    :param table_types: table types
    :param interfaces: interfaces
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason_message: drop reason message
    :param dst_mac: dst mac
    :param src_mac: src mac
    :param drop_reason: drop reason
    """
    output = engines.dut.run_cmd(cmd)
    split_tables = output.split("Buffer Info")
    parsed_tables = []

    for table_type, table in zip(table_types, split_tables):
        parser = table_parser_info[table_type]
        parsed_table = generic_sonic_output_parser(table, headers_ofset=parser['headers_ofset'],
                                                   len_ofset=parser['len_ofset'],
                                                   data_ofset_from_start=parser['data_ofset_from_start'],
                                                   column_ofset=parser['column_ofset'],
                                                   output_key=parser['output_key'],
                                                   header_line_number=parser['header_len'])
        parsed_tables.append(parsed_table)

    result = check_if_entry_exists(parsed_tables[0], interface, dst_ip,
                                   src_ip, proto, drop_reason_message, dst_mac, src_mac)
    if not result['result']:
        pytest.fail("Could not find drop in WJH {} table".format(table_type[0]))

    if drop_reason in ['buffer_congestion', 'buffer_latency']:
        check_buffer_info_table(parsed_tables[1], result['entry'], drop_reason, table_types[0],
                                is_dynamic_buffer_configured(engines))


def is_dynamic_buffer_configured(engines):
    get_buffer_mode_cmd = 'redis-cli -n 4 hget "DEVICE_METADATA|localhost" buffer_model'
    buffer_mode = engines.dut.run_cmd(get_buffer_mode_cmd)
    return buffer_mode.strip('"') == "dynamic"


def check_buffer_info_table(table, entry, drop_reason, table_type, is_dynamic_buffer=False):
    """
    A function that checks the WJH buffer info table
    :param table: buffer info table
    :param entry: entry which found on raw/agg table
    :param drop_reason: drop reason
    :param table_type: table type (raw/agg)
    :param is_dynamic_buffer: whether dynamic or static buffer mode is configured
    """
    logger.info(f'Validating buffer table. Table type is:{table_type}, '
                f'is dynamic buffer configured:{is_dynamic_buffer}')
    index = entry['#']
    entry_found = False

    tc_id = "N/A"
    tc_usage = "N/A"
    latency = "N/A"
    tc_watermark = "N/A"
    latency_watermark = "N/A"
    latency_exceed_substring = "Latency"
    tc_watermark_exceed_substring = "TC Watermark >"
    occupancy_exceed_substring = "Occupancy >"

    expected_tc_id = '1' if is_dynamic_buffer else '0'

    for key in table:
        entry = table[key]
        # If entry is a list, it means that the message is longer then one line,
        # but all rest of info is in the first entry
        if isinstance(entry, list):
            entry = entry[0]
        if (entry['#'] == index):
            tc_id = entry['TC ID']
            tc_usage = entry['TC Usage [KB]']
            latency = entry['Latency [nanoseconds]']
            tc_watermark = entry['TC Watermark [KB]']
            latency_watermark = entry['Latency Watermark [nanoseconds]']
            entry_found = True
            break

    if not entry_found:
        pytest.fail("Buffer info table does not contain the entry found on raw/agg table.")

    if (table_type == 'raw'):
        if drop_reason == 'buffer_congestion':
            if (tc_id == expected_tc_id and ((occupancy_exceed_substring in tc_usage) or (tc_usage != "N/A" and int(tc_usage) > 0)) and
                    latency == "N/A" and tc_watermark == "N/A" and latency_watermark == "N/A"):
                return
        elif drop_reason == 'buffer_latency':
            if (tc_id == expected_tc_id and ((occupancy_exceed_substring in tc_usage) or (tc_usage != "N/A" and int(tc_usage) > 0)) and
                    ((latency_exceed_substring in latency) or (latency != "N/A" and int(latency) > 0)) and
                    tc_watermark == "N/A" and latency_watermark == "N/A"):
                return

    elif (table_type == 'agg'):
        if drop_reason == 'buffer_congestion':
            if (tc_id == expected_tc_id and tc_usage == "N/A" and latency == "N/A" and
                    ((tc_watermark_exceed_substring in tc_watermark) or (tc_watermark != "N/A" and int(tc_watermark))) > 0 and
                    latency_watermark == "N/A"):
                return
        elif (drop_reason == 'buffer_latency'):
            if (tc_id == expected_tc_id and tc_usage == "N/A" and latency == "N/A" and
                    ((tc_watermark_exceed_substring in tc_watermark) or (tc_watermark != "N/A" and int(tc_watermark))) > 0 and
                    latency_watermark != "N/A" and
                    ((latency_exceed_substring in latency_watermark) or int(latency_watermark) > 0)):
                return

    pytest.fail("Buffer info table is wrong, tc_id = {}, tc_usage = {}, latency = {}, tc_watermark = {}, "
                "latency_watermark = {}".format(tc_id, tc_usage, latency, tc_watermark, latency_watermark))


def do_raw_test(engines, cli_object, channel, channel_type, interface, dst_ip, src_ip, proto, drop_reason, dst_mac,
                src_mac, command):
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

    retry_call(validate_wjh_table, fargs=[engines, command, 'raw', interface, dst_ip, src_ip, proto, drop_reason,
                                          dst_mac, src_mac],
               tries=3, delay=3, logger=logger)


def do_buffer_raw_test(engines, cli_object, channel, channel_types, interface, dst_ip, src_ip, proto,
                       drop_reason_message, dst_mac, src_mac, command, drop_reason):
    """
    A function that checks the WJH feature with raw channel type
    :param engines: engines fixture
    :param cli_object: cli_object
    :param channel: channel
    :param channel_types: channel types
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason_message: drop reason message
    :param dst_mac: dst mac
    :param src_mac: src mac
    :param command: raw command
    :param drop_reason: drop reason
    """
    check_if_channel_enabled(cli_object, engines, channel, channel_types[0])

    retry_call(validate_wjh_buffer_table, fargs=[engines, command, channel_types, interface, dst_ip, src_ip, proto,
                                                 drop_reason_message, dst_mac, src_mac, drop_reason],
               tries=3, delay=3, logger=logger)


def do_agg_test(engines, cli_object, channel, channel_type, interface, dst_ip, src_ip, proto, drop_reason, dst_mac,
                src_mac, command):
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

    retry_call(validate_wjh_table, fargs=[engines, command, 'agg', interface, dst_ip, src_ip, proto, drop_reason,
                                          dst_mac, src_mac],
               tries=3, delay=3, logger=logger)


def do_buffer_agg_test(engines, cli_object, channel, channel_types, interface, dst_ip, src_ip, proto,
                       drop_reason_message, dst_mac, src_mac, command, drop_reason):
    """
    A function that checks the WJH feature with aggregated channel type
    :param engines: engines fixture
    :param cli_object: cli_object
    :param channel: channel
    :param channel_types: channel types
    :param interface: the interface name
    :param dst_ip: dst ip
    :param src_ip: src ip
    :param proto: protocol
    :param drop_reason_message: drop reason message
    :param dst_mac: dst mac
    :param src_mac: src mac
    :param command: raw command
    :param drop_reason: drop reason
    """
    check_if_channel_enabled(cli_object, engines, channel, channel_types[0])

    retry_call(validate_wjh_buffer_table, fargs=[engines, command, channel_types, interface, dst_ip, src_ip, proto,
                                                 drop_reason_message, dst_mac, src_mac, drop_reason],
               tries=3, delay=3, logger=logger)


@pytest.mark.wjh
@pytest.mark.build
@pytest.mark.physical_coverage
@pytest.mark.push_gate
@pytest.mark.parametrize("drop_reason", drop_reason_dict.keys())
@allure.title('WJH Buffer test case')
def test_buffer(drop_reason, engines, topology_obj, players, interfaces, wjh_buffer_configuration, ha_dut_2_mac,
                hb_dut_2_mac):
    """
    This test will configure the DUT and hosts to generate buffer drops
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
    drop_reason_message = drop_reason_dict[drop_reason]

    cli_object = topology_obj.players['dut']['cli']
    with allure.step('Validating WJH raw table output'):
        do_buffer_raw_test(engines=engines, cli_object=cli_object, channel='buffer',
                           channel_types=['raw', 'raw_buffer_info'], interface=interfaces.dut_hb_2, dst_ip=ha_ip,
                           src_ip=hb_ip, proto='udp', drop_reason_message=drop_reason_message,
                           dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac, command='show what-just-happened poll buffer',
                           drop_reason=drop_reason)

    with allure.step('Sending iPerf traffic'):
        logger.info('Sending iPerf traffic')
        IperfChecker(players, validation).run_validation()

    with allure.step('Validating WJH aggregated table output'):
        # The ip protocol cannot be parsed when the packet is fragmented.
        # It will be displayed as "ip" in the table.
        do_buffer_agg_test(engines=engines, cli_object=cli_object, channel='buffer',
                           channel_types=['agg', 'agg_buffer_info'], interface=interfaces.dut_hb_2, dst_ip=ha_ip,
                           src_ip=hb_ip, proto='ip', drop_reason_message=drop_reason_message,
                           dst_mac=ha_dut_2_mac, src_mac=hb_dut_2_mac,
                           command='show what-just-happened poll buffer --aggregate', drop_reason=drop_reason)


@pytest.mark.wjh
@pytest.mark.build
@allure.title('WJH L1 Raw test case')
def test_l1_raw_drop(engines, cli_objects):
    port = cli_objects.dut.interface.get_active_phy_port()
    if not port:
        pytest.skip("Could not find port in active state. Skipping the test.")
    try:
        with allure.step('Shutting down {} interface'.format(port)):
            cli_objects.dut.interface.disable_interface(port)

        drop_reason_message = 'Generic L1 event - Check layer 1 aggregated information'
        na = 'N/A'
        with allure.step('Validating WJH raw table output'):
            do_raw_test(engines=engines, cli_object=cli_objects.dut, channel='layer-1', channel_type='raw',
                        interface=port, dst_ip=na, src_ip=na, proto=na, drop_reason=drop_reason_message,
                        dst_mac=na, src_mac=na, command='show what-just-happened poll layer-1')
    finally:
        cli_objects.dut.interface.enable_interface(port)


@pytest.mark.wjh
@pytest.mark.build
@allure.title('WJH L1 Aggregated test case')
def test_l1_agg_drop(engines, cli_objects):
    check_if_channel_enabled(cli_objects.dut, engines, 'layer-1', 'aggregate')
    port = cli_objects.dut.interface.get_active_phy_port()
    if not port:
        pytest.skip("Could not find port in active state. Skipping the test.")
    with allure.step('Shutting down {} interface'.format(port)):
        cli_objects.dut.interface.disable_interface(port)
    drop_reason_message = 'Port admin down - Validate port configuration'
    na = 'N/A'
    try:
        with allure.step('Validating WJH L1 Aggregated table output with down port'):
            table = get_parsed_table(engines.dut, 'show what-just-happened poll layer-1 --aggregate', 'agg')
            verify_l1_agg_drop_exists(table, port, 'Down', drop_reason_message)

        with allure.step('Starting up {} interface'.format(port)):
            cli_objects.dut.interface.enable_interface(port)
            retry_call(cli_objects.dut.interface.check_ports_status, fargs=[[port]], tries=10, delay=5,
                       logger=logger)
            time.sleep(3)

        with allure.step('Validating WJH L1 Aggregated table output with up port'):
            table = get_parsed_table(engines.dut, 'show what-just-happened poll layer-1 --aggregate', 'agg')
            verify_l1_agg_drop_exists(table, port, 'Up', drop_reason_message)

    finally:
        with allure.step('Starting up {} interface'.format(port)):
            cli_objects.dut.interface.enable_interface(port)


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
def test_l2_src_mac_equals_dst_mac(engines, cli_objects, topology_obj, interfaces, hb_dut_2_mac):
    src_ip = '1.1.1.1'
    dst_ip = '40.0.0.3'
    count = 50
    pkt = 'Ether(src="{}", dst="{}")/IP(dst="{}", src="{}")/TCP()'.format(hb_dut_2_mac, hb_dut_2_mac, dst_ip, src_ip)
    drop_reason_message = 'Source MAC equals destination MAC - Bad packet was received from peer'
    try:
        with allure.step('Sending packet with src mac = dst mac'):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2),
                                              'packets': pkt,
                                              'count': 1}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L2 raw table output'):
            do_raw_test(engines=engines, cli_object=cli_objects.dut, channel='forwarding', channel_type='raw',
                        interface=interfaces.dut_ha_2, dst_ip=dst_ip, src_ip=src_ip, proto='tcp',
                        drop_reason=drop_reason_message, dst_mac=hb_dut_2_mac, src_mac=hb_dut_2_mac,
                        command='show what-just-happened poll forwarding')

        with allure.step('Sending {} packets with src mac = dst mac'.format(count)):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2),
                                              'packets': pkt,
                                              'count': count}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L2 aggregated table output'):
            do_agg_test(engines=engines, cli_object=cli_objects.dut, channel='forwarding', channel_type='aggregate',
                        interface=interfaces.dut_ha_2, dst_ip=dst_ip, src_ip=src_ip, proto='tcp',
                        drop_reason=drop_reason_message, dst_mac=hb_dut_2_mac, src_mac=hb_dut_2_mac,
                        command='show what-just-happened poll forwarding --aggregate')

    except Exception as e:
        pytest.fail("Could not finish the test.\nAborting!.")


@pytest.mark.wjh
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('WJH L3 test case')
def test_l3_dst_ip_is_loopback(engines, cli_objects, topology_obj, interfaces):
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
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2),
                                              'packets': pkt,
                                              'count': 1}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L3 raw table output'):
            do_raw_test(engines=engines, cli_object=cli_objects.dut, channel='forwarding', channel_type='raw',
                        interface=interfaces.dut_ha_2, dst_ip=loopback_ip, src_ip=src_ip, proto='tcp',
                        drop_reason=drop_reason_message, dst_mac=broadcast_mac, src_mac=src_mac,
                        command='show what-just-happened poll forwarding')

        with allure.step('Sending {} loopback dst ip packets'.format(count)):
            validation = {
                'sender': 'ha', 'send_args': {'interface': '{}.40'.format(interfaces.ha_dut_2),
                                              'packets': pkt,
                                              'count': 50}
            }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Validating WJH L3 aggregated table output'):
            do_agg_test(engines=engines, cli_object=cli_objects.dut, channel='forwarding', channel_type='aggregate',
                        interface=interfaces.dut_ha_2, dst_ip=loopback_ip, src_ip=src_ip, proto='tcp',
                        drop_reason=drop_reason_message, dst_mac=broadcast_mac, src_mac=src_mac,
                        command='show what-just-happened poll forwarding --aggregate')

    except Exception as e:
        pytest.fail("Could not finish the test.\nAborting!.")
