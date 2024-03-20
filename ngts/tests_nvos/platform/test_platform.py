import logging
import pytest

from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform(engines, test_api):
    """
    Validates the output of nv show platform.
    The OpenAPI test checks the JSON output while the NVUE test checks the auto output.
    Test flow:
        1. nv show platform (json output for OpenAPI test, auto output for NVUE test)
        2. Parse output to dict
        3. Validate all keys (field names) exist and there are no extra keys
        4. Validate all values are correct
    """
    TestToolkit.tested_api = test_api
    with allure.step("Create system object"):
        platform = Platform()

    output_format = OutputFormat.auto if test_api == ApiType.NVUE else OutputFormat.json
    output = OutputParsingTool.parse_show_output_to_dict(platform.show(output_format=output_format),
                                                         output_format=output_format).get_returned_value()
    ValidationTool.validate_output_of_show(output, TestToolkit.devices.dut.show_platform_output).verify_result()
