import pytest
import os


def test_simx_custom_base_mac(cli_objects, interfaces):

    expected_base_mac_file_path = f'/tmp/simx_base_mac_{cli_objects.dut.engine.ip}'
    if not os.path.exists(expected_base_mac_file_path):
        pytest.skip(f'File: {expected_base_mac_file_path} does not exist(file should be created during SIMX '
                    f'container bringup).')

    with open(expected_base_mac_file_path) as base_mac_obj:
        base_mac_used_during_deploy = base_mac_obj.read()

    platform_syseeprom_output = cli_objects.dut.chassis.show_platform_syseeprom()
    ifconfig_mac = cli_objects.dut.ifconfig.get_interface_ifconfig_details(interfaces.dut_ha_1)

    assert base_mac_used_during_deploy.lower() == ifconfig_mac.mac_addr, \
        f'Base MAC in ifconfig output: {ifconfig_mac.mac_addr} not equal to ' \
        f'expected MAC: {base_mac_used_during_deploy.lower()}'
    assert base_mac_used_during_deploy in platform_syseeprom_output, \
        f'Expected Base MAC: {base_mac_used_during_deploy} not available in "show platform syseeprom" output'
