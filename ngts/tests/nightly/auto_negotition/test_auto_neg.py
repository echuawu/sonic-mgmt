import logging
import re
import allure
import pytest
import random
from copy import deepcopy
from retry.api import retry_call

from ngts.config_templates.ip_config_template import IpConfigTemplate
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.tests.nightly.auto_negotition.conftest import get_interface_cable_type, get_interface_cable_width, \
    get_matched_types, speed_string_to_int, get_lb_mutual_speed, convert_speeds_to_kb_format
from ngts.constants.constants import AutonegCommandConstants
from ngts.helpers.interface_helpers import get_alias_number
from ngts.tests.nightly.conftest import save_configuration_and_reboot, save_configuration, compare_actual_and_expected

logger = logging.getLogger()


def test_auto_neg(topology_obj, engines, cli_objects, tested_lb_dict,
                  split_mode_supported_speeds, interfaces_types_dict,
                  cable_type_to_speed_capabilities_dict, cleanup_list,
                  ignore_expected_loganalyzer_reboot_exceptions):
    """
    check 1#:
    This test case will set on loopbacks with/without splits,
    Then will set all advertised-speeds and all advertised-types on loopbacks.
    Enable auto-negotiation and validate speed/type configuration is as expected.

    check 2#:
    set custom advertised-speeds/advertised-types on loopbacks.
    Enable auto-negotiation and validate speed/type configuration is as expected.

    check 3#:
    save configuration and reload/warm reboot switch

    check 4#:
    validate speed/type configuration is as expected.

    check 5#:
    disable auto negotiation and validate the configuration return to previous setting.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    with allure.step("Check default auto neg configuration"):
        conf = generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict,
                                     cable_type_to_speed_capabilities_dict)
        logger.info("Checking default configuration: {}".format(conf))

        logger.info("Set auto negotiation mode to disabled on ports before test starts")
        configure_port_auto_neg(engines.dut, cli_objects.dut, conf.keys(), conf, cleanup_list, mode='disabled')

        logger.info("Enable auto-negotiation with default settings and"
                    " validate speed/type configuration is as expected.")
        auto_neg_checker(topology_obj, engines.dut, cli_objects.dut, tested_lb_dict, conf,
                         cable_type_to_speed_capabilities_dict, cleanup_list)
        configure_port_auto_neg(engines.dut, cli_objects.dut, conf.keys(), conf, cleanup_list, mode='disabled')

    with allure.step("Check custom auto neg configuration"):
        conf = generate_subset_conf(tested_lb_dict, split_mode_supported_speeds, cable_type_to_speed_capabilities_dict)
        logger.info("Checking custom configuration: {}".format(conf))
        conf_backup = deepcopy(conf)
        logger.info("Enable auto-negotiation with custom settings and "
                    "validate speed/type configuration is as expected.")
        auto_neg_checker(topology_obj, engines.dut, cli_objects.dut, tested_lb_dict, conf,
                         cable_type_to_speed_capabilities_dict, cleanup_list, set_cleanup=False)

    with allure.step("Randomly reboot/reload"):
        reboot_reload_random(engines.dut, cli_objects.dut, conf.keys(), cleanup_list)

    with allure.step("Verify configuration persist after reboot/reload"):
        logger.info("validate speed/type configuration is as expected after reload/reboot")
        verify_auto_neg_configuration(engines.dut, cli_objects.dut, conf)

    with allure.step("Disable auto neg and verify port returns to previous configuration"):
        logger.info("Disable auto negotiation and validate the configuration return to previous setting.")
        configure_port_auto_neg(engines.dut, cli_objects.dut, conf.keys(), conf, cleanup_list, mode='disabled')
        verify_auto_neg_configuration(engines.dut, cli_objects.dut, conf_backup)


def test_auto_neg_toggle_peer_port(topology_obj, engines, cli_objects,
                                   interfaces, split_mode_supported_speeds,
                                   interfaces_types_dict, cable_type_to_speed_capabilities_dict, cleanup_list):
    """
    configuring default/costume auto neg on the dut port connected to host
    while toggling a port connected to the host
    Validating auto neg behavior is not affected by the ports being toggled.
    validating with host-dut traffic.

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces: dut <-> hosts interfaces fixture
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    tested_lb_dict = {1: [(interfaces.dut_ha_1, interfaces.ha_dut_1)]}

    with allure.step("Generate configurations for test"):
        def_conf = generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict,
                                         cable_type_to_speed_capabilities_dict)
        sub_conf = generate_subset_conf(tested_lb_dict, split_mode_supported_speeds, cable_type_to_speed_capabilities_dict)
        modify_subset_conf_for_toggle_peer(interfaces.dut_ha_1, sub_conf, cable_type_to_speed_capabilities_dict)

    with allure.step("Set ip configuration for future traffic validations"):
        set_peer_port_ip_conf(topology_obj, interfaces, cleanup_list)

    with allure.step("Check default configuration"):
        logger.info("Checking default configuration: {}".format(def_conf))
        auto_neg_toggle_peer_checker(topology_obj, engines, cli_objects, def_conf, interfaces,
                                     cable_type_to_speed_capabilities_dict, cleanup_list)

    with allure.step("Check custom configuration"):
        logger.info("Checking custom configuration: {}".format(sub_conf))
        auto_neg_toggle_peer_checker(topology_obj, engines, cli_objects, sub_conf, interfaces,
                                     cable_type_to_speed_capabilities_dict, cleanup_list)


