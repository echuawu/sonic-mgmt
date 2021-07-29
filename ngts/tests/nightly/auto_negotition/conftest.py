import logging
import pytest
import os
import re
from retry.api import retry_call

from ngts.constants.constants import SPC, SPC2_3
from ngts.tests.nightly.conftest import get_dut_loopbacks, cleanup
from ngts.helpers.interface_helpers import get_lb_mutual_speed
logger = logging.getLogger()


@pytest.fixture(autouse=True, scope='session')
def tested_lb_dict(topology_obj, interfaces_types_dict, split_mode_supported_speeds,
                   cable_type_to_speed_capabilities_dict):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback list for each split mode on the dut
    {1: [('Ethernet52', 'Ethernet56')],
    2: [('Ethernet12', 'Ethernet16')],
    4: [('Ethernet20', 'Ethernet24')]}
    """
    tested_lb_dict = {1: [],
                      2: [(topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1'])]
                      }
    update_split_4_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict)

    verify_tested_lb_dict(tested_lb_dict, interfaces_types_dict, split_mode_supported_speeds,
                          cable_type_to_speed_capabilities_dict)
    split_mode = 1
    for lb in get_dut_loopbacks(topology_obj):
        if verify_cable_compliance_info_support_all_speeds(lb, split_mode, interfaces_types_dict,
                                                           split_mode_supported_speeds,
                                                           cable_type_to_speed_capabilities_dict):
            tested_lb_dict[split_mode].append(lb)
            break
    if not tested_lb_dict[split_mode]:
        raise AssertionError("Test cannot run due to incorrect cable info on all dut un split loopbacks")
    logger.info("Tests will run on the following ports that have accurate cable compliance:\n{}".format(tested_lb_dict))
    return tested_lb_dict


def update_split_4_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict):
    """
    :param topology_obj: topology object fixture
    :param split_mode_supported_speeds: a dictionary with available speed options for each split mode on all setup ports
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: Update loopback with split 4 configuration only in cases were there are mutaul speeds available,
    for example, parsing of platform.json file for panther will not return speeds option for port with split 4,
    because this breakout mode is not supported on panther
    """
    split_4_lb = (topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1'])
    mutual_speeds = get_lb_mutual_speed(split_4_lb, 4, split_mode_supported_speeds)
    if mutual_speeds:
        tested_lb_dict.update({4: [split_4_lb]})


@pytest.fixture(scope='session')
def tested_dut_host_lb_dict(topology_obj, interfaces, interfaces_types_dict, split_mode_supported_speeds,
                            cable_type_to_speed_capabilities_dict):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback of dut - host ports connectivity
    {1: [('Ethernet64', 'enp66s0f0')]}
    """
    if not verify_cable_compliance_info_support_all_speeds(ports_list=[interfaces.dut_ha_1],
                                                           split_mode=1,
                                                           interfaces_types_dict=interfaces_types_dict,
                                                           split_mode_supported_speeds=split_mode_supported_speeds,
                                                           cable_type_to_speed_capabilities_dict=cable_type_to_speed_capabilities_dict):
        raise AssertionError("Test cannot run due to incorrect cable info on dut port connected to host")
    tested_dut_host_lb_dict = {1: [(interfaces.dut_ha_1, interfaces.ha_dut_1)]}
    logger.info("Test will run on the following ports which have accurate cable compliance:\n{}"
                .format(tested_dut_host_lb_dict))
    return tested_dut_host_lb_dict


def verify_tested_lb_dict(tested_lb_dict, interfaces_types_dict, split_mode_supported_speeds,
                          cable_type_to_speed_capabilities_dict):
    for split_mode, ports_lb_list in tested_lb_dict.items():
        for lb in ports_lb_list:
            if not verify_cable_compliance_info_support_all_speeds(lb, split_mode, interfaces_types_dict,
                                                                   split_mode_supported_speeds,
                                                                   cable_type_to_speed_capabilities_dict):
                raise AssertionError("Test cannot run due to incorrect cable info on loopback: {}, "
                                     "with split configuration mode: {}".format(lb, split_mode))


