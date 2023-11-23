import pytest
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


@pytest.mark.system
@pytest.mark.nvos_chipsim_ci
@pytest.mark.nvos_build
def test_reboot_command(engines, devices, test_name):
    """
    Test flow:
        1. run nv action reboot system
    """
    system = System(None)

    with allure.step('Run nv action reboot system'):
        OperationTime.save_duration('reboot', '', test_name, system.reboot.action_reboot)

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
def test_reboot_command_immediate(engines, devices, test_name):
    """
    Test flow:
        1. run nv action reboot system mode immediate
    """
    system = System(None)
    with allure.step('Run nv action reboot system mode immediate'):
        OperationTime.save_duration('reboot', 'immediate', test_name, system.reboot.action_reboot, params='immediate')


@pytest.mark.system
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_reboot_command_force(engines, devices, test_name, test_api):
    """
    Test flow:
        1. run nv action reboot system mode force
    """
    TestToolkit.tested_api = test_api
    system = System(None)
    with allure.step('Run nv action reboot system mode force'):
        OperationTime.save_duration('reboot', 'force', test_name, system.reboot.action_reboot, params='force')


@pytest.mark.system
def test_reboot_command_type(engines, devices):
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
