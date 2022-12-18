import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool


@pytest.mark.system
def test_reboot_command(engines):
    """
    Test flow:
        1. run nv action reboot system
    """
    system = System(None)

    with allure.step('Run nv action reboot system'):
        system.reboot.action_reboot()

    with allure.step("Check system reboot output"):
        output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show()).get_returned_value()
        assert "reason" in output.keys(), "'reason' not in the output"
        assert "history" in output.keys(), "'history' not in the output"

        with allure.step("Check system reboot reason output"):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show("reason")).get_returned_value()
            ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(output, ["gentime", "reason", "user"])

        with allure.step("Check system reboot history output"):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show("history")).get_returned_value()
            if output and len(output.keys()) > 0:
                ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(output[list(output.keys())[0]],
                                                                                  ["gentime", "reason", "user"])


@pytest.mark.system
def test_reboot_command_immediate(engines):
    """
    Test flow:
        1. run nv action reboot system mode immediate
    """
    system = System(None)
    with allure.step('Run nv action reboot system mode immediate'):
        system.reboot.action_reboot(params='immediate')


@pytest.mark.system
def test_reboot_command_force(engines):
    """
    Test flow:
        1. run nv action reboot system mode force
    """
    system = System(None)
    with allure.step('Run nv action reboot system mode force'):
        system.reboot.action_reboot(params='force')


@pytest.mark.system
def test_reboot_command_type(engines):
    """
    Test flow:
        1. run nv action reboot system --type fast
        2. expected message: not supported for IB
        3. run nv action reboot system --type warm
        4. expected message: not supported for IB
    """
    substring = 'NVOS cant perform it'
    err_message = 'User requested a fast reboot, but NVOS cant perform it'

    with allure.step('Run nv action reboot system type fast'):
        output = engines.dut.run_cmd('nv action reboot system type fast')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)

    with allure.step('Run nv action reboot system type warm'):
        output = engines.dut.run_cmd('nv action reboot system type warm')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)
