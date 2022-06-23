import logging
import pytest
import allure
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool

logger = logging.getLogger()


@pytest.mark.checklist
def test_show_platform_firmware(engines):
    """
    Show platform firmware test
    """

    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Run show platform firmware"):
        logging.info("Run show command to view platform firmware")
        output = platform.firmware.show()
        platform_firmware = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
        assert platform_firmware, "The output is empty"

    with allure.step("Run show platform <component_id> and compare the output to the general output"):
        for component_id, component_prop in platform_firmware.items():
            with allure.step("Verify fields of component id '{}'".format(component_id)):
                logging.info("Verify fields of component id '{}'".format(component_id))
                output = platform.firmware.show(component_id)
                component_id_prop = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
                ValidationTool.compare_dictionaries(component_prop, component_id_prop).verify_result()
