import re
import random
import logging
import pytest
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.tests.nightly.auto_negotition.conftest import speed_string_to_int, \
    get_interface_cable_type, get_lb_mutual_speed, convert_speeds_to_kb_format
from ngts.tests.nightly.conftest import cleanup
from ngts.constants.constants import AutonegCommandConstants
from ngts.tests.nightly.auto_negotition.test_auto_neg import generate_default_conf, auto_neg_checker, get_lb_mutual_type, \
    get_types_in_string_format, get_speed_from_cable_type, verify_auto_neg_configuration, configure_ports, configure_port_auto_neg


logger = logging.getLogger()

ALL_CABLE_TYPES = {'CR', 'CR2', 'CR4', 'SR', 'SR2', 'SR4', 'LR',
                   'LR4', 'KR', 'KR2', 'KR4', 'CAUI', 'GMII',
                   'SFI', 'XLAUI', 'CAUI4', 'XAUI', 'XFI'}

INVALID_AUTO_NEG_MODE = r"enable"
INVALID_PORT_ERR = r"Invalid\s+port\s+specified"
INVALID_AUTO_NEG_MODE_ERR = r'Error:\s+Invalid\s+value\s+for\s+"<mode>":\s+invalid choice:' \
                            r'\s+enable.\s\(choose\s+from\s+enabled,\s+disabled\)'


@pytest.mark.skip(reason="skip until all tests will be approved on final auto neg image")
def test_negative_config_interface_autoneg(topology_obj, engines, cli_objects, interfaces):
    """
    Test command "config interface autoneg <interface_name> <mode>".
    Verify the command return error if given invalid interface_name or mode.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces:  dut <-> hosts interfaces fixture
    :return: raise assertion error in case of failure
    """

    logger.info("Verify the command return error if given invalid auto neg mode.")
    cli_objects.dut.interface.check_ports_status(engines.dut, ports_list=[interfaces.dut_ha_1])
    output = \
        cli_objects.dut.interface.config_auto_negotiation_mode(engines.dut, interfaces.dut_ha_1, INVALID_AUTO_NEG_MODE)
    verify_show_cmd(output, [(INVALID_AUTO_NEG_MODE_ERR, True)])

    logger.info("Verify the command return error if given invalid interface_name")
    cli_objects.dut.interface.check_ports_status(engines.dut, ports_list=[interfaces.dut_ha_1])
    output = cli_objects.dut.interface.config_auto_negotiation_mode(engines.dut,
                                                                    get_invalid_interface(topology_obj),
                                                                    "enabled")

    verify_show_cmd(output, [(INVALID_PORT_ERR, True)])


def get_invalid_interface(topology_obj):
    """
    :param topology_obj: a topology fixture
    :return: an interface that does not exist on dut, i.e, Ethernet61
    """
    ports = topology_obj.players_all_ports['dut']
    port_num = list(map(lambda port: int(re.search("Ethernet(\d+)", port).group(1)), ports))
    max_port = max(port_num)
    return "Ethernet{}".format(max_port+1)


