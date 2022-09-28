import pytest


@pytest.mark.disable_loganalyzer
def test_boot_into_onie(cli_objects, topology_obj, is_simx):

    if is_simx or cli_objects.dut.general.is_dpu():
        pytest.skip('No need to reboot into ONIE for SIMX/DPU setups')

    cli_objects.dut.general.prepare_onie_reboot_script_on_dut()
    onie_reboot_script_cmd = '/tmp/onie_reboot.sh install'
    topology_obj.players['dut']['engine'].send_config_set([onie_reboot_script_cmd],
                                                          exit_config_mode=False,
                                                          cmd_verify=False)
