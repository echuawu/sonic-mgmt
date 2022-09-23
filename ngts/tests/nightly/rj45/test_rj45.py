import allure
import random
import logging
import copy

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
        interfaces_status, t_eeprom, t_error_status, t_lpmode, t_presence = get_cli_outputs(engines.dut,
                                                                                            cli_objects.dut)

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
        validate_lag_status(engines.dut, cli_objects.dut, test_ifaces_list, rj45_port_speed)


def get_cli_outputs(engine, cli_object):
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


def validate_lag_status(engine, cli_object, test_ifaces_list, rj45_port_speed):

    interfaces_status = cli_object.interface.parse_interfaces_status()
    for port in LACP_IFACES_LIST:
        with allure.step(f'Validate LAG {port}'):
            assert interfaces_status[port]['Speed'] in LACP_POSSIBLE_SPEEDS_LIST, f'Port {port} speed not as expected'

    for port in test_ifaces_list:
        with allure.step(f'Validate port {port} status is UP and speed is {rj45_port_speed}'):
            assert interfaces_status[port]['Oper'] == 'up'
            assert interfaces_status[port]['Speed'] == rj45_port_speed
