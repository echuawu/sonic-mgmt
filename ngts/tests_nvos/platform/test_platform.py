import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from infra.tools.redmine.redmine_api import is_redmine_issue_active

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
def test_show_platform(engines):
    """
    Show platform hardware test
    """
    res = is_redmine_issue_active([3640664])
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show platform output"):
        with allure.step("Verify text output"):
            logging.info("Verify text output")
            logging.info("Required comp: " + str(PlatformConsts.PLATFORM_OUT_COMP))
            output = platform.show(output_format=OutputFormat.auto)
            assert not any(comp not in output for comp in PlatformConsts.PLATFORM_OUT_COMP), \
                "Not all required components were found"

        with allure.step("Verify json output"):
            logging.info("Verify json output")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.show()).verify_result()
            main_keys = output.keys()
            assert PlatformConsts.PLATFORM_ENVIRONMENT in main_keys, \
                PlatformConsts.PLATFORM_ENVIRONMENT + " can't be found in the output"
            assert PlatformConsts.PLATFORM_HW in main_keys, \
                PlatformConsts.PLATFORM_HW + " can't be found in the output"
            Tools.ValidationTool.verify_field_exist_in_json_output(output[PlatformConsts.PLATFORM_ENVIRONMENT],
                                                                   PlatformConsts.ENV_COMP).verify_result()
            Tools.ValidationTool.verify_field_exist_in_json_output(output[PlatformConsts.PLATFORM_HW],
                                                                   ["component"]).verify_result()


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
def test_show_platform_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform(engines)
