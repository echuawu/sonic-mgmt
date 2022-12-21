import re
import allure
import random
import logging
import copy

from retry.api import retry_call
"""

 RJ45 Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+RJ45+port+test+Documentation

"""

logger = logging.getLogger()
RJ45_POSSIBLE_SPEEDS_LIST = ['1000M', '100M', '10M']
LACP_POSSIBLE_SPEEDS_LIST = ['2G', '200M', '20M']
LACP_IFACES_LIST = ['PortChannel0001', 'PortChannel0002']


def test_rj45_cli(engines, cli_objects, platform_params, rj45_ports_list, sfp_ports_list, dut_ports_interconnects,
                  cleanup_list):
    """
    Basic CLI test for RJ45 ports.
    Test logic is next:
    - Validate CLI show commands output
    - Validate hwsku.json file
    - Validate CLI config commands
    - Validate that possible to create LAG with 2 RJ45 ports
    - Validate that not possible to add SFP port to LAG which already has RJ45 ports
    - Validate speed for LAG port which has 2 RJ45 ports
    :param engines: engines fixture
    :param cli_objects: cli_objects fixture
    :param platform_params: platform_params fixture
    :param rj45_ports_list: rj45_ports_list fixture which has list of RJ45 ports
    :param sfp_ports_list: sfp_ports_list fixture which has list of SFP ports
    :param dut_ports_interconnects: dut_ports_interconnects fixture
    :param cleanup_list: cleanup_list fixture
    """
    with allure.step('Get interfaces data'):
        interfaces_status, t_eeprom, t_error_status, t_lpmode, t_presence = get_cli_outputs(cli_objects.dut)

    with allure.step('Get hwsku data'):
        hwsku_data = cli_objects.dut.general.get_hwsku_json_as_dict(platform_params.platform,
                                                                    platform_params.hwsku)

    with allure.step('Validate CLI show commands output'):
        validate_cli_show_commands_output(rj45_ports_list, interfaces_status, t_eeprom, t_error_status, t_lpmode,
                                          t_presence, hwsku_data)

    rj45_iface, rj45_peer_iface, rj45_second_iface, rj45_second_peer_iface = \
        get_four_test_interfaces(rj45_ports_list, dut_ports_interconnects)

    test_ifaces_list = [rj45_iface, rj45_peer_iface, rj45_second_iface, rj45_second_peer_iface]
    rj45_port_speed = random.choice(RJ45_POSSIBLE_SPEEDS_LIST)
    sfp_port = random.choice(sfp_ports_list)
    sfp_port_orig_speed = interfaces_status[sfp_port]['Speed']

    with allure.step('Validate CLI config commands output'):
        validate_cli_config_commands_output(engines.dut, rj45_iface)

    with allure.step('Set test ports speed'):
        for port in test_ifaces_list:
            cli_objects.dut.interface.set_interface_speed(port, rj45_port_speed)
            cleanup_list.append((cli_objects.dut.interface.set_interface_speed,
                                 (port, '1000M')))

        cli_objects.dut.interface.set_interface_speed(sfp_port, '1000')
        cleanup_list.append((cli_objects.dut.interface.set_interface_speed,
                             (sfp_port, sfp_port_orig_speed)))

    with allure.step('Create 2 LAG interfaces with 2 physical members each'):
        lag_configs_list = [{'type': 'lacp', 'name': LACP_IFACES_LIST[0], 'members': [rj45_iface,
                                                                                      rj45_second_iface]},
                            {'type': 'lacp', 'name': LACP_IFACES_LIST[1], 'members': [rj45_peer_iface,
                                                                                      rj45_second_peer_iface]}]

        for lag_config_dict in lag_configs_list:
            cli_objects.dut.lag.create_lag_interface_and_assign_physical_ports(lag_config_dict)
            cleanup_list.append((cli_objects.dut.lag.delete_lag_interface_and_unbind_physical_ports,
                                 (lag_config_dict,)))

    with allure.step('Validate LAG ports status and speed'):
        validate_lag_status(cli_objects.dut, test_ifaces_list, rj45_port_speed)


