import logging
import pytest

from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RegisterTool import RegisterTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()

MODULE_STATUS_DICT = {"Inserted": {"N/A", "Power budget exceeded", "Long range for non - Mellanox cable or module",
                                   "Bit I2C stuck", "Unsupported cable", "High temperature", "Enforce part number list",
                                   "Bad EEPROM", "Bad cable", "PMD type not enabled",
                                   "PCIE system power slot exceeded"},
                      "Removed": {"N/A"}}


@pytest.mark.platform
@pytest.mark.ib
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_transceiver_status(engines, test_api):
    """
    The test will check default field and values for transceiver module_status and error.

    flow:
    1. Check module and error_status for plugged module
    2. Check module and error_status for unplugged module
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create platform object"):
        platform = Platform()

    plugged_module = "sw1"
    unplugged_module = "sw12"

    _verify_transceiver_status(platform, transceiver_id=plugged_module)
    _verify_transceiver_status(platform, transceiver_id=unplugged_module, expected_module_status='Removed')


@pytest.mark.platform
@pytest.mark.ib
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_transceiver_status_unplug(engines, test_api):
    """
    The test will check if the module_status changes to Removed after simulating unplug event.

    flow:
    1. Verify module is plugged
    2. Unplug selected module
    3. Check module and error_status for unplugged module
    4. Plug module back
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    module_index = 0
    module_under_test = f"sw{module_index + 1}"

    try:
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

        _simulate_unplug_event(engines.dut, module_index)

        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Removed')

    finally:
        _simulate_plugin_event(engines.dut, module_index)
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')


@pytest.mark.platform
@pytest.mark.ib
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_transceiver_status_with_reboot(engines, devices, test_api):
    """
    The test will check if the value of module_status is reset after reboot.

    flow:
    1. Verify module is plugged
    2. Unplug selected module
    3. Check module and error_status for unplugged module
    4. Reboot the system
    5. Verify module is plugged
    """
    TestToolkit.tested_api = test_api

    with allure.step("Create System and platform object"):
        platform = Platform()
        system = System()

    module_index = 0
    module_under_test = f"sw{module_index + 1}"

    try:
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

        _simulate_unplug_event(engines.dut, module_index)

        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Removed')

        with allure.step("Reboot the system"):
            system.reboot.action_reboot(engine=engines.dut, device=devices.dut)

        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

    finally:
        _simulate_plugin_event(engines.dut, module_index)
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')


def _verify_transceiver_status(platform, transceiver_id='sw1', expected_module_status='Inserted',
                               expected_error_status='N/A'):
    with allure.step("Check module-status and module-error-status exists in nv show platform hardware transceiver"):
        transceiver_output = OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.transceiver.show(transceiver_id)).get_returned_value()
        fields_to_check = [PlatformConsts.TRANSCEIVER_STATUS, PlatformConsts.TRANSCEIVER_ERROR_STATUS]
        Tools.ValidationTool.verify_field_exist_in_json_output(transceiver_output, fields_to_check). \
            verify_result()

    with allure.step(f"Check {PlatformConsts.TRANSCEIVER_STATUS} has correct value {expected_module_status}"):
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=transceiver_output,
                                                          field_name=PlatformConsts.TRANSCEIVER_STATUS,
                                                          expected_value=expected_module_status) \
            .verify_result()

    with allure.step("Verify error status exists"):
        module_status = transceiver_output[PlatformConsts.TRANSCEIVER_STATUS].strip()
        error_status = transceiver_output[PlatformConsts.TRANSCEIVER_ERROR_STATUS].strip()
        assert error_status in MODULE_STATUS_DICT[
            module_status], f"module-error-status is in not allowed state: {error_status}"

    with allure.step(f"Check {PlatformConsts.TRANSCEIVER_ERROR_STATUS} has correct value {expected_error_status}"):
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=transceiver_output,
                                                          field_name=PlatformConsts.TRANSCEIVER_ERROR_STATUS,
                                                          expected_value=expected_error_status) \
            .verify_result()


def _simulate_plugin_event(engine, module_index):
    with allure.step("Simulate plugin event"):
        admin_status = "1"  # The code to simulate plug event
        RegisterTool.update_pmaos_register(engine, admin_status=admin_status, module_index=module_index)


def _simulate_unplug_event(engine, module_index):
    with allure.step("Simulate unplug event"):
        admin_status = "0xe"  # The code to simulate unplug event
        RegisterTool.update_pmaos_register(engine, admin_status=admin_status, module_index=module_index)
