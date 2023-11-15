import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
def test_show_platform_software(engines):
    """
    Show platform software test
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Check show software output"):
        if TestToolkit.tested_api == ApiType.NVUE:
            with allure.step("Verify text output"):
                logging.info("Verify text output")
                output = platform.software.show(output_format=OutputFormat.auto)
                list_of_sw = output.split("\n", 3)
                assert 'operational' in list_of_sw[0] and 'applied' in list_of_sw[0], \
                    "Titles cant be found in the output"
                assert len(list_of_sw) > 2 and list_of_sw[2], "The list of installed software is empty"

        with allure.step("Verify json output"):
            logging.info("Verify json output")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(platform.software.show()).get_returned_value()
            assert output and len(output.keys()) > 0, "The list of installed software is empty"

    with allure.step("Check show software installed output"):
        if TestToolkit.tested_api == ApiType.NVUE:
            with allure.step("Verify text output"):
                logging.info("Verify text output")
                output = platform.software.show("installed", output_format=OutputFormat.auto)
                list_of_sw = output.split("\n", 3)
                assert "Installed software" in list_of_sw[0], "'Installed software' title can't be found in the output"
                assert len(list_of_sw) > 2 and list_of_sw[2], "The list of installed software is empty"

        with allure.step("Verify json output"):
            logging.info("Verify json output")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.software.show("installed")).get_returned_value()
            assert output and len(output.keys()) > 0, "The list of installed software is empty"

        with allure.step("Verify json output for a specific SW"):
            logging.info("Verify json output for a specific SW")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.software.show("installed {}".format(list(output.keys())[1]))).get_returned_value()
            assert not any(field not in output for field in ["description", "package", "version"]), \
                "Not all required fields were found"


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.nvos_chipsim_ci
def test_show_platform_software_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_platform_software(engines)
