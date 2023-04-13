import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli


@pytest.mark.system
def test_reboot_command(engines, devices):
    """
    Test flow:
        1. run nv action reboot system
    """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    system = System(None)

    with allure.step('Run nv action reboot system'):
        res_obj = system.reboot.action_reboot()

    with allure.step("Check system reboot output"):
        output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show()).get_returned_value()
        assert "reason" in output.keys(), "'reason' not in the output"
        assert "history" in output.keys(), "'history' not in the output"

        with allure.step("Check system reboot reason output"):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show("reason")).get_returned_value()
            ValidationTool.verify_all_fields_value_exist_in_output_dictionary(output, ["gentime", "reason", "user"]).verify_result()

        with allure.step("Check system reboot history output"):
            output = OutputParsingTool.parse_json_str_to_dictionary(system.reboot.show("history")).get_returned_value()
            if output and len(output.keys()) > 0:
                ValidationTool.verify_all_fields_value_exist_in_output_dictionary(output[list(output.keys())[0]],
                                                                                  ["gentime", "reason", "user"]).verify_result()


@pytest.mark.system
def test_reboot_command_immediate(engines, devices):
    """
    Test flow:
        1. run nv action reboot system mode immediate
    """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    system = System(None)
    with allure.step('Run nv action reboot system mode immediate'):
        res_obj = system.reboot.action_reboot(params='immediate')


@pytest.mark.system
def test_reboot_command_force(engines, devices):
    """
    Test flow:
        1. run nv action reboot system mode force
    """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    system = System(None)
    with allure.step('Run nv action reboot system mode force'):
        res_obj = system.reboot.action_reboot(params='force')


@pytest.mark.system
def test_reboot_command_type(engines, devices):
    """
    Test flow:
        1. run nv action reboot system --type fast
        2. expected message: not supported for IB
        3. run nv action reboot system --type warm
        4. expected message: not supported for IB
    """
    if devices.dut.ASIC_TYPE == 'Quantum' and is_redmine_issue_active([3292179]):
        pytest.skip("Test skipped due to an open bug: https://redmine.mellanox.com/issues/3292179")

    substring = 'NVOS cant perform it'
    err_message = 'User requested a fast reboot, but NVOS cant perform it'

    with allure.step('Run nv action reboot system type fast'):
        output = engines.dut.run_cmd('nv action reboot system type fast')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)

    with allure.step('Run nv action reboot system type warm'):
        output = engines.dut.run_cmd('nv action reboot system type warm')
        ValidationTool.verify_substring_in_output(output, substring, err_message, True)