def verify_cable_compliance_info_support_all_speeds(ports_list, split_mode, interfaces_types_dict,
                                                    split_mode_supported_speeds, cable_type_to_speed_capabilities_dict):
    supported_speeds_match_res = True
    for port in ports_list:
        supported_speeds_by_platform_json = set(split_mode_supported_speeds[port][split_mode])
        supported_speeds_by_cable_compliance = \
            get_port_supported_speeds_based_on_cable_compliance_info(port, interfaces_types_dict,
                                                                     cable_type_to_speed_capabilities_dict)
        if not supported_speeds_by_platform_json == supported_speeds_by_cable_compliance:
            logger.warning("Test detected incorrect cable info: "
                           "Port {} supported speeds list is {} but cable compliance "
                           "of port on include types {} which support speeds {}."
                           .format(port, supported_speeds_by_platform_json, interfaces_types_dict[port],
                                   supported_speeds_by_cable_compliance))
            supported_speeds_match_res = False
    return supported_speeds_match_res


def get_port_supported_speeds_based_on_cable_compliance_info(port, interfaces_types_dict,
                                                             cable_type_to_speed_capabilities_dict):
    supported_speeds_set = set()
    for cable_type in interfaces_types_dict[port]:
        supported_speeds_set.update(set(cable_type_to_speed_capabilities_dict.get(cable_type, [])))
    return supported_speeds_set


@pytest.fixture(autouse=True, scope='session')
@pytest.mark.usefixtures("split_mode_supported_speeds")
@pytest.mark.usefixtures("parse_cables_info")
@pytest.mark.usefixtures("hosts_ports")
def interfaces_types_dict(topology_obj, engines, cli_objects, interfaces, split_mode_supported_speeds,
                          cable_type_to_speed_capabilities_dict, parse_cables_info, hosts_ports):
    """
    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces: host <-> dut interfaces fixture
    :param split_mode_supported_speeds: a dictionary with available speed options for each split mode on all setup ports
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param parse_cables_info: a dictionary of port supported types based on the port cable number
    :param hosts_ports: a dictionary with hosts engine, cli_object and ports
    :return: a dictionary of port supported types based on the port cable number and split mode including host port
    i.e,
    {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...
    'enp131s0f1': {'25GBASE-SR', '50GBASE-KR2', '100GBASE-CR4', '100GBASE-LR4_ER4',
    '40GBASE-CR4', '25GBASE-KR', '1GBASE-KX', '100GBASE-SR4', '40GBASE-KR4',
    '10GBASE-KR', '40GBASE-LR4', '40GBASE-SR4', '25GBASE-CR', '100GBASE-KR4', '50GBASE-CR2'}}
    """
    res_dict = parse_cables_info
    res_dict = update_split_ports_types(topology_obj, split_mode_supported_speeds, res_dict,
                                        cable_type_to_speed_capabilities_dict)
    for host_engine, host_info in hosts_ports.items():
        host_cli, host_ports = host_info
        for port in host_ports:
            res_dict[port] = \
                list(host_cli.interface.parse_show_interface_ethtool_status(host_engine, port)["advertised types"])
    return res_dict