def modify_subset_conf_for_toggle_peer(dut_peer_port, sub_conf, cable_type_to_speed_capabilities_dict):
    """
    This function modify the subset configuration because in order to
    configure adv-speed on a linux port the only configuration is with hex values,
    i.e. "ethtool -s eth0 advertise 0x1020" and also doesn't support configuration of any subset of speeds.

    Hence, the test only configure adv speeds/type on the dut port and doesn't modify the linux port.
    So the faction modify the expected speed,type,width
    result to what it would be if the configuration is made only on the dut and the linux port has the default settings.

    if sub_conf:

    {'Ethernet32': {'Auto-Neg Mode': 'disabled',
    'Speed': '10G',
    'Adv Speeds': '100000,40000,10000',
    'Type': 'CR',
    'Width': 1,
    'Adv Types': 'CR,CR4',
    'expected_speed': '40G', -> will be changed to 100G
    'expected_type': 'CR4',
    'expected_width': 4},
    'enp130s0f0': {'Auto-Neg Mode': 'disabled',
    'Speed': '10G',
    'Adv Speeds': '40000,10000', -> is all
    'Type': 'CR',
    'Width': 1,
    'Adv Types': 'CR,CR4', -> is all
    'expected_speed': '40G', -> will be changed to 100G
    'expected_type': 'CR4',
    'expected_width': 4}}
    """
    peer_port_speed = max(sub_conf[dut_peer_port][AutonegCommandConstants.ADV_SPEED].split(','),
                          key=lambda speed_as_str: int(speed_as_str))
    expected_speed = "{}G".format(int(int(peer_port_speed)/1000))
    interface_type = get_matched_types([expected_speed], cable_type_to_speed_capabilities_dict).pop()
    cable_type = get_interface_cable_type(interface_type)
    width = get_interface_cable_width(interface_type)
    for port, port_conf_dict in sub_conf.items():
        sub_conf[port]['expected_speed'] = expected_speed
        sub_conf[port]['expected_type'] = cable_type
        sub_conf[port]['expected_width'] = width


@pytest.mark.disable_loganalyzer
def test_interface_with_fec_none(topology_obj, engines, cli_objects, tested_lb_dict, cleanup_list):
    """
    This test case verifying the FEC is NONE in scenario for celestial peak setup.

    test flow:

        chose a random loopback(without splits configuration):
        configure FEC none on loopback
        verify with mlxlink FEC was configured to "none"
        verify with sonic show command ports are UP
        check FEC persists across reload and all 3 boot types – warm, fast, and cold.

    :param topology_obj: topology object fixture
    :param engines:  ssh engines connection
    :param cli_objects: cli objects of setup entities
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of faliure
    """
    tested_lb = tested_lb_dict[1].pop()
    logger.info("Configure fec to none on loopback: {}".format(tested_lb))
    for interface in tested_lb:
        cli_objects.dut.interface.configure_interface_fec(engines.dut, interface, fec_option="none")
        cleanup_list.append((cli_objects.dut.interface.configure_interface_fec, (engines.dut, interface, 'rs')))

    conf = {interface: {} for interface in tested_lb}
    for interface in tested_lb:
        conf[interface][AutonegCommandConstants.FEC] = "none"
        conf[interface][AutonegCommandConstants.OPER] = "up"
        conf[interface][AutonegCommandConstants.ADMIN] = "up"

    logger.info("Verify Fec none configuration")
    retry_call(verify_auto_neg_configuration, fargs=[engines.dut, cli_objects.dut, conf],
               tries=3, delay=5, logger=logger)

    reboot_reload_random(engines.dut, cli_objects.dut, conf.keys(), cleanup_list)

    logger.info("Verify Fec none configuration after reload/reboot")
    retry_call(verify_auto_neg_configuration, fargs=[engines.dut, cli_objects.dut, conf],
               tries=3, delay=5, logger=logger)


