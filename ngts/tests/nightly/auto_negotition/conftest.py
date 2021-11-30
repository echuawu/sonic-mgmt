import logging
import pytest
import os
import re
from retry.api import retry_call

from ngts.constants.constants import InterfacesTypeConstants
from ngts.tests.nightly.conftest import get_dut_loopbacks, cleanup
from ngts.helpers.interface_helpers import get_lb_mutual_speed
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def auto_neg_configuration(topology_obj, setup_name, engines, cli_objects, platform_params):
    """
    Pytest fixture which will clean all fec configuration leftover from the dut

    """

    yield

    logger.info('Starting Auto Neg configuration cleanup')
    SonicGeneralCli.apply_basic_config(topology_obj, engines.dut, cli_objects.dut, setup_name, platform_params)

    logger.info('Auto Neg cleanup completed')


@pytest.fixture(scope='session')
def tested_lb_dict(topology_obj, interfaces_types_dict, split_mode_supported_speeds):
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

    split_mode = 1
    dut_lbs = get_dut_loopbacks(topology_obj)
    tested_lb_dict[split_mode].append(get_dut_lb_with_max_capability(dut_lbs, split_mode_supported_speeds))
    logger.info("Tests will run on the following ports :\n{}".format(tested_lb_dict))
    return tested_lb_dict


def get_dut_lb_with_max_capability(dut_lbs, split_mode_supported_speeds):
    return max(dut_lbs, key=lambda lb: speed_string_to_int_in_mb(max(get_lb_mutual_speed(lb, 1, split_mode_supported_speeds),
                                                                     key=speed_string_to_int_in_mb)))


@pytest.fixture(scope='session')
def ports_lanes_dict(engines, interfaces, cli_objects):
    ports_lanes_dict = {}
    interfaces_status = cli_objects.dut.interface.parse_interfaces_status(engines.dut)
    for port, port_status in interfaces_status.items():
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


@pytest.fixture(scope='session')
def tested_dut_host_lb_dict(topology_obj, interfaces, interfaces_types_dict, split_mode_supported_speeds):
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


def speed_string_to_int_in_mb(speed):
    """
    :param speed: a speed string i.e, '25G', '100M'
    :return: speed int value in megabits, i.e., 25000, 100
    """
    match_gig = re.search(r'(\d+)G', speed)
    match_mb = re.search(r'(\d+)M', speed)
    if match_gig:
        speed_int = int(match_gig.group(1)) * 1000
    elif match_mb:
        speed_int = int(match_mb.group(1))
    else:
        try:
            speed_int = int(speed)
        except ValueError:
            raise Exception(f'Can not match speed in Mbits/Gbits from: {speed}')
    return speed_int


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
    lane_option = list(filter(lambda lane_option: lane_option <= lane_number, [1, 2, 4]))
    for speed in speed_list:
        for lane in lane_option:
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


@pytest.fixture(autouse=False)
def expected_auto_neg_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        expected_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "expected_negative_auto_neg_logs.txt")))
        loganalyzer.expect_regex.extend(expected_regex_list)


@pytest.fixture(scope='function')
def skip_if_active_optical_cable(topology_obj, engines):
    """
    Fixture that skips test execution in case setup has Active Optical Cable
    """
    cables_output = retry_call(check_cable_compliance_info_updated_for_all_port,
                               fargs=[topology_obj, engines], tries=12, delay=10, logger=logger)
    if re.search(r"Active\s+Optical\s+Cable", cables_output, re.IGNORECASE):
        pytest.skip("This test is not supported because setup has Active Optical Cable")


def check_cable_compliance_info_updated_for_all_port(topology_obj, engines):
    ports = topology_obj.players_all_ports['dut']
    logger.info("Verify cable compliance info is updated for all ports")
    compliance_info = engines.dut.run_cmd("show interfaces transceiver eeprom")
    for port in ports:
        if not re.search("{}: SFP EEPROM detected".format(port), compliance_info):
            raise AssertionError("Cable Information for port {} is not Loaded by"
                                 " \"show interfaces transceiver eeprom\" cmd".format(port))
    return compliance_info


def get_speeds_in_Gb_str_format(speeds_list):
        """
        :param speeds_list: a list of speeds ['10000', '50000']
        :return: return a string of speeds configuration in G format, i.e, "10G,50G"
        """
        speeds_list = sorted(speeds_list, key=lambda speed_str: int(speed_str))
        speeds_in_str_format = list(map(lambda speed: "{}G".format(int(int(speed) / 1000)), speeds_list))
        return ",".join(speeds_in_str_format)