@pytest.mark.skip(reason="skip until all tests will be approved on final auto neg image")
def test_negative_config_advertised_speeds(topology_obj, engines, cli_objects, tested_lb_dict,
                                           split_mode_supported_speeds,
                                           interfaces_types_dict, cable_type_to_speed_capabilities_dict,
                                           ignore_expected_loganalyzer_exceptions, cleanup_list):
    """
    Test command config interface advertised-speeds <interface_name> <speed_list>.
    Verify the command return error if given invalid interface name or speed list.
    Verify auto-negotiation fails in case of mismatch advertised speeds list,
    meaning the port should not change speed because ports advertised different speeds.
    port should remain in up state even if the auto negotiation failed.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param ignore_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    split_mode = random.choice([2, 4])
    lb = tested_lb_dict[split_mode].pop()
    lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds)

    logger.info("Verify the command return error if given invalid speed list")
    invalid_speed = get_invalid_speed(lb[0], lb_mutual_speeds, split_mode_supported_speeds)
    output = cli_objects.dut.interface.config_advertised_speeds(engines.dut, lb[0], invalid_speed)
    verify_show_cmd(output, [(r"Invalid\s+speed\s+value\s+specified", True)])

    logger.info("Verify the command return error if given invalid interface name")
    output = cli_objects.dut.interface.config_advertised_speeds(engines.dut,
                                                                get_invalid_interface(topology_obj),
                                                                "all")
    verify_show_cmd(output, [(INVALID_PORT_ERR, True)])

    logger.info("Verify auto-negotiation fails in case of mismatch advertised list")
    rand_idx = random.choice(range(1, len(lb_mutual_speeds)))
    port_1_adv_speed, port_2_adv_speed = [lb_mutual_speeds[0:rand_idx], lb_mutual_speeds[rand_idx:]]
    tested_lb_dict = {split_mode: [lb]}
    conf = generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict)
    conf[lb[0]][AutonegCommandConstants.ADV_SPEED] = convert_speeds_to_kb_format(port_1_adv_speed)
    conf[lb[1]][AutonegCommandConstants.ADV_SPEED] = convert_speeds_to_kb_format(port_2_adv_speed)
    for port in lb:
        conf[port]['expected_speed'] = conf[port][AutonegCommandConstants.SPEED]
        conf[port]['expected_type'] = conf[port][AutonegCommandConstants.TYPE]
    logger.info("Set auto negotiation mode to disabled on ports")
    configure_port_auto_neg(engines.dut, cli_objects.dut, lb, conf, cleanup_list, mode='disabled')
    auto_neg_checker(topology_obj, engines.dut, cli_objects.dut, tested_lb_dict, conf,
                     cable_type_to_speed_capabilities_dict, cleanup_list)


def get_invalid_speed(port, supported_speed, split_mode_supported_speeds):
    """
    :param port: an interface on dut , i.e, Ethernet60
    :param supported_speed: port supported speeds
    :param split_mode_supported_speeds: a dictionary with available speed for each breakout mode on all setup ports
    :return: a list of speeds which are not supported by the port, i.e,
    """
    return convert_speeds_to_kb_format(set(split_mode_supported_speeds[port][1]).difference(supported_speed))


@pytest.mark.skip(reason="skip until all tests will be approved on final auto neg image")
def test_negative_config_interface_type(topology_obj, engines, cli_objects, interfaces,
                                        interfaces_types_dict):
    """
    Test command "config interface type <interface_name> <interface_type>".
    Verify the command return error if given invalid interface name.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces: dut <-> hosts interfaces fixture
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :return: raise assertion error in case of failure
    """
    logger.info("Verify the command return error if given invalid interface name")
    interfaces_types = list(map(lambda str_type: get_interface_cable_type(str_type),
                                interfaces_types_dict[interfaces.dut_ha_1]))
    output = cli_objects.dut.interface.config_interface_type(engines.dut,
                                                             get_invalid_interface(topology_obj),
                                                             random.choice(interfaces_types))
    verify_show_cmd(output, [(INVALID_PORT_ERR, True)])


@pytest.mark.skip(reason="skip until all tests will be approved on final auto neg image")
def test_negative_config_advertised_types(topology_obj, engines, cli_objects, tested_lb_dict,
                                          split_mode_supported_speeds,
                                          interfaces_types_dict, cable_type_to_speed_capabilities_dict,
                                          ignore_expected_loganalyzer_exceptions, cleanup_list):
    """
    Test command config interface advertised-types <interface_name> <interface_type_list>.
    Verify the command return error if given invalid interface name.
    verify auto-negotiation fails in case of mismatch advertised list.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param ignore_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    split_mode = random.choice([2, 1])
    lb = tested_lb_dict[split_mode].pop()
    logger.info("Verify the command return error if given invalid interface name")
    output = cli_objects.dut.interface.config_advertised_interface_types(engines.dut,
                                                                         get_invalid_interface(topology_obj),
                                                                         "all")
    verify_show_cmd(output, [(INVALID_PORT_ERR, True)])
    lb_mutual_types = list(get_lb_mutual_type(lb, interfaces_types_dict))
    rand_idx = random.choice(range(1, len(lb_mutual_types)))
    port_1_adv_type, port_2_adv_type = [lb_mutual_types[0:rand_idx], lb_mutual_types[rand_idx:]]
    tested_lb_dict = {split_mode: [lb]}
    conf = generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict)
    conf[lb[0]][AutonegCommandConstants.ADV_TYPES] = get_types_in_string_format(port_1_adv_type)
    conf[lb[1]][AutonegCommandConstants.ADV_TYPES] = get_types_in_string_format(port_2_adv_type)
    for port in lb:
        conf[port]['expected_speed'] = conf[port][AutonegCommandConstants.SPEED]
        conf[port]['expected_type'] = conf[port][AutonegCommandConstants.TYPE]
    logger.info("verify auto-negotiation fails in case of mismatch advertised list")
    auto_neg_checker(topology_obj, engines.dut, cli_objects.dut, tested_lb_dict, conf,
                     cable_type_to_speed_capabilities_dict, cleanup_list)


