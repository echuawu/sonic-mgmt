import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_constants.constants_nvos import OutputFormat

logger = logging.getLogger()


@pytest.mark.platform
def test_show_platform_firmware(engines):
    """
    Show platform firmware test
    """
    with allure.step("Create System object"):
        platform = Platform()

    """with allure.step("Check tab suggestion"):
        output = platform.get_tab_output("firmware")
        Tools.ValidationTool.validate_all_values_exists_in_list(PlatformConsts.FW_COMP, output).verify_result()"""

    with allure.step("Check show firmware output"):
        with allure.step("Verify text output"):
            logging.info("Verify text output")
            output = platform.firmware.show(output_format=OutputFormat.auto)
            logging.info("Required comp: " + str(PlatformConsts.FW_COMP))
            assert not any(comp not in output for comp in PlatformConsts.FW_COMP), \
                "Not all required component were found"

        with allure.step("Verify json output"):
            logging.info("Verify json output")
            output = Tools.OutputParsingTool.parse_json_str_to_dictionary(platform.firmware.show()).get_returned_value()
            Tools.ValidationTool.verify_field_exist_in_json_output(output, PlatformConsts.FW_COMP, True).verify_result()

        with allure.step("Compare general output to each firmware component"):
            logging.info("Compare general output to each firmware component")
            for comp_name, comp_output in output.items():
                _compare_general_output_to_comp_output(platform, comp_name, comp_output)


def _compare_general_output_to_comp_output(platform, comp_name, general_comp_output):
    logging.info("Check {} component output")
    with allure.step("Verify all fields exist in the output"):
        comp_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(platform.firmware.show(
            comp_name)).verify_result()
        Tools.ValidationTool.verify_field_exist_in_json_output(comp_output, PlatformConsts.FW_FIELDS).verify_result()

    with allure.step("Verify 'type' and 'actual-firmware'"):
        assert comp_output["type"] in comp_name, "the type is not equal to component name"
        assert comp_output["actual-firmware"] != "N/A", "actual-firmware can't be N/A"

    if comp_name == PlatformConsts.FW_SSD:
        with allure.step("Verify 'part-number' and 'serial-number' foe FW SSD"):
            assert comp_output["part-number"] != "N/A", "part-number can't be N/A"
            assert comp_output["serial-number"] != "N/A", "serial-number can't be N/A"

    with allure.step("Verify all {} fields and values equal to general output".format(comp_name)):
        Tools.ValidationTool.compare_dictionary_content(comp_output, general_comp_output).verify_result()
