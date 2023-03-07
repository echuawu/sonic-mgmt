import logging
import pytest
import os
import re
import json

from ngts.constants.constants import InterfacesTypeConstants, SonicConst
from ngts.tests.conftest import get_dut_loopbacks
from ngts.helpers.interface_helpers import get_lb_mutual_speed, speed_string_to_int_in_mb

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def auto_neg_configuration(topology_obj, setup_name, engines, cli_objects, platform_params):
    """
    Pytest fixture which will clean all fec configuration leftover from the dut

    """

    yield

    logger.info('Starting Auto Neg configuration cleanup')
    cli_objects.dut.general.apply_basic_config(topology_obj, setup_name, platform_params)

    logger.info('Auto Neg cleanup completed')


@pytest.fixture(scope='session')
def tested_lb_dict(topology_obj, split_mode_supported_speeds):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback list for each split mode on the dut
    {1: [('Ethernet52', 'Ethernet56')],
    2: [('Ethernet12', 'Ethernet16')],
    4: [('Ethernet20', 'Ethernet24')]}
    """
    tested_lb_dict = {1: []
                      }
    update_split_2_if_possible(topology_obj, tested_lb_dict)
    update_split_4_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict)
    update_split_8_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict)

    split_mode = 1
    dut_lbs = get_dut_loopbacks(topology_obj)
    tested_lb_dict[split_mode].append(get_dut_lb_with_max_capability(dut_lbs, split_mode_supported_speeds))
    logger.info("Tests will run on the following ports :\n{}".format(tested_lb_dict))
    return tested_lb_dict


def get_dut_lb_with_max_capability(dut_lbs, split_mode_supported_speeds):
    return max(dut_lbs, key=lambda lb: speed_string_to_int_in_mb(max(get_lb_mutual_speed(lb, 1, split_mode_supported_speeds),
                                                                     key=speed_string_to_int_in_mb)))


@pytest.fixture(scope='session')
def ports_lanes_dict(interfaces_status_dict, interfaces, cli_objects):
    ports_lanes_dict = {}
    for port, port_status in interfaces_status_dict.items():
        lanes = port_status['Lanes'].split(sep=",")
        ports_lanes_dict[port] = len(lanes)
    ports_lanes_dict[interfaces.ha_dut_1] = 4
    return ports_lanes_dict


def update_split_4_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict):
    """
    :param topology_obj: topology object fixture
    :param split_mode_supported_speeds: a dictionary with available speed options for each split mode on all setup ports
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: Update loopback with split 4 configuration only in cases were there are mutaul speeds available,
    for example, parsing of platform.json file for panther will not return speeds option for port with split 4,
    because this breakout mode is not supported on panther
    """
    if topology_obj.ports.get('dut-lb-splt4-p1-1') and topology_obj.ports.get('dut-lb-splt4-p2-1'):
        split_4_lb = (topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1'])
        mutual_speeds = get_lb_mutual_speed(split_4_lb, 4, split_mode_supported_speeds)
        if mutual_speeds:
            tested_lb_dict.update({4: [split_4_lb]})


def update_split_2_if_possible(topology_obj, tested_lb_dict):
    """
    :param topology_obj: topology object fixture
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: Update loopback with split 2 configuration only in cases were there is such a loopback in setup
    (some simx setups don't have split ports as part of the configuration)
    """
    if topology_obj.ports.get('dut-lb-splt2-p1-1') and topology_obj.ports.get('dut-lb-splt2-p2-1'):
        split_2_lb = (topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1'])
        tested_lb_dict.update({2: [split_2_lb]})


def update_split_8_if_possible(topology_obj, split_mode_supported_speeds, tested_lb_dict):
    """
    :param topology_obj: topology object fixture
    :param split_mode_supported_speeds: a dictionary with available speed options for each split mode on all setup ports
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: Update loopback with split 8 configuration only in cases were there are mutaul speeds available,
    for example, parsing of platform.json file for panther will not return speeds option for port with split 8,
    because this breakout mode is not supported on panther
    """
    if topology_obj.ports.get('dut-lb-splt8-p1-1') and topology_obj.ports.get('dut-lb-splt8-p2-1'):
        split_8_lb = (topology_obj.ports['dut-lb-splt8-p1-1'], topology_obj.ports['dut-lb-splt8-p2-1'])
        mutual_speeds = get_lb_mutual_speed(split_8_lb, 8, split_mode_supported_speeds)
        if mutual_speeds:
            tested_lb_dict.update({8: [split_8_lb]})


@pytest.fixture(scope='session')
def tested_dut_host_lb_dict(topology_obj, interfaces, split_mode_supported_speeds):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback of dut - host ports connectivity
    {1: [('Ethernet64', 'enp66s0f0')]}
    """
    tested_dut_host_lb_dict = {1: [(interfaces.dut_ha_1, interfaces.ha_dut_1)]}
    logger.info("Test will run on the following ports:\n{}".format(tested_dut_host_lb_dict))
    return tested_dut_host_lb_dict


@pytest.fixture(scope='session')
def interfaces_types_dict(platform_params, chip_type):
    """

    """
    platform = platform_params.filtered_platform
    if chip_type == "SPC":
        supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC.get(platform.upper())
        if not supported_speed:
            supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC['default']
    elif chip_type == "SPC2":
        supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC2[platform.upper()]
    elif chip_type == "SPC3":
        supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC3[platform.upper()]
    else:
        raise AssertionError("Chip type {} is unrecognized".format(chip_type))
    return supported_speed


@pytest.fixture(scope='session')
def interfaces_types_port_dict(engines, cli_objects, platform_params, chip_type, ports_aliases_dict, interfaces,
                               interfaces_types_dict):
    """
    get the supported interface type with the sdk api
    example of the return value of the get_supported_intf_type.py:
    {'1': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G'], 'CR4': ['40G', '100G', '200G']},
     '2': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G'], 'CR4': ['40G', '100G', '200G']},
     '3': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G'], 'CR4': ['40G', '100G', '200G']},
     '4': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G']},
     '5': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G']},
     '6': {'CR': ['1G', '10G', '25G', '50G']},
     '7': {'CR': ['1G', '10G', '25G', '50G']},
     '8': {'CR': ['1G', '10G', '25G', '50G'], 'CR2': ['50G', '100G'], 'CR4': ['40G', '100G', '200G']},
     ...
     }
    """
    supported_speed = {}
    # For SPC1, the sdk dose not support to get port rate cap .
    if chip_type == "SPC":
        port_supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC.get(
            platform_params.filtered_platform.upper())
        if not port_supported_speed:
            port_supported_speed = InterfacesTypeConstants.INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC['default']
        for intf, alias in ports_aliases_dict.items():
            supported_speed[intf] = port_supported_speed
    else:
        base_dir = os.path.dirname(os.path.realpath(__file__))
        get_port_cap_file_name = "get_port_supported_intf_type.py"
        get_port_cap_file = os.path.join(base_dir, f"{get_port_cap_file_name}")
        engines.dut.copy_file(source_file=get_port_cap_file,
                              file_system='/tmp',
                              dest_file=get_port_cap_file_name,
                              overwrite_file=True,)
        cmd_copy_file_to_syncd = f"docker cp /tmp/{get_port_cap_file_name} syncd:/"
        engines.dut.run_cmd(cmd_copy_file_to_syncd)

        port_cap = engines.dut.run_cmd(f'docker exec syncd bash -c "python3 /{get_port_cap_file_name}"')
        port_cap = json.loads(port_cap.replace("\'", "\""))

        for intf, alias in ports_aliases_dict.items():
            regex_pattern = r"etp(\d+)\w*"
            label_port = re.match(regex_pattern, alias).group(1)
            supported_intf_type = port_cap[label_port]
            supported_speed[intf] = {}
            for intf_type, speeds in supported_intf_type.items():
                if not intf_type[2:]:
                    lane_num = 1
                else:
                    lane_num = int(intf_type[2:])
                supported_speed[intf][lane_num] = {intf_type: speeds}
    supported_speed[interfaces.ha_dut_1] = supported_speed[interfaces.dut_ha_1]
    return supported_speed


@pytest.fixture(autouse=True, scope='session')
def ports_aliases_dict(engines, cli_objects):
    """
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :return: a dictionary of the port and it's sonic alias on the dut
    i.e, {'Ethernet0': 'etp1', ..
          'Ethernet60': 'etp16'}
    """
    return cli_objects.dut.interface.parse_ports_aliases_on_sonic()


def get_interface_cable_width(type_string, expected_speed=None):
    """
    :param type_string: a interface type string 'CR'
    :param expected_speed: if the expected speed is 400G the width of the cable will be 8,
                           although the cable type will be CR4 - this is a sonic limitation
    :return: int width  value, i.e, '1'
    more examples,
    'CR' -> 1
    'CR2' -> 2
    'CR4' -> 4
    """
    width = 1
    match = re.search(r"\w+(\d+)", type_string)
    if match:
        width = int(match.group(1))
    if expected_speed == '400G':
        width = 8
    return width


def get_matched_types(lane_number, speed_list, types_dict):
    """
    :param lane_number: the port number of lanes i.e, 1,2,4 etc
    :param speed_list: set of speeds, {'40G', '25G', '50G', '10G'}
    :param types_dict: a dictionary of port supported types based on
    the port number of lanes
    i.e,
    {
        SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
        SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
        SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']},
    }
    :return: a set of types that match speeds in the list, i.e, {'CR', 'CR4'}
    """
    matched_types = set()
    lane_option = list(filter(lambda lane_option: lane_option <= lane_number, [1, 2, 4, 8]))
    for speed in speed_list:
        for lane in lane_option:
            if lane in types_dict:
                for interface_type, supported_speeds in types_dict[lane].items():
                    if speed in supported_speeds:
                        matched_types.add(interface_type)
    return matched_types


def convert_speeds_to_mb_format(speeds_list):
    """
    :param speeds_list: a list of speeds,  ['40G', '10G', '50G']
    :return: return a string of speeds configuration in string list format, i.e, '40000,10000,50000'
    """
    speeds_in_mb_format = list(map(lambda speed: str(speed_string_to_int_in_mb(speed)), speeds_list))
    return ",".join(speeds_in_mb_format)


@pytest.fixture(autouse=False)
def expected_auto_neg_loganalyzer_exceptions(request, cli_objects, loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param request: pytest build-in
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    dut_hostname = cli_objects.dut.chassis.get_hostname()
    if loganalyzer:
        expected_regex_list = \
            loganalyzer[dut_hostname].parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        "expected_negative_auto_neg_logs.txt")))
        loganalyzer[dut_hostname].expect_regex.extend(expected_regex_list)

    yield

    # If test skipped - remove expected regexps from loganalyzer.expect_regex list
    if request.node.rep_setup.skipped:
        if loganalyzer:
            expected_regex_list = \
                loganalyzer[dut_hostname].parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            "expected_negative_auto_neg_logs.txt")))

            for regexp in expected_regex_list:
                loganalyzer[dut_hostname].expect_regex.remove(regexp)


def get_all_advertised_speeds_sorted_string(speeds_list, physical_interface_type=None):
    """
    :param speeds_list: a list of speeds ['10000', '50000']
    :param physical_interface_type: physical interface type
    :return: return a string of sorted speeds configuration in M/G format, i.e, "10G,50G"
    """
    speeds_list = sorted(speeds_list, key=lambda speed_str: int(speed_str))
    if physical_interface_type == 'RJ45':
        speeds_in_str_format = list(map(lambda speed: "{}M".format(int(speed)), speeds_list))
    else:
        speeds_in_str_format = list(map(lambda speed: "{}G".format(int(int(speed) / 1000)), speeds_list))
    return ",".join(speeds_in_str_format)
