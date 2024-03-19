import logging
import random
import pytest

from ngts.nvos_constants.constants_nvos import ApiType, OutputFormat, PlatformConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.platform.Platform import Platform
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_software(engines, test_api, output_format):
    """nv show platform software"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show software output"):
        output = OutputParsingTool.parse_show_output_to_dict(platform.software.show(output_format=output_format),
                                                             output_format=output_format).get_returned_value()
        assert output, f"'nv show platform software' returned empty output"
        if test_api == ApiType.OPENAPI:
            installed_str = "installed"
            ValidationTool.validate_set_equal(output.keys(), {installed_str}).verify_result()
            output = output[installed_str]
        ValidationTool.validate_set_equal(tuple(output.values())[0].keys(), PlatformConsts.SW_FIELD_NAMES
                                          ).verify_result()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_software_installed(engines, test_api, output_format):
    """`nv show platform software installed` and `nv show platform software installed <software-id>`"""
    TestToolkit.tested_api = test_api

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show software installed output"):
        output = OutputParsingTool.parse_show_output_to_dict(
            platform.software.installed.show(output_format=output_format),
            output_format=output_format).get_returned_value()
        assert output, f"'nv show platform software installed' returned empty output"
        ValidationTool.validate_set_equal(tuple(output.values())[0].keys(), PlatformConsts.SW_FIELD_NAMES
                                          ).verify_result()

    with allure.step("Verify output for a specific SW"):
        random_software = random.choice(tuple(output.keys()))
        logging.info(f"Verify fields for {random_software}")
        specific_output = OutputParsingTool.parse_show_output_to_dict(
            platform.software.installed.show(op_param=random_software, output_format=output_format),
            output_format=output_format).get_returned_value()
        ValidationTool.validate_set_equal(specific_output.keys(), PlatformConsts.SW_FIELD_NAMES).verify_result()
