import logging
import random
import pytest

from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.nvos_ci
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_inventory(engines, devices, test_api):
    """nv show platform inventory"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Running command and parsing output"):
        output_format = OutputFormat.auto if test_api == ApiType.NVUE else OutputFormat.json
        output = OutputParsingTool.parse_show_output_to_dict(
            platform.inventory.show(output_format=output_format),
            output_format=output_format, field_name_dict={'HW Version': 'hardware-version'}).get_returned_value()

    with allure.step("Checking all inventory items exist"):
        ValidationTool.validate_set_equal(output.keys(), devices.dut.platform_inventory_items).verify_result()

    with allure.step("Checking all fields are present"):
        ValidationTool.validate_set_equal(output[PlatformConsts.HW_COMP_SWITCH].keys(),
                                          devices.dut.platform_inventory_fields).verify_result()

    with allure.step("Determining random sample"):
        random_fan_name = random.choice(devices.dut.fan_list)
        random_psu_name = random.choice(devices.dut.psu_list)
        switch_name = PlatformConsts.HW_COMP_SWITCH

    with allure.step("Checking field values"):
        errors = False
        try:
            with allure.step(f"For fan {random_fan_name} (chosen randomly)"):
                _test_show_platform_inventory_fan(output[random_fan_name], devices.dut)
        except Exception as e:
            errors = True
            logger.error(e)

        try:
            with allure.step(f"For psu {random_psu_name} (chosen randomly)"):
                _test_show_platform_inventory_psu(output[random_psu_name], devices.dut)
        except Exception as e:
            errors = True
            logger.error(e)

        try:
            with allure.step(f"For switch"):
                _test_show_platform_inventory_switch(output[switch_name], devices.dut)
        except Exception as e:
            errors = True
            logger.error(e)

        assert not errors, f"Errors encountered"


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_inventory_fan(engines, devices, test_api):
    """nv show platform inventory <random-fan-name>"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Running command and parsing output"):
        random_fan = random.choice(devices.dut.fan_list)
        logger.info(f"Random fan chosen: {random_fan}")
        output_format = OutputFormat.auto if test_api == ApiType.NVUE else OutputFormat.json
        output = OutputParsingTool.parse_show_output_to_dict(
            platform.inventory.show(random_fan, output_format=output_format),
            output_format=output_format, field_name_dict={'HW Version': 'hardware-version'}).get_returned_value()

    with allure.step("Asserting values"):
        _test_show_platform_inventory_fan(output, devices.dut)


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_inventory_psu(engines, devices, test_api):
    """nv show platform inventory <random-psu-name>"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Running command and parsing output"):
        random_psu = random.choice(devices.dut.psu_list)
        logger.info(f"Random PSU chosen: {random_psu}")
        output_format = OutputFormat.auto if test_api == ApiType.NVUE else OutputFormat.json
        output = OutputParsingTool.parse_show_output_to_dict(
            platform.inventory.show(random_psu, output_format=output_format),
            output_format=output_format, field_name_dict={'HW Version': 'hardware-version'}).get_returned_value()

    with allure.step("Asserting values"):
        _test_show_platform_inventory_psu(output, devices.dut)


@pytest.mark.platform
@pytest.mark.cumulus
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_inventory_switch(engines, devices, test_api):
    """nv show platform inventory SWITCH"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Running command and parsing output"):
        output_format = OutputFormat.auto if test_api == ApiType.NVUE else OutputFormat.json
        output = OutputParsingTool.parse_show_output_to_dict(
            platform.inventory.show(PlatformConsts.HW_COMP_SWITCH, output_format=output_format),
            output_format=output_format, field_name_dict={'HW Version': 'hardware-version'}).get_returned_value()

    with allure.step("Asserting values"):
        _test_show_platform_inventory_switch(output, devices.dut)


def _test_show_platform_inventory_fan(actual_output: dict, device: BaseSwitch):
    ValidationTool.validate_output_of_show(actual_output, device.platform_inventory_fan_values).verify_result()


def _test_show_platform_inventory_psu(actual_output: dict, device: BaseSwitch):
    ValidationTool.validate_output_of_show(actual_output, device.platform_inventory_psu_values).verify_result()


def _test_show_platform_inventory_switch(actual_output: dict, device: BaseSwitch):
    ValidationTool.validate_output_of_show(actual_output, device.platform_inventory_switch_values).verify_result()