def reboot_reload_random(dut_engine, cli_object, ports, cleanup_list):
    """
    Do reload/warm-reboot on dut
    :param dut_engine: a ssh connection to dut
    :param cli_object: a cli object of dut
    :param ports: a ports list on dut to validate after reboot
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case reload/reboot failed
    """
    mode = random.choice(['reload', 'warm-reboot', 'fast-reboot', 'reboot'])
    with allure.step('Preforming {} on dut:'.format(mode)):
        if mode == 'reload':
            save_configuration(dut_engine, cli_object, cleanup_list)
            logger.info("Reloading dut")
            cli_object.general.reload_configuration(dut_engine)
        else:
            logger.info("Preforming warm reboot on dut")
            save_configuration_and_reboot(dut_engine, cli_object, ports, cleanup_list, reboot_type=mode)


def get_speeds_in_Gb_str_format(speeds_list):
    """
    :param speeds_list: a list of speeds ['10000', '50000']
    :return: return a string of speeds configuration in G format, i.e, "10G,50G"
    """
    speeds_list = sorted(speeds_list, key=lambda speed_str: int(speed_str))
    speeds_in_str_format = list(map(lambda speed: "{}G".format(int(int(speed)/1000)), speeds_list))
    return ",".join(speeds_in_str_format)


def generate_subset_conf(tested_lb_dict, split_mode_supported_speeds, types_dict):
    """
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param types_dict: a dictionary of supported speed by type based on dut chip type
    :return: a dictionary of the port auto negotiation custom configuration and expected outcome
    {'Ethernet4': {'Auto-Neg Mode': 'disabled',
                   'Speed': '10G',
                   'Adv Speeds':
                   '100000,10000',
                   'Type': 'CR',
                   'Width': 1,
                   'Adv Types': 'CR,CR4',
                   'expected_speed': '100G',
                   'expected_type': 'CR4',
                   'expected_width': 4},
    'Ethernet8': {'Auto-Neg Mode': 'disabled',
                  'Speed': '10G',
                  'Adv Speeds': '50000,100000,10000',
                  'Type': 'CR',
                  'Width': 1,
                  'Adv Types':
                  'CR,CR2,CR4',
                  'expected_speed': '100G',
                  'expected_type': 'CR4',
                  'expected_width': 4}, ...
    }
    """
    with allure.step('creating custom configuration'):
        conf = dict()
        for split_mode, lb_list in tested_lb_dict.items():
            for lb in lb_list:
                lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds)
                mutual_speed_in_subset = min(lb_mutual_speeds, key=speed_string_to_int)
                all_adv_speeds = []
                all_adv_types = []
                for port in lb:
                    adv_speeds = set(random.choices(lb_mutual_speeds, k=random.choice(range(1, len(lb_mutual_speeds)+1))))
                    if mutual_speed_in_subset not in adv_speeds:
                        adv_speeds.add(mutual_speed_in_subset)
                    adv_types = get_matched_types(adv_speeds, types_dict)
                    all_adv_speeds.append(adv_speeds)
                    all_adv_types.append(adv_types)
                    speed = mutual_speed_in_subset
                    adv_speeds = convert_speeds_to_kb_format(adv_speeds)
                    interface_type = get_matched_types([speed], types_dict).pop()
                    cable_type = get_interface_cable_type(interface_type)
                    width = get_interface_cable_width(interface_type)
                    conf[port] = build_custom_conf(speed, adv_speeds, cable_type, adv_types, width)
                expected_speed, expected_interface_type, expected_type, expected_width = \
                    get_custom_expected_conf_res(all_adv_speeds, all_adv_types)
                conf = update_custom_expected_conf(conf, lb, expected_speed, expected_type, expected_width)
        logger.debug("Generated subset configuration is: {}".format(conf))
        return conf


def get_custom_expected_conf_res(all_adv_speeds, all_adv_types):
    expected_speed = max(set.intersection(*all_adv_speeds), key=speed_string_to_int)
    expected_interface_type = max(set.intersection(*all_adv_types), key=get_speed_from_cable_type)
    expected_type = get_interface_cable_type(expected_interface_type)
    expected_width = get_interface_cable_width(expected_interface_type)
    return expected_speed, expected_interface_type, expected_type, expected_width


def build_custom_conf(speed, adv_speeds, cable_type, adv_types, width):
    port_custom_conf = {
        AutonegCommandConstants.AUTONEG_MODE: 'disabled',
        AutonegCommandConstants.SPEED: speed,
        AutonegCommandConstants.ADV_SPEED: adv_speeds,
        AutonegCommandConstants.TYPE: cable_type,
        AutonegCommandConstants.WIDTH: width,
        AutonegCommandConstants.ADV_TYPES: get_types_in_string_format(adv_types)
    }
    return port_custom_conf


def update_custom_expected_conf(conf, lb, expected_speed, expected_type, expected_width):
    for port in lb:
        conf[port]['expected_speed'] = expected_speed
        conf[port]['expected_type'] = expected_type
        conf[port]['expected_width'] = expected_width
    return conf


