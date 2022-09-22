import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat

logger = logging.getLogger()


@pytest.mark.platform
def test_show_platform(engines):
    """
    Show platform hardware test
    """
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