@pytest.fixture(autouse=True, scope='session')
@pytest.mark.usefixtures("parse_cables_info")
def cable_type_to_speed_capabilities_dict(engines, cli_objects, chip_type, parse_cables_info):
    """
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param chip_type: the dut chip type, i.e. 'SPC'
    :param parse_cables_info: a dictionary of port supported types based on the port cable number
    :return: a dictionary of supported speed by type based on dut chip type, i.e,
    {'40GBASE-CR4': ['40G'],
    '100GBASE-CR4': ['100G'],
    '25GBASE-CR': ['10G', '25G']}
    """
    types_dict = dict()
    types_set = set()
    res_dict = parse_cables_info
    for interface, interface_type_list in res_dict.items():
        types_set.update(interface_type_list)
    for interface_type in types_set:
        if chip_type == "SPC":
            if interface_type not in SPC:
                AssertionError("It seems that type {} shouldn't be supported on SPC system, "
                               "it might be needed to change the cable on this setup".format(interface_type))
            types_dict[interface_type] = SPC[interface_type]
        else:
            if interface_type not in SPC2_3:
                AssertionError("Type {} is not updated in SPC2/SPC3 types dictionary, please update type capability"
                               .format(interface_type))
            types_dict[interface_type] = SPC2_3[interface_type]
    return types_dict


@pytest.fixture(autouse=True, scope='session')
@pytest.mark.usefixtures("ports_aliases_dict")
def parse_cables_info(topology_obj, engines, cli_objects, ports_aliases_dict):
    """
    :param topology_obj: topology_obj fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param ports_aliases_dict: a dictionary of the port and it's sonic alias on the dut
    :return: a dictionary of supported cable types for each port
             {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...,
              'Ethernet32': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR']}
    """
    compliance_info = retry_call(check_cable_compliance_info_updated_for_all_port, fargs=[topology_obj, engines],
                                 tries=12, delay=10, logger=logger)
    parsed_output_list = re.compile(r"Ethernet\d+").split(compliance_info)
    # first value is ""
    parsed_output_list.pop(0)
    parse_regex_pattern = r"(Ethernet\d+)"
    parsed_port_list = re.findall(parse_regex_pattern, compliance_info)
    res = dict()
    for index, port_name in enumerate(parsed_port_list):
        parsed_types = re.findall(r"(\d+G*BASE-\w+\d*)", parsed_output_list[index])
        remove_cx_type(parsed_types)
        # TODO: remove once bug redmine 2696720 is resolved
        if re.search("400G CR8", parsed_output_list[index]):
            parsed_types.append("400GBASE-CR8")
        res[port_name] = parsed_types

    return res


def remove_cx_type(parsed_supported_types):
    for cable_type in parsed_supported_types:
        if re.search('-CX', cable_type):
            parsed_supported_types.remove(cable_type)


def check_cable_compliance_info_updated_for_all_port(topology_obj, engines):
    ports = topology_obj.players_all_ports['dut']
    logger.info("Verify cable compliance info is updated for all ports")
    compliance_info = engines.dut.run_cmd("show interfaces transceiver eeprom")
    for port in ports:
        if not re.search("{}: SFP EEPROM detected".format(port), compliance_info):
            raise AssertionError("Cable Information for port {} is not Loaded by"
                                 " \"show interfaces transceiver eeprom\" cmd".format(port))
    return compliance_info


@pytest.fixture(autouse=True, scope='session')
def ports_aliases_dict(engines, cli_objects):
    """
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :return: a dictionary of the port and it's sonic alias on the dut
    i.e, {'Ethernet0': 'etp1', ..
          'Ethernet60': 'etp16'}
    """
    return cli_objects.dut.interface.parse_ports_aliases_on_sonic(engines.dut)