def get_cli_outputs(cli_object):
    with allure.step('Get interfaces status'):
        interfaces_status = cli_object.interface.parse_interfaces_status()

    with allure.step('Get transceiver eeprom'):
        transceiver_eeprom = cli_object.interface.parse_interfaces_transceiver_eeprom()

    with allure.step('Get transceiver error-status'):
        transceiver_error_status = cli_object.interface.parse_interfaces_transceiver_error_status()

    with allure.step('Get transceiver lpmode'):
        transceiver_lpmode = cli_object.interface.parse_interfaces_transceiver_lpmode()

    with allure.step('Get transceiver presence'):
        transceiver_presence = cli_object.interface.parse_interfaces_transceiver_presence()

    return interfaces_status, transceiver_eeprom, transceiver_error_status, transceiver_lpmode, transceiver_presence


def validate_cli_show_commands_output(rj45_ports_list, interfaces_status, t_eeprom, t_error_status, t_lpmode,
                                      t_presence, hwsku_data):

    with allure.step('Validate RJ45 ports available'):
        assert rj45_ports_list, 'RJ45 ports not available'

    for port in rj45_ports_list:
        with allure.step(f'Validate "show interfaces status" output for port {port}'):
            assert interfaces_status[port]['Speed'] in RJ45_POSSIBLE_SPEEDS_LIST, f'Port {port} speed not as expected'
            assert interfaces_status[port]['FEC'] == 'N/A', f'Port {port} FEC value is incorrect'

        with allure.step(f'Validate "show interfaces transceiver *" output for port {port}'):
            assert t_eeprom[port]['Status'] == 'SFP EEPROM is not applicable for RJ45 port'
            assert t_error_status[port]['Error Status'] == 'N/A'  # TODO: clarify, should be: 'SFP EEPROM Not Supported on TP cable'
            assert t_lpmode[port]['Low-power Mode'] == 'N/A'
            assert t_presence['Ethernet0']['Presence'] == 'Present'  # TODO: clarify what should be here

        with allure.step(f'Validate port type in hwsku file for port {port}'):
            assert hwsku_data['interfaces'][port]['port_type'] == 'RJ45'


def get_four_test_interfaces(rj45_ports_list, dut_ports_interconnects):
    tmp_list = copy.deepcopy(rj45_ports_list)
    rj45_iface = random.choice(tmp_list)
    rj45_peer_iface = dut_ports_interconnects[rj45_iface]
    tmp_list.remove(rj45_iface)
    tmp_list.remove(rj45_peer_iface)
    rj45_second_iface = random.choice(tmp_list)
    rj45_second_peer_iface = dut_ports_interconnects[rj45_second_iface]

    return rj45_iface, rj45_peer_iface, rj45_second_iface, rj45_second_peer_iface


def validate_cli_config_commands_output(engine, test_iface):

    with allure.step(f'Validate "sfputil lpmode off {test_iface}"'):
        output_disable_lp_mode = engine.run_cmd(f'sudo sfputil lpmode off {test_iface}')
        assert output_disable_lp_mode == f'Disabling low-power mode is not applicable for RJ45 port {test_iface}.'

    with allure.step(f'Validate "sfputil lpmode on {test_iface}"'):
        output_enable_lp_mode = engine.run_cmd(f'sudo sfputil lpmode on {test_iface}')
        assert output_enable_lp_mode == f'Enabling low-power mode is not applicable for RJ45 port {test_iface}.'

    with allure.step(f'Validate "sudo sfputil reset {test_iface}"'):
        output_sfputil_reset = engine.run_cmd(f'sudo sfputil reset {test_iface}')
        assert output_sfputil_reset == f'Reset is not applicable for RJ45 port {test_iface}.'

    with allure.step(f'Validate "sudo config interface type {test_iface} CR"'):
        output_iface_type_set = engine.run_cmd(f'sudo config interface type {test_iface} CR')
        # TODO: check expected message from HLD
        assert output_iface_type_set == f'Setting RJ45 ports\' type is not supported'

    with allure.step(f'Validate "sudo config interface fec {test_iface} fc"'):
        output_iface_fec_set = engine.run_cmd(f'sudo config interface fec {test_iface} fc')
        # TODO: check expected message from HLD
        assert output_iface_fec_set == f'Setting fec is not supported on port {test_iface}'


def validate_lag_status(cli_object, test_ifaces_list, rj45_port_speed):

    interfaces_status = cli_object.interface.parse_interfaces_status()
    for port in LACP_IFACES_LIST:
        with allure.step(f'Validate LAG {port}'):
            assert interfaces_status[port]['Speed'] in LACP_POSSIBLE_SPEEDS_LIST, f'Port {port} speed not as expected'

    for port in test_ifaces_list:
        with allure.step(f'Validate port {port} status is UP and speed is {rj45_port_speed}'):
            assert interfaces_status[port]['Oper'] == 'up'
            assert interfaces_status[port]['Speed'] == rj45_port_speed


