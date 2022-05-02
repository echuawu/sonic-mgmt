import allure
import logging
import random


logger = logging.getLogger()


# TODO uncomment not supported yet validations
def test_bf_sanity(cli_objects, topology_obj, platform_params):
    """
    Sanity test for Sonic on BlueField doing some basic validations of platform, sfputil, interfaces transceiver
     and no traceback in show interfaces commands
    :param cli_objects: cli objects fixture
    :param topology_obj: topology object
    :param platform_params: platform parameters
    :return:
    """
    random_iface = random.choice(topology_obj.players_all_ports['dut'])

    with allure.step("Verify no traceback in show version cmd"):
        cli_objects.dut.general.show_version(validate=True)

    with allure.step("validation of platform summaty output"):
        validate_platform_summary(cli_objects, platform_params)

    # currently oper state is down
    # with allure.step('Check the list and status of ports in "show interfaces status" output'):
    #     cli_objects.dut.interface.check_ports_status(topology_obj.players_all_ports['dut'])

    with allure.step('Compare sfputil and interfaces transceiver eeprom'):
        sfputil_res = cli_objects.dut.sfputil.parse_sfputil_eeprom()
        transceiver_res = cli_objects.dut.interface.parse_interfaces_transceiver_eeprom()
        compare_sfputil_and_ifaces_transceiver_relusts(sfputil_res, transceiver_res)

    with allure.step('Compare sfputil and interfaces transceiver presence'):
        sfputil_res = cli_objects.dut.sfputil.parse_sfputil_presence()
        transceiver_res = cli_objects.dut.interface.parse_interfaces_transceiver_presence()
        compare_sfputil_and_ifaces_transceiver_relusts(sfputil_res, transceiver_res)

    with allure.step('Verify no traceback in sfputil/interfaces transceiver lpmode/fwversion/error-status'):
        # cli_objects.dut.sfputil.get_sfputil_lpmode(validate=True)   # currently not implemented
        # cli_objects.dut.interface.get_interfaces_transceiver_lpmode(validate=True) # currently not implemented
        cli_objects.dut.sfputil.get_sfputil_error_status(validate=True)
        cli_objects.dut.interface.get_interfaces_transceiver_error_status(validate=True)
        # cli_objects.dut.sfputil.get_sfputil_fwversion('Ethernet0')    # currently has traceback

    with allure.step('Verify no traceback in show interfaces cmds'):
        cli_objects.dut.interface.show_interfaces_alias(validate=True)
        cli_objects.dut.interface.show_interfaces_auto_negotiation_status(validate=True)
        cli_objects.dut.interface.show_interfaces_counters(validate=True)
        cli_objects.dut.interface.show_interfaces_counters_detailed(random_iface, validate=True)
        cli_objects.dut.interface.show_interfaces_counters_errors(validate=True)
        cli_objects.dut.interface.show_interfaces_counters_rates(validate=True)
        cli_objects.dut.interface.show_interfaces_counters_description(validate=True)
        cli_objects.dut.interface.show_interfaces_naming_mode(validate=True)
        cli_objects.dut.interface.show_interfaces_neighbor_expected(validate=True)


def validate_platform_summary(cli_objects, platform_params):
    platform_keys_validate_content = ['platform', 'hwsku', 'asic_count']
    platform_keys_validate_existence = ['serial number', 'model number', 'hardware revision', 'asic']
    dut_output = cli_objects.dut.chassis.parse_platform_summary()

    missing_keys = list(set(platform_keys_validate_content + platform_keys_validate_existence) - set(dut_output.keys()))
    assert (not missing_keys, f'Some keys are missing in "show platform summary" output: {missing_keys}')

    for key, value in dut_output.items():
        key = key.lower()
        if key in platform_keys_validate_content:
            assert(value == platform_params[key], f'Unexpected value for key {key}.\n'
                                                  f'Expected: {platform_params[key]}\n'
                                                  f'Current:{value}')


def compare_sfputil_and_ifaces_transceiver_relusts(sfputil_res, transceiver_res):
    assert (sfputil_res == transceiver_res, f"sfputil and interfaces transceiver are different.\n"
                                            f"sfputil: {sfputil_res}\ninterfaces transceiver: {transceiver_res}")