def get_default_expected_conf_res(lb_mutual_speeds, cable_type_to_speed_capabilities_dict):
    expected_speed = max(lb_mutual_speeds, key=speed_string_to_int)
    expected_interface_type = get_matched_types([expected_speed], cable_type_to_speed_capabilities_dict).pop()
    expected_type = get_interface_cable_type(expected_interface_type)
    expected_width = get_interface_cable_width(expected_interface_type)
    return expected_speed, expected_interface_type, expected_type, expected_width


def build_default_conf(min_speed, min_type, width, expected_speed, expected_type, expected_width):
    port_default_conf = {
        AutonegCommandConstants.AUTONEG_MODE: 'disabled',
        AutonegCommandConstants.SPEED: min_speed,
        AutonegCommandConstants.ADV_SPEED: 'all',
        AutonegCommandConstants.TYPE: min_type,
        AutonegCommandConstants.WIDTH: width,
        AutonegCommandConstants.ADV_TYPES: 'all',
        AutonegCommandConstants.OPER: "up",
        AutonegCommandConstants.ADMIN: "up",
        'expected_speed': expected_speed,
        'expected_type': expected_type,
        'expected_width': expected_width
    }
    return port_default_conf


def update_port_conf(conf, port_list):
    """
    :param conf: current configuration on ports
    :param port_list: list of ports to update
    :return: update conf info to the expected configuration on port when auto neg is enabled
    """
    for port in port_list:
        conf[port][AutonegCommandConstants.SPEED] = conf[port]['expected_speed']
        conf[port][AutonegCommandConstants.TYPE] = conf[port]['expected_type']
        conf[port][AutonegCommandConstants.WIDTH] = conf[port]['expected_width']
        conf[port][AutonegCommandConstants.OPER] = "up"
        conf[port][AutonegCommandConstants.ADMIN] = "up"


def get_loopback_first_second_ports_lists(tested_lb_dict):
    """
    this function returns 2 lists, first list contains the first port in each loopback in tested_lb_dict
    the second list has the second port in each loopback in tested_lb_dict.
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: a list of loopbacks first ports and a list of loopbacks second ports, i.e,
    lb_ports_1_list ['Ethernet48', 'Ethernet12', 'Ethernet20']
    lb_ports_2_list ['Ethernet44', 'Ethernet16', 'Ethernet24']
    """
    lb_ports_1_list, lb_ports_2_list = [], []
    for split_mode, lb_list in tested_lb_dict.items():
        for lb in lb_list:
            lb_ports_1_list.append(lb[0])
            lb_ports_2_list.append(lb[1])
    return lb_ports_1_list, lb_ports_2_list


def get_loopback_lists(tested_lb_dict):
    """
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :return: a list of all the loopbacks in the tested lb dictionary, i.e,

    """
    loopback_lists = []
    for split_mode, lb_list in tested_lb_dict.items():
        for lb in lb_list:
            loopback_lists.append(lb)
    return loopback_lists


def verify_auto_neg_configuration(dut_engine, cli_object, conf):
    """
    :param dut_engine:
    :param cli_object:
    :param conf: a dictionary of the port auto negotiation configuration and expected outcome
    :return:
    """
    with allure.step('Verify speed, advertised speed, type, advertised type, state and width on ports: {}'
                     .format(list(conf.keys()))):
        ports_aliases_dict = cli_object.interface.parse_ports_aliases_on_sonic(dut_engine)
        pci_conf = retry_call(cli_object.chassis.get_pci_conf, fargs=[dut_engine], tries=6, delay=10)
        for port, port_conf_dict in conf.items():
            retry_call(verify_autoneg_status_cmd_output_for_port, fargs=[dut_engine, cli_object, port, port_conf_dict],
                       tries=12, delay=10, logger=logger)
            retry_call(verify_mlxlink_status_cmd_output_for_port, fargs=[dut_engine, cli_object, port, port_conf_dict,
                                                                         ports_aliases_dict, pci_conf],
                       tries=12, delay=10, logger=logger)


def verify_autoneg_status_cmd_output_for_port(dut_engine, cli_object, port, port_conf_dict):
    logger.info("Verify Auto negotiation status based on sonic command")
    sonic_actual_conf = cli_object.interface.parse_show_interfaces_auto_negotiation_status(dut_engine, interface=port)
    compare_actual_and_expected_auto_neg_output(expected_conf=port_conf_dict, actual_conf=sonic_actual_conf[port])


def verify_mlxlink_status_cmd_output_for_port(dut_engine, cli_object, port, port_conf_dict,
                                              ports_aliases_dict, pci_conf):
    port_number = get_alias_number(ports_aliases_dict[port])
    logger.info("Verify Auto negotiation status based on mlxlink command")
    mlxlink_actual_conf = cli_object.interface.parse_port_mlxlink_status(dut_engine, pci_conf, port_number)
    compare_actual_and_expected_auto_neg_output(expected_conf=port_conf_dict, actual_conf=mlxlink_actual_conf)