@allure.step
def get_interfaces_type_from_state_db(engine, ifaces_list=None):
    """
    Get interface(-s) type dictionary from STATE_DB
    @param engine: engine.dut from engines fixture
    @param ifaces_list: list, interface(-s) to lookup, if None all interfaces and types will be returned
    @return: dict, example: {"Ethernet0": "RJ45", "Ethernet1": "RJ45", ...}
    """
    if not ifaces_list:
        output = engine.run_cmd('redis-cli -n 6 keys TRANSCEIVER_INFO*')
        ifaces_list = re.findall(r"TRANSCEIVER_INFO\|(Ethernet\d+)", output)
    interfaces_type_from_state_db = {}
    for iface in ifaces_list:
        iface_type = engine.run_cmd(f'redis-cli -n 6 hget "TRANSCEIVER_INFO|{iface}" type')
        interfaces_type_from_state_db[iface] = iface_type.strip('"')
    return interfaces_type_from_state_db


@allure.step
def get_interfaces_type_from_cli(cli_objects):
    """
    Get interfaces types dictionary from CLI
    @param cli_objects: cli_objects fixture
    @return: dictionary, example: {"Ethernet0": "RJ45", "Ethernet1": "RJ45", ...}
    """
    interface_type_from_cli = {}
    for iface, iface_info in cli_objects.dut.interface.parse_interfaces_status().items():
        interface_type_from_cli[iface] = iface_info['Type']
    return interface_type_from_cli


@allure.step
def verify_interfaces_state(cli_objects, ifaces_list, expected_oper="up", expected_admin="up"):
    """
    Verify interface(-s) state as expected in "show interfaces status"
    @param cli_objects: cli_objects fixture
    @param ifaces_list: list, interface(-s) to lookup
    @param expected_oper: str, expected interface operational state
    @param expected_admin: str, expected interface admin state
    """
    interfaces_status_dict = cli_objects.dut.interface.parse_interfaces_status()
    for iface in ifaces_list:
        actual_admin = interfaces_status_dict[iface]['Admin']
        logger.info(f"Checking Admin state for {iface} in 'show interfaces status'."
                    f"Expected: {expected_admin}, actual: {actual_admin}")
        assert actual_admin == expected_admin, f"Expected Admin state: {expected_admin}, actual: {actual_admin}"

        actual_oper = interfaces_status_dict[iface]['Oper']
        logger.info(f"Checking Oper state for {iface} in 'show interfaces status'."
                    f"Expected: {expected_oper}, actual: {actual_oper}")
        assert actual_oper == expected_oper, f"Expected Oper state: {expected_oper}, actual: {actual_oper}"
    logger.info(f"Interfaces from the list {ifaces_list} are Oper:{expected_oper}, Admin: {expected_admin}")


@allure.step
def verify_interfaces_type_cli(cli_objects, ifaces_list, expected_type):
    """
    Verify interface(-s) type as expected in "show interfaces status" and STATE_DB
    @param cli_objects: cli_objects fixture
    @param ifaces_list: list, interface(-s) to lookup
    @param expected_type: str, expected interface type, e.g. "RJ45", "N/A" etc.
    """
    interfaces_status_dict = get_interfaces_type_from_cli(cli_objects)
    for iface in ifaces_list:
        actual_type = interfaces_status_dict[iface]
        logger.info(f"Checking {iface} type in 'show interfaces status'. "
                    f"Expected: {expected_type}, actual: {actual_type}")
        assert actual_type == expected_type, f"Expected port type: {expected_type}, actual: {actual_type}"
    logger.info(f'Interfaces from the list {ifaces_list} have {expected_type} port type in "show interfaces status"')


@allure.step
def verify_interfaces_type_state_db(engine, ifaces_list, expected_type):
    """
    Verify interface(-s) type as expected in "show interfaces status" and STATE_DB
    @param engine: engine.dut from engines fixture
    @param ifaces_list: list, interface(-s) to lookup
    @param expected_type: str, expected interface type, e.g. "RJ45" etc.
    """
    for iface, actual_type in get_interfaces_type_from_state_db(engine, ifaces_list).items():
        logger.info(f"Checking {iface} type in STATE_DB. Expected: {expected_type}, actual: {actual_type}")
        assert actual_type == expected_type, f"Expected port type: {expected_type}, actual: {actual_type}"
    logger.info(f'Interfaces from the list {ifaces_list} have {expected_type} port type in STATE_DB')


