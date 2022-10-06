import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.platform
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
                assert 'operational' in list_of_sw[0] and 'applied' in list_of_sw[0] and 'description' in list_of_sw[0], \
                    "Titles cant be found in the output"
                if not is_redmine_issue_active([3215476]):
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
                assert "Installed software" in list_of_sw[0] and "description" in list_of_sw[0], \
                    "Titles cant be found in the output"
                if not is_redmine_issue_active([3215476]):
                    assert len(list_of_sw) > 2 and list_of_sw[2], "The list of installed software is empty"

        with allure.step("Verify json output"):
            logging.info("Verify json output")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                platform.software.show("installed")).get_returned_value()
            assert output and len(output.keys()) > 0, "The list of installed software is empty"