def compare_actual_and_expected_auto_neg_output(expected_conf, actual_conf):
    """
    :param expected_conf:
    :param actual_conf:
    :return: raise assertion error in case expected and actual configuration don't match
    """
    with allure.step('Compare expected and actual auto neg configuration'):
        logger.debug("expected: {}".format(expected_conf))
        logger.debug("actual: {}".format(actual_conf))
        for key, value in expected_conf.items():
            if key in actual_conf.keys() and key != AutonegCommandConstants.TYPE:
                actual_conf_value = actual_conf[key]
                if key == AutonegCommandConstants.ADV_SPEED:
                    compare_advertised_speeds(value, actual_conf_value)
                elif key == AutonegCommandConstants.ADV_TYPES:
                    compare_advertised_types(value, actual_conf_value)
                else:
                    compare_actual_and_expected(key, value, actual_conf_value)


def compare_advertised_speeds(expected_adv_speed, actual_adv_speed):
    """
    :param expected_adv_speed:
    :param actual_adv_speed:
    :return:
    """
    if expected_adv_speed != 'all':
        expected_adv_speed = get_speeds_in_Gb_str_format(expected_adv_speed.split(','))
    compare_actual_and_expected(AutonegCommandConstants.ADV_SPEED, expected_adv_speed, actual_adv_speed)


def compare_advertised_types(expected_adv_type, actual_adv_type):
    """
    :param expected_adv_type:
    :param actual_adv_type:
    :return:
    """
    expected_adv_type = expected_adv_type.split(',')
    actual_adv_type = actual_adv_type.split(',')
    compare_actual_and_expected(AutonegCommandConstants.ADV_TYPES, set(expected_adv_type), set(actual_adv_type))


def set_speed_type_cleanup(port, engine, cli_object, base_interfaces_speeds,
                           cable_type_to_speed_capabilities_dict, cleanup_list):
    base_speed = base_interfaces_speeds[port]
    base_type = get_port_base_type(base_speed, cable_type_to_speed_capabilities_dict)
    cleanup_list.append((cli_object.interface.set_interface_speed, (engine, port, base_speed)))
    cleanup_list.append((cli_object.interface.config_interface_type, (engine, port, base_type)))
    cleanup_list.append((cli_object.interface.config_advertised_speeds, (engine, port, 'all')))
    cleanup_list.append((cli_object.interface.config_advertised_interface_types, (engine, port, 'all')))


def get_port_base_type(base_speed, cable_type_to_speed_capabilities_dict):
    base_speed_matched_type_list = get_matched_types([base_speed], cable_type_to_speed_capabilities_dict)
    if not base_speed_matched_type_list:
        raise AssertionError("Couldn't match type to speed {}, base on \"show interfaces transceiver eeprom\" "
                             "the cable types supported are {}".format(base_speed,
                                                                       cable_type_to_speed_capabilities_dict))
    base_type = get_interface_cable_type(base_speed_matched_type_list.pop())
    return base_type