def update_split_ports_types(topology_obj, split_mode_supported_speeds, ports_supported_types, types_dict):
    """
    This function will update the types for port that are split in the topology,
    for example, if port that is split to 4 like dut-lb-splt4-p1-1 support speeds up to 25G,
    the types supported by the port are ['25GBASE-CR']
    even if the cables on that port supports ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'].

    :param topology_obj: topology object fixture
    :param split_mode_supported_speeds: a dictionary with available speed options for each split mode on all setup ports
    :param ports_supported_types:  a dictionary of port supported types based on the port cable number
    :param types_dict: a dictionary of supported speed by type based on dut chip type
    :return: a dictionary of port supported types based on the port cable number and port split mode
             {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...,
              'Ethernet32': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR']}
    """
    splitted_ports = {2: [topology_obj.ports['dut-lb-splt2-p1-1'],
                          topology_obj.ports['dut-lb-splt2-p1-2'],
                          topology_obj.ports['dut-lb-splt2-p2-1'],
                          topology_obj.ports['dut-lb-splt2-p2-2']],
                      4: [topology_obj.ports['dut-lb-splt4-p1-1'],
                          topology_obj.ports['dut-lb-splt4-p1-2'],
                          topology_obj.ports['dut-lb-splt4-p1-3'],
                          topology_obj.ports['dut-lb-splt4-p1-4'],
                          topology_obj.ports['dut-lb-splt4-p2-1'],
                          topology_obj.ports['dut-lb-splt4-p2-2'],
                          topology_obj.ports['dut-lb-splt4-p2-3'],
                          topology_obj.ports['dut-lb-splt4-p2-4']]}
    for split_mode, ports_list in splitted_ports.items():
        for port in ports_list:
            supported_speeds = split_mode_supported_speeds[port][split_mode]
            supported_types = get_matched_types(port, supported_speeds, ports_supported_types, types_dict)
            ports_supported_types[port] = list(supported_types)
    return ports_supported_types


@pytest.fixture(autouse=True)
def cleanup_list():
    """
    Fixture to execute cleanup after a test is run
    :return: None
    """
    cleanup_list = []
    logger.info("------------------TEST START HERE------------------")
    yield cleanup_list
    logger.info("------------------test teardown------------------")
    cleanup(cleanup_list)


def get_interface_cable_type(type_string):
    """
    :param type_string: a interface type string '25GBASE-CR'
    :return: string type value, i.e, 'CR'
    """
    return re.search(r"\d+G*BASE-(\w+\d*)", type_string).group(1)


def get_interface_cable_width(type_string):
    """
    :param type_string: a interface type string '25GBASE-CR'
    :return: int width  value, i.e, '1'
    more examples,
    '25GBASE-CR' -> 1
    '50GBASE-CR2' -> 2
    '40GBASE-CR4' -> 4
    """
    match = re.search(r"\d+G*BASE-\w+(\d+)", type_string)
    if match:
        width = match.group(1)
        return int(width)
    else:
        return 1


def speed_string_to_int(speed):
    """
    :param speed: a speed string i.e, '25G'
    :return: speed int value, i.e., 25
    """
    return int(re.search(r'(\d+)G', speed).group(1))


def get_matched_types(port, speed_list, ports_supported_types, types_dict):
    """
    :param port: i.e, "Ethernet0"
    :param speed_list: set of speeds, {'40G', '25G', '50G', '10G'}
    :param ports_supported_types: a dictionary of port supported types based on
    the port cable number and port split mode
    {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...,
     'Ethernet32': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR']}
    :param types_dict: a dictionary of supported speed by type based on dut chip type
    :return: a set of types that match speeds in the list, i.e, {'25GBASE-CR', '40GBASE-CR4'}
    """
    matched_types = set()
    for speed in speed_list:
        for interface_type in ports_supported_types[port]:
            if speed in types_dict.get(interface_type, []):
                matched_types.add(interface_type)
    return matched_types


def convert_speeds_to_kb_format(speeds_list):
    """
    :param speeds_list: a list of speeds,  ['40G', '10G', '50G']
    :return: return a string of speeds configuration in string list format, i.e, '40000,10000,50000'
    """
    speeds_in_kb_format = list(map(lambda speed: str(speed_string_to_int(speed) * 1000), speeds_list))
    return ",".join(speeds_in_kb_format)


@pytest.fixture(autouse=False)
def ignore_expected_loganalyzer_reboot_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "..", "..", "..",
                                                               "tools", "loganalyzer",
                                                               "reboot_loganalyzer_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


@pytest.fixture(autouse=False)
def ignore_auto_neg_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "negative_auto_neg_log_analyzer_ignores.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)
