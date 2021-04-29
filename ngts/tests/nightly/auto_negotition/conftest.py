import logging
import pytest
import random
import os
import re

from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.constants.constants import SPC, SPC2_3
from ngts.tests.nightly.conftest import get_dut_loopbacks, \
    cleanup

logger = logging.getLogger()


@pytest.fixture(autouse=True, scope='session')
def hosts_ports(engines, cli_objects, interfaces):
    hosts_ports = {engines.ha: (cli_objects.ha, [interfaces.ha_dut_1, interfaces.ha_dut_2]),
                   engines.hb: (cli_objects.hb, [interfaces.hb_dut_1, interfaces.hb_dut_2])}
    return hosts_ports


@pytest.fixture(autouse=True, scope='session')
@pytest.mark.usefixtures("hosts_ports")
def split_mode_supported_speeds(topology_obj, engines, cli_objects, interfaces, hosts_ports):
    """
    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces: host <-> dut interfaces fixture
    :param hosts_ports: a dictionary with hosts engine, cli_object and ports
    :return: a dictionary with available breakout options on all setup ports (included host ports)
        i.e,  {'Ethernet0': {1: {'100G', '50G', '40G', '10G', '25G'},
                            2: {'40G', '10G', '25G', '50G'},
                            4: {'10G', '25G'}},
              ...
              'enp131s0f1': {1: {'100G', '40G', '50G', '10G', '1G', '25G'}}}
    """
    platform_json_info = SonicGeneralCli.get_platform_json(engines.dut, cli_objects.dut)
    split_mode_supported_speeds = SonicGeneralCli.parse_platform_json(topology_obj, platform_json_info)
    for host_engine, host_info in hosts_ports.items():
        host_cli, host_ports = host_info
        for port in host_ports:
            split_mode_supported_speeds[port] = \
                {1: host_cli.interface.parse_show_interface_ethtool_status(host_engine, port)["supported speeds"]}
    return split_mode_supported_speeds


@pytest.fixture(autouse=True, scope='session')
def tested_lb_dict(topology_obj):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback list for each split mode on the dut
    {1: [('Ethernet52', 'Ethernet56')],
    2: [('Ethernet12', 'Ethernet16')],
    4: [('Ethernet20', 'Ethernet24')]}
    """
    tested_lb_dict = {1: [random.choice(get_dut_loopbacks(topology_obj))],
                      2: [(topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1'])],
                      4: [(topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1'])]}
    return tested_lb_dict


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
            types_dict[interface_type] = SPC[interface_type]
        else:
            types_dict[interface_type] = SPC2_3[interface_type]
    return types_dict


@pytest.fixture(autouse=True, scope='session')
@pytest.mark.usefixtures("ports_aliases_dict")
def parse_cables_info(engines, cli_objects, ports_aliases_dict):
    """
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param ports_aliases_dict: a dictionary of the port and it's sonic alias on the dut
    :return: a dictionary of supported cable types for each port
             {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...,
              'Ethernet32': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR']}
    """
    engines.dut.run_cmd("sudo mst cable add")
    cable_info = engines.dut.run_cmd("sudo mlxcables")
    parse_regex_pattern = r"Cable\s+#(\d+):(\n.*){7}Compliance\s+:\s+([\d+\w+\-\w+,\s]*)\n"
    parsed_output_list = re.findall(parse_regex_pattern, cable_info)
    res = dict()
    for port_num, _, supported_types in parsed_output_list:
        parsed_supported_types = re.findall(r"(\d+GBASE-\w+\d*)", supported_types)
        for port_name, port_sonic_alias in ports_aliases_dict.items():
            if re.match(r"etp{}\w*".format(port_num), port_sonic_alias):
                res[port_name] = parsed_supported_types
    return res


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
            supported_types = get_matched_types(supported_speeds, types_dict)
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
    return re.search(r"\d+GBASE-(\w+\d*)", type_string).group(1)


def speed_string_to_int(speed):
    """
    :param speed: a speed string i.e, '25G'
    :return: speed int value, i.e., 25
    """
    return int(re.search(r'(\d+)G', speed).group(1))


def get_matched_types(speed_list, types_dict):
    """
    :param speed_list: set of speeds, {'40G', '25G', '50G', '10G'}
    :param types_dict: a dictionary of supported speed by type based on dut chip type
    :return: a set of types that match speeds in the list, i.e, {'25GBASE-CR', '40GBASE-CR4'}
    """
    matched_types = set()
    for speed in speed_list:
        for interface_type, type_supported_speeds_list in types_dict.items():
            if speed in type_supported_speeds_list:
                matched_types.add(interface_type)
    return matched_types


@pytest.fixture(autouse=False)
def ignore_expected_loganalyzer_exceptions(loganalyzer):
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
    yield
    # if loganalyzer:
    #     ignore_regex_list = \
    #         loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                                                            "negative_auto_neg_log_analyzer_ignores.txt")))
    #     for ignore in ignore_regex_list:
    #         loganalyzer.ignore_regex.remove(ignore)


def get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds):
    """
    :param lb: a tuple of ports connected as loopback ('Ethernet52', 'Ethernet56')
    :param split_mode: the port split mode i.e, 1/2/4
    :param split_mode_supported_speeds: a dictionary with available breakout options on all setup ports
    (including host ports)
    :return: a list of mutual speeds supported by the loopback ports, i.e. ['50G', '10G', '40G', '25G', '100G']
    """
    speeds_sets = []
    for port in lb:
        speeds_sets.append(set(split_mode_supported_speeds[port][split_mode]))
    return list(set.intersection(*speeds_sets))


def convert_speeds_to_kb_format(speeds_list):
    """
    :param speeds_list: a list of speeds,  ['40G', '10G', '50G']
    :return: return a string of speeds configuration in string list format, i.e, '40000,10000,50000'
    """
    speeds_in_kb_format = list(map(lambda speed: str(speed_string_to_int(speed) * 1000), speeds_list))
    return ",".join(speeds_in_kb_format)