@pytest.mark.skip(reason="skip until all tests will be approved on final auto neg image")
def test_negative_advertised_speed_type_mismatch(topology_obj, engines, cli_objects, tested_lb_dict,
                                                 split_mode_supported_speeds, cable_type_to_speed_capabilities_dict,
                                                 interfaces_types_dict, ignore_expected_loganalyzer_exceptions,
                                                 cleanup_list):
    """
    Verify error in log when configuring mismatch type and speed, like 'CR' and '100G',
    Verify port state is down when speed and type doesn't match.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param ignore_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    split_mode = 1
    lb = tested_lb_dict[split_mode].pop()
    tested_lb_dict = {1: [lb]}
    conf = generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict)
    lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds)
    lb_mutual_types = get_lb_mutual_type(lb, interfaces_types_dict)
    max_speed = max(lb_mutual_speeds, key=speed_string_to_int)
    min_type = min(lb_mutual_types, key=get_speed_from_cable_type)
    conf[lb[0]][AutonegCommandConstants.SPEED] = max_speed
    conf[lb[0]][AutonegCommandConstants.TYPE] = get_interface_cable_type(min_type)
    conf[lb[0]][AutonegCommandConstants.ADV_SPEED] = convert_speeds_to_kb_format([max_speed])
    conf[lb[0]][AutonegCommandConstants.ADV_TYPES] = get_interface_cable_type(min_type)
    conf[lb[0]]['expected_speed'] = conf[lb[0]][AutonegCommandConstants.SPEED]
    conf[lb[0]]['expected_type'] = conf[lb[0]][AutonegCommandConstants.TYPE]
    one_port_conf = {lb[0]: conf[lb[0]]}
    base_interfaces_speeds = cli_objects.dut.interface.get_interfaces_speed(engines.dut, interfaces_list=lb)
    configure_ports(engines.dut, cli_objects.dut, one_port_conf, base_interfaces_speeds,
                    cable_type_to_speed_capabilities_dict, cleanup_list)
    #cli_objects.dut.check_ports_status(engines.dut, ports_list=lb, expected_status='down')
    configure_port_auto_neg(engines.dut, cli_objects.dut, [lb[0]], one_port_conf, cleanup_list)
    conf[lb[0]][AutonegCommandConstants.OPER] = 'down'
    verify_auto_neg_configuration(engines.dut, cli_objects.dut, one_port_conf)
    cleanup(cleanup_list)
    cli_objects.dut.interface.check_ports_status(engines.dut, ports_list=lb, expected_status='up')
