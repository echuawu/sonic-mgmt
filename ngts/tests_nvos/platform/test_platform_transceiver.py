import logging
import time

import pytest

from ngts.nvos_tools.ib.InterfaceConfiguration.Interface import Interface
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port, PortRequirements
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
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

    plugged_module = _get_module(desired_state=NvosConsts.LINK_STATE_UP)
    unplugged_module = _get_module(desired_state=NvosConsts.LINK_STATE_DOWN)

    _verify_link_state(plugged_module, desired_state=NvosConsts.LINK_STATE_UP, port_count=2)
    _verify_transceiver_status(platform, transceiver_id=plugged_module)

    _verify_transceiver_status(platform, transceiver_id=unplugged_module, expected_module_status='Removed')
    _verify_link_state(unplugged_module, desired_state=NvosConsts.LINK_STATE_DOWN, port_count=2)


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

    platform = Platform()
    desired_state = NvosConsts.LINK_STATE_UP

    with allure.step(f"Get module with state {desired_state}"):
        module_under_test = _get_module(desired_state=desired_state)
        assert module_under_test, f"No module with state {desired_state} found"
        module_index = int(
            ''.join(c for c in module_under_test if c.isdigit())) - 1  # module start from 0, while sw from 1

    try:
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

        _simulate_unplug_event(engines.dut, module_index)
        _verify_link_state(module_under_test, desired_state=NvosConsts.LINK_STATE_DOWN)
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Removed')

    finally:
        _simulate_plugin_event(engines.dut, module_index)
        _verify_link_state(module_under_test, desired_state=NvosConsts.LINK_STATE_UP)
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

    desired_state = NvosConsts.LINK_STATE_UP
    with allure.step(f"Get module with state {desired_state}"):
        module_under_test = _get_module(desired_state=desired_state)
        assert module_under_test, f"No module with state {desired_state} found"
        module_index = int(
            ''.join(c for c in module_under_test if c.isdigit())) - 1  # module start from 0, while sw from 1

    try:
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

        _simulate_unplug_event(engines.dut, module_index)
        _verify_link_state(module_under_test, desired_state=NvosConsts.LINK_STATE_DOWN)

        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Removed')

        with allure.step("Reboot the system"):
            system.reboot.action_reboot(engine=engines.dut, device=devices.dut)

        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')

    finally:
        _simulate_plugin_event(engines.dut, module_index)
        _verify_link_state(module_under_test, desired_state=NvosConsts.LINK_STATE_UP)
        _verify_transceiver_status(platform, transceiver_id=module_under_test, expected_module_status='Inserted')


def _verify_transceiver_status(platform, transceiver_id='sw1', expected_module_status='Inserted',
                               expected_error_status='N/A'):
    with allure.step("Check status and error-status exists in nv show platform transceiver"):
        transceiver_output = OutputParsingTool.parse_json_str_to_dictionary(
            platform.transceiver.show(transceiver_id)).get_returned_value()
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


def _verify_link_state(transceiver_id, desired_state=NvosConsts.LINK_STATE_UP, port_count=2):
    first_port = 1
    for i in range(first_port, port_count + 1):
        port_name = f"{transceiver_id}p{i}"
        interface = Interface(None, port_name=port_name)
        with allure.step(f"Verify link for {port_name} is {desired_state}"):
            output = OutputParsingTool.parse_json_str_to_dictionary(interface.link.state.show()).get_returned_value()
            assert desired_state in output, f"The interface {port_name} has undesired link state"


def _simulate_plugin_event(engine, module_index):
    with allure.step(f"Simulate plugin event for {module_index}"):
        admin_status = "1"  # The code to simulate plug event
        RegisterTool.update_pmaos_register(engine, admin_status=admin_status, module_index=module_index)
        time.sleep(40)


def _simulate_unplug_event(engine, module_index):
    with allure.step(f"Simulate unplug event for {module_index}"):
        admin_status = "0xe"  # The code to simulate unplug event
        RegisterTool.update_pmaos_register(engine, admin_status=admin_status, module_index=module_index)
        time.sleep(2)


def _get_module(desired_state=NvosConsts.LINK_STATE_UP):
    with allure.step(f"Get module with state {desired_state}"):
        port_requirements_object = PortRequirements()
        port_requirements_object.set_port_state(desired_state)
        port_requirements_object.set_port_type(IbInterfaceConsts.IB_PORT_TYPE)
        ports = Port.get_list_of_ports(port_requirements_object=port_requirements_object)
        assert len(ports) > 0, f"No ports with state {desired_state} found"
        return ports[0].name[:-2]
