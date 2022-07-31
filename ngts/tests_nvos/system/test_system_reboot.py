import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool


@pytest.mark.system
def test_reboot_command(engines):
    """
    Test flow:
        1. run nv action reboot system
    """
    system = System(None)
    with allure.step('Run nv action reboot system'):
        system.reboot.action_reboot()


@pytest.mark.system
def test_reboot_command_immediate(engines):
    """
    Test flow:
        1. run nv action reboot system --mode immediate
    """
    system = System(None)
    with allure.step('Run nv action reboot system --mode immediate'):
        system.reboot.action_reboot('--mode', 'immediate')


@pytest.mark.system
def test_reboot_command_force(engines):
    """
    Test flow:
        1. run nv action reboot system --mode force
    """
    system = System(None)
    with allure.step('Run nv action reboot system --mode force'):
        system.reboot.action_reboot('--mode', 'force')


@pytest.mark.system
def test_reboot_command_type(engines):
    """
    Test flow:
        1. run nv action reboot system --type fast
        2. expected message: not supported for IB
        3. run nv action reboot system --type warm
        4. expected message: not supported for IB
    """
    substring = 'currently not supported'
    err_message = 'reboot with type is not supported for IB'

    with allure.step('Run nv action reboot system --type fast'):
        output = engines.dut.run_cmd('nv action reboot system --type fast')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)

    with allure.step('Run nv action reboot system --type warm'):
        output = engines.dut.run_cmd('nv action reboot system --type warm')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)