def auto_neg_toggle_peer_checker(topology_obj, engines, cli_objects, conf, interfaces, cable_type_to_speed_capabilities_dict, cleanup_list):
    """

    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param conf: the auto negotiation configuration dictionary to be tested
    :param interfaces: dut <-> hosts interfaces fixture
    breakout options on all setup ports (including host ports)
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    retry_call(cli_objects.dut.interface.check_ports_status,
               fargs=[engines.dut, [interfaces.dut_ha_1]], tries=6, delay=10, logger=logger)
    dut_interfaces_speeds, ha_interfaces_speeds = retry_call(get_peer_ports_speeds,
                                                             fargs=[engines, cli_objects, interfaces],
                                                             tries=4, delay=10, logger=logger)
    disable_auto_neg_on_peer_ports(engines, cli_objects, interfaces, conf, cleanup_list)
    configure_peer_ports(engines, cli_objects, conf, interfaces, dut_interfaces_speeds, ha_interfaces_speeds,
                         cable_type_to_speed_capabilities_dict, cleanup_list)
    toggle_port(engines.dut, cli_objects.dut, interfaces.dut_ha_1, cleanup_list)
    logger.info("Enable auto-negotiation on dut interface {}".format(interfaces.dut_ha_1))
    configure_port_auto_neg(engines.dut, cli_objects.dut, ports_list=[interfaces.dut_ha_1], conf=conf,
                            cleanup_list=cleanup_list, mode='enabled')
    logger.info("Verify speed/type configuration didn't modify while auto neg is off on interface {}"
                .format(interfaces.ha_dut_1))
    verify_auto_neg_configuration(engines.dut, cli_objects.dut, conf={interfaces.dut_ha_1: conf[interfaces.dut_ha_1]})
    logger.info("Enable auto negotiation on host port {}".format(interfaces.ha_dut_1))
    configure_port_auto_neg(engines.ha, cli_objects.ha, ports_list=[interfaces.ha_dut_1],
                            conf=conf, cleanup_list=cleanup_list, mode='on')
    toggle_port(engines.ha, cli_objects.ha, interfaces.ha_dut_1, cleanup_list)
    logger.info("Check configuration on ports modify when auto neg is enabled on both ports")
    update_port_conf(conf, port_list=list(conf.keys()))
    verify_auto_neg_configuration(engines.dut, cli_objects.dut, conf={interfaces.dut_ha_1: conf[interfaces.dut_ha_1]})
    logger.info("Validate with traffic between dut-host ports")
    validate_traffic(topology_obj, interfaces)


def get_peer_ports_speeds(engines, cli_objects, interfaces):
    logger.info("Get base speed settings on ports: {}".format([interfaces.dut_ha_1, interfaces.ha_dut_1]))
    dut_interfaces_speeds = \
        cli_objects.dut.interface.get_interfaces_speed(engines.dut, interfaces_list=[interfaces.dut_ha_1])
    ha_interfaces_speeds = \
        cli_objects.ha.interface.get_interfaces_speed(engines.ha, interfaces_list=[interfaces.ha_dut_1])
    return dut_interfaces_speeds, ha_interfaces_speeds


def disable_auto_neg_on_peer_ports(engines, cli_objects, interfaces, conf, cleanup_list):
    logger.info("Disable auto negotiation on host port {}".format(interfaces.ha_dut_1))
    configure_port_auto_neg(engines.ha, cli_objects.ha, ports_list=[interfaces.ha_dut_1],
                            conf=conf, cleanup_list=cleanup_list, mode='off')
    logger.info("Disable auto-negotiation on dut interface {}".format(interfaces.dut_ha_1))
    configure_port_auto_neg(engines.dut, cli_objects.dut, ports_list=[interfaces.dut_ha_1], conf=conf,
                            cleanup_list=cleanup_list, mode='disabled')


def configure_peer_ports(engines, cli_objects, conf, interfaces, dut_interfaces_speeds, ha_interfaces_speeds,
                         cable_type_to_speed_capabilities_dict, cleanup_list):
    logger.info("Configure auto negotiation on dut port {}".format(interfaces.dut_ha_1))
    configure_ports(engines.dut, cli_objects.dut, conf={interfaces.dut_ha_1: conf[interfaces.dut_ha_1]},
                    base_interfaces_speeds=dut_interfaces_speeds,
                    cable_type_to_speed_capabilities_dict=cable_type_to_speed_capabilities_dict,
                    cleanup_list=cleanup_list)
    logger.info("Configure auto negotiation on host port {}".format(interfaces.ha_dut_1))
    configure_ports(engines.ha, cli_objects.ha, conf={interfaces.ha_dut_1: conf[interfaces.ha_dut_1]},
                    base_interfaces_speeds=ha_interfaces_speeds,
                    cable_type_to_speed_capabilities_dict=cable_type_to_speed_capabilities_dict,
                    cleanup_list=cleanup_list)


def toggle_port(engine, cli_object, port, cleanup_list):
    logger.info("Toggle port: {}".format(port))
    disable_interface(engine, cli_object, port, cleanup_list)
    cli_object.interface.enable_interface(engine, port)


def configure_dut_peer_ports(engines, cli_objects, conf, interfaces, cable_type_to_speed_capabilities_dict, cleanup_list):
    """
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param conf: the auto negotiation configuration dictionary to be tested
    :param interfaces: dut <-> hosts interfaces fixture
    breakout options on all setup ports (including host ports)
    the port cable number and split mode including host port
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case of failure
    """
    logger.info("Get base speed settings on ports: {}".format([interfaces.dut_ha_1, interfaces.ha_dut_1]))
    dut_interfaces_speeds = \
        cli_objects.dut.interface.get_interfaces_speed(engines.dut, interfaces_list=[interfaces.dut_ha_1])
    ha_interfaces_speeds = \
        cli_objects.ha.interface.get_interfaces_speed(engines.ha, interfaces_list=[interfaces.ha_dut_1])
    logger.info("Configure auto negotiation on dut port {}".format(interfaces.dut_ha_1))
    configure_ports(engines.dut, cli_objects.dut, conf={interfaces.dut_ha_1: conf[interfaces.dut_ha_1]},
                    base_interfaces_speeds=dut_interfaces_speeds,
                    cable_type_to_speed_capabilities_dict=cable_type_to_speed_capabilities_dict,
                    cleanup_list=cleanup_list)
    logger.info("Configure auto negotiation on host port {}".format(interfaces.ha_dut_1))
    configure_ports(engines.ha, cli_objects.ha, conf={interfaces.ha_dut_1: conf[interfaces.ha_dut_1]},
                    base_interfaces_speeds=ha_interfaces_speeds,
                    cable_type_to_speed_capabilities_dict=cable_type_to_speed_capabilities_dict,
                    cleanup_list=cleanup_list)


def set_peer_port_ip_conf(topology_obj, interfaces, cleanup_list):
    """
    set ips on the dut and host ports
    :param topology_obj: topology object fixture
    :param interfaces: dut <-> hosts interfaces fixture
    :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
    :return: None
    """
    ip_config_dict = \
        {'dut': [{'iface': interfaces.dut_ha_1, 'ips': [('20.20.20.1', '24')]}],
         'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('20.20.20.2', '24')]}]}
    cleanup_list.append((IpConfigTemplate.cleanup, (topology_obj, ip_config_dict,)))
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)


def validate_traffic(topology_obj, interfaces):
    """
    send ping between dut and host and validate the results
    :param topology_obj: topology object fixture
    :param interfaces: dut <-> hosts interfaces fixture
    :return: raise assertion errors in case of validation errors
    """
    with allure.step('send ping from {} to {}'.format(interfaces.ha_dut_1, interfaces.dut_ha_1)):
        validation = {'sender': 'ha', 'args': {'interface': interfaces.ha_dut_1, 'count': 3, 'dst': '20.20.20.1'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 untagged packets from {} to {}'.format(interfaces.ha_dut_1, interfaces.dut_ha_1))
        ping.run_validation()


def disable_interface(engine, cli_object, interface, cleanup_list):
    """
    disable the interface and add interface enabling to cleanup
    :param engine: a ssh connection
    :param cli_object: a cli object
    :param interface: an interface
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :return: None
    """
    logger.info("Disable the interface {}".format(interface))
    cleanup_list.append((cli_object.interface.enable_interface, (engine, interface)))
    cli_object.interface.disable_interface(engine, interface)


def auto_neg_checker(topology_obj, dut_engine, cli_object, tested_lb_dict, conf,
                     cable_type_to_speed_capabilities_dict, cleanup_list, set_cleanup=True):
    """
    The function does as following:
     1) Configure the auto negotiation configuration on ports(speed, type, advertised speeds, advertised types)
     2) Enable auto negotiation mode on the first port of the loopbacks
     3) Check the speed type configuration didn't change
     while auto negotiation is only enabled on one port in the loopabck.
     4) Enable auto negotiation mode on the second port of the loopbacks
     5) Verify the speed/type change to the expected result
     6) Verify with traffic

    :param topology_obj: topology object fixture
    :param dut_engine: a ssh connection to dut
    :param cli_object: a cli object of dut
    :param tested_lb_dict:  a dictionary of loopback list for each split mode on the dut
    :param conf: a dictionary of the port auto negotiation configuration and expected outcome
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :param set_cleanup:  if True, add cleanup to cleanup list
    :return: raise a assertion error in case validation failed
    """
    with allure.step("Auto negotiation checker"):
        lb_ports_1_list, lb_ports_2_list = get_loopback_first_second_ports_lists(tested_lb_dict)
        base_interfaces_speeds = cli_object.interface.get_interfaces_speed(dut_engine, interfaces_list=conf.keys())
        logger.info("Configure auto negotiation configuration on ports(speed,type,advertised speeds,advertised types)")
        configure_ports(dut_engine, cli_object, conf, base_interfaces_speeds, cable_type_to_speed_capabilities_dict,
                        cleanup_list, set_cleanup=set_cleanup)
        logger.info("Enable auto negotiation mode on the first port of the loopbacks")
        configure_port_auto_neg(dut_engine, cli_object, lb_ports_1_list, conf, cleanup_list)
        logger.info("Check configuration on ports did not modify while auto neg is enabled on one loopback port")
        verify_auto_neg_configuration(dut_engine, cli_object, conf)
        logger.info("Enable auto negotiation mode on the second port of the loopbacks")
        configure_port_auto_neg(dut_engine, cli_object, lb_ports_2_list, conf, cleanup_list)
        update_port_conf(conf, conf.keys())
        logger.info("Verify the speed/type change to expected result when auto neg is enabled on both loopback ports")
        verify_auto_neg_configuration(dut_engine, cli_object, conf)
        #send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, get_loopback_lists(tested_lb_dict))


def get_lb_mutual_type(lb, interfaces_types_dict):
    """
    :param lb: a tuple of ports connected as loopback ('Ethernet52', 'Ethernet56')
    :param interfaces_types_dict: a dictionary of ports supported types
    :return: a set of mutual types supported by the loopback ports, i.e, {'100GBASE-CR4', '25GBASE-CR', '40GBASE-CR4'}
    """
    types_sets = []
    for port in lb:
        types_sets.append(set(interfaces_types_dict[port]))
    return set.intersection(*types_sets)


def get_types_in_string_format(types_list):
    """
    :param types_list: a list/set of types, i.e, {'25GBASE-CR', '40GBASE-CR4'}
    :return: return a string of types configuration in string list format, i.e,'CR,CR4'
    """
    types_in_str_format = list(set(map(lambda type: get_interface_cable_type(type), types_list)))
    return ",".join(types_in_str_format)


def get_speed_from_cable_type(interface_type):
    """
    :param interface_type: an interface type string '100GBASE-CR4'
    :return: a int value of speed in type , i.e, 100
    """
    return int(re.search(r'(\d+)G*BASE', interface_type).group(1))


def configure_ports(engine, cli_object, conf, base_interfaces_speeds, cable_type_to_speed_capabilities_dict,
                    cleanup_list, set_cleanup=True):
    """
    configure the ports speed, advertised speed, type and advertised type based on conf dictionary

    :param engine: an ssh connection
    :param cli_object: a cli object of dut
    :param conf: a dictionary of the port auto negotiation default configuration and expected outcome
    :param base_interfaces_speeds: base speed on the ports before test configuration
    :param cable_type_to_speed_capabilities_dict: a dictionary of supported speed by type based on dut chip type
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :param set_cleanup: if True, add cleanup to cleanup list
    :return: none
    """
    with allure.step('Configuring speed, advertised speed, type and advertised type on ports: {}'
                             .format(list(conf.keys()))):
        for port, port_conf_dict in conf.items():
            if set_cleanup:
                set_speed_type_cleanup(port, engine, cli_object, base_interfaces_speeds,
                                       cable_type_to_speed_capabilities_dict, cleanup_list)
            logger.info("Configure speed on {}".format(port))
            cli_object.interface.\
                set_interface_speed(engine, port, port_conf_dict[AutonegCommandConstants.SPEED])
            logger.info("Configure type on {}".format(port))
            cli_object.interface.\
                config_interface_type(engine, port, port_conf_dict[AutonegCommandConstants.TYPE])
            logger.info("Configure advertised speeds on {}".format(port))
            cli_object.interface.\
                config_advertised_speeds(engine, port, port_conf_dict[AutonegCommandConstants.ADV_SPEED])
            logger.info("Configure advertised types on {}".format(port))
            cli_object.interface.\
                config_advertised_interface_types(engine, port, port_conf_dict[AutonegCommandConstants.ADV_TYPES])


def configure_port_auto_neg(engine, cli_object, ports_list, conf, cleanup_list, mode='enabled'):
    """
    configure the auto neg mode on the port.
    :param engine: a ssh connection
    :param cli_object: cli object of engine
    :param ports_list: a list of ports, i.e,
    :param conf: a dictionary of the port auto negotiation default configuration and expected outcome
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :param mode: a auto negation mode
    :return: none
    """
    with allure.step('configuring auto negotiation mode {} on ports {}'.format(mode, ports_list)):
        for port in ports_list:
            cli_object.interface.config_auto_negotiation_mode(engine, port, mode)
            conf[port][AutonegCommandConstants.AUTONEG_MODE] = mode
            if mode == 'enabled':
                cleanup_list.append((cli_object.interface.config_auto_negotiation_mode,
                                     (engine, port, 'disabled')))
            if mode == 'off':
                cleanup_list.append((cli_object.interface.config_auto_negotiation_mode,
                                     (engine, port, 'on')))


def generate_default_conf(tested_lb_dict, split_mode_supported_speeds, interfaces_types_dict,
                          cable_type_to_speed_capabilities_dict):
    """
    :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
    :param split_mode_supported_speeds: a dictionary with available
    breakout options on all setup ports (including host ports)
    :param interfaces_types_dict: a dictionary of port supported types based on
    the port cable number and split mode including host port
    :return: a dictionary of the port auto negotiation default configuration and expected outcome
    {'Ethernet52': {'Auto-Neg Mode': 'disabled',
    'Speed': '10G',
    'Adv Speeds': 'all',
    'Type': 'CR',
    'Adv Types': 'all',
    'Oper': 'up',
    'Admin': 'up',
    'expected_speed': '100G',
    'expected_type': 'CR4'}, ...}
    """
    with allure.step('creating default configuration'):
        conf = dict()
        for split_mode, lb_list in tested_lb_dict.items():
            for lb in lb_list:
                lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds)
                lb_mutual_types = get_lb_mutual_type(lb, interfaces_types_dict)
                min_speed = min(lb_mutual_speeds, key=speed_string_to_int)
                interface_type = min(lb_mutual_types, key=get_interface_cable_width)
                min_type = get_interface_cable_type(interface_type)
                width = get_interface_cable_width(interface_type)
                expected_speed, expected_interface_type, expected_type, expected_width = \
                    get_default_expected_conf_res(lb_mutual_speeds, cable_type_to_speed_capabilities_dict)
                for port in lb:
                    conf[port] = build_default_conf(min_speed, min_type, width,
                                                    expected_speed, expected_type, expected_width)
        logger.debug("Generated default configuration is: {}".format(conf))
        return conf