@allure.step
def check_mismatch_in_hwsku(hwsku_ifaces_types, ifaces_types, source):
    """
    Verify initial types are the same in STATE_DB, "show interfaces status" and hwsku.json for each interface
    @param hwsku_ifaces_types: dict, interfaces from hwsku.json, e.g. {'Ethernet0': 'RJ45', 'Ethernet1': 'RJ45',...}
    @param ifaces_types: dictionary, interfaces from "show interface status" or STATE_DB,
                         e.g.: {"Ethernet0": "RJ45", "Ethernet1": "RJ45", ...}
    @param source: str, "STATE_DB" or "show interfaces status"
    """
    for iface_name, iface_type in ifaces_types.items():
        if not hwsku_ifaces_types[iface_name] and "SFP" in iface_type:
            # There is no info about SFP interfaces in hwsku.json
            continue
        assert hwsku_ifaces_types[iface_name] == iface_type, \
            f'Mismatch in port types between hwsku.json and {source}. ' \
            f'"Expected port type: {hwsku_ifaces_types[iface_name]}, actual: {iface_type}'
    logger.info(f"No mismatches between hwsku.json and {source}")


def test_rj45_type_verification(engines, cli_objects, platform_params, rj45_ports_list, sfp_ports_list,
                                dut_ports_interconnects):
    """
    Test for verify RJ45 interfaces type is “N/A” if there is no entry for a port in the table
    STATE_DB.TRANSCEIVER_INFO table. It is required that the port type should always be “RJ45” for RJ45 ports,
    but the corresponding entry should be removed from the table when the port is operational down, which causes
    the port type to be “N/A”. Information from STATE_DB should be fetched and properly rendered
    in CLI command "show interfaces status" output.
    @param engines: engines fixture
    @param cli_objects: cli_objects fixture
    @param platform_params: platform_params fixture
    @param rj45_ports_list: fixture, list with rj45 ports, e.g.: ['Ethernet0', 'Ethernet1', 'Ethernet2'...]
    @param sfp_ports_list: fixture, list with SFP ports, e.g.: ['Ethernet1', 'Ethernet2'...]
    @param dut_ports_interconnects: fixture, dictionary with all the Noga connectivity for dut ports,
                                    e.g. {'Ethernet5': 'Ethernet4', 'Ethernet48': 'enp67s0f1',...}
    """
    with allure.step("1. Get interfaces info form hwsku.json"):
        logger.info("1. Getting interfaces info form hwsku.json")
        hwsku_data = cli_objects.dut.general.get_hwsku_json_as_dict(platform_params.platform, platform_params.hwsku)
        hwsku_ifaces_types = {iface: data.get('port_type') for iface, data in hwsku_data['interfaces'].items()}

    with allure.step("2. Get interfaces info from STATE_DB"):
        logger.info("2. Getting interfaces info from STATE_DB")
        initial_state_db_ifaces_types = get_interfaces_type_from_state_db(engines.dut)

    with allure.step('3. Get interfaces info from "show interfaces status"'):
        logger.info('3. Getting interfaces info from "show interfaces status"')
        initial_cli_ifaces_types = get_interfaces_type_from_cli(cli_objects)

    with allure.step("4. Check initial interfaces types mismatch comparing to hwsku.json"):
        logger.info("4. Checking initial interfaces types mismatch comparing to hwsku.json")
        check_mismatch_in_hwsku(hwsku_ifaces_types, initial_state_db_ifaces_types, "STATE_DB")
        check_mismatch_in_hwsku(hwsku_ifaces_types, initial_cli_ifaces_types, "show interfaces status")

    with allure.step("5. Select four random RJ45 ports and one SFP"):
        logger.info("5. Selecting four random RJ45 ports and one SFP")
        selected_rj45_interfaces = random.sample(rj45_ports_list, 4)
        selected_rj45_peers = [dut_ports_interconnects[iface] for iface in selected_rj45_interfaces]
        selected_rj45_interfaces_with_peers = selected_rj45_interfaces + selected_rj45_peers
        selected_sfp_interface = random.choice(sfp_ports_list)
        all_selected_interfaces = selected_rj45_interfaces + selected_rj45_peers + [selected_sfp_interface]
        change_state_interfaces = selected_rj45_interfaces + [selected_sfp_interface]
        logger.info(f"Selected interfaces:\n"
                    f"RJ45: {selected_rj45_interfaces}\n"
                    f"Their peers: {selected_rj45_peers}\n"
                    f"SFP interface: {selected_sfp_interface}")
        random.shuffle(change_state_interfaces)  # Shuffling interfaces list to disable them each time in random order.

    try:
        with allure.step("6. Check initial interfaces state"):
            logger.info("6. Checking initial interfaces state")
            verify_interfaces_state(cli_objects, all_selected_interfaces, expected_oper="up", expected_admin="up")

        with allure.step('7. Set selected interfaces into admin state "DOWN" and verify their state'):
            logger.info('7. Setting selected interfaces into admin state "DOWN" and verify their state')
            for iface in change_state_interfaces:
                cli_objects.dut.interface.disable_interface(iface)
            retry_call(verify_interfaces_state, fargs=[cli_objects, change_state_interfaces, "down", "down"],
                       tries=10, delay=5, logger=logger)

        with allure.step('8. Verify the type changed to “N/A” for RJ45 ports'):
            logger.info('8. Verifying the type changed to “N/A” for RJ45 ports')
            retry_call(verify_interfaces_type_cli, fargs=[cli_objects, selected_rj45_interfaces, "N/A"],
                       tries=10, delay=5, logger=logger)
            retry_call(verify_interfaces_type_state_db, fargs=[engines.dut, selected_rj45_interfaces, "(nil)"],
                       tries=10, delay=5, logger=logger)

        with allure.step('9. Verify peers operational state is "DOWN", admin still "UP", port type - "N/A"'):
            logger.info('9. Verifying peers operational state is "DOWN", admin still "UP", port type - "N/A"')
            verify_interfaces_state(cli_objects, selected_rj45_peers, expected_oper="down", expected_admin="up")
            retry_call(verify_interfaces_type_cli, fargs=[cli_objects, selected_rj45_peers, "N/A"],
                       tries=10, delay=5, logger=logger)
            retry_call(verify_interfaces_type_state_db, fargs=[engines.dut, selected_rj45_peers, "(nil)"],
                       tries=10, delay=5, logger=logger)

        with allure.step('10. Verify SFP interface type and in "show interfaces status" and in STATE_DB'):
            logger.info('10. Verifying SFP interface type and in "show interfaces status" and in STATE_DB')
            # Port type should remain unchanged for non-RJ45 interfaces
            verify_interfaces_type_cli(cli_objects, [selected_sfp_interface],
                                       expected_type=initial_state_db_ifaces_types[selected_sfp_interface])
            verify_interfaces_type_state_db(engines.dut, [selected_sfp_interface],
                                            expected_type=initial_state_db_ifaces_types[selected_sfp_interface])

        with allure.step('11. Set selected interfaces into admin state "UP"'):
            logger.info('11. Setting selected interfaces into admin state "UP"')
            for iface in change_state_interfaces:
                cli_objects.dut.interface.enable_interface(iface)
            retry_call(verify_interfaces_state, fargs=[cli_objects, change_state_interfaces, "up", "up"],
                       tries=10, delay=5, logger=logger)

        with allure.step('12. Verify the type changed to "RJ45", for all RJ45 interfaces '
                         'but unchanged for SFP interface in "show interfaces status" and STATE_DB'):
            logger.info('12. Verifying the type changed to "RJ45", for all RJ45 interfaces '
                        'but unchanged for SFP interface in "show interfaces status" and STATE_DB')
            retry_call(verify_interfaces_type_cli, fargs=[cli_objects, selected_rj45_interfaces_with_peers, "RJ45"],
                       tries=10, delay=5, logger=logger)
            retry_call(verify_interfaces_type_state_db,
                       fargs=[engines.dut, selected_rj45_interfaces_with_peers, "RJ45"],
                       tries=10, delay=5, logger=logger)
            verify_interfaces_type_cli(cli_objects, [selected_sfp_interface],
                                       expected_type=initial_state_db_ifaces_types[selected_sfp_interface])
            verify_interfaces_type_state_db(engines.dut, [selected_sfp_interface],
                                            expected_type=initial_state_db_ifaces_types[selected_sfp_interface])

    except Exception as err:
        with allure.step('The test has failed. Returning interfaces into "UP" state'):
            logger.info('The test has failed. Returning interfaces into "UP" state')
            for iface in change_state_interfaces:
                cli_objects.dut.interface.enable_interface(iface)
            retry_call(verify_interfaces_state, fargs=[cli_objects, change_state_interfaces, "up", "up"],
                       tries=10, delay=5, logger=logger)
        raise AssertionError(err)
