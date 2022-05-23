import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool

logger = logging.getLogger()


@pytest.mark.general
def test_system_sample(engines):
    """
    Sample test for system
    """
    system = System(None)

    with allure.step("Update ignore id to <ignore_id>"):
        system.config.apply.ignore.ignore_id = "<ignore_id>"

    ignore_str = '<ignore_str>'

    system.config.apply.ignore.set(ignore_str)

    output = system.config.apply.ignore.show()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()

    ValidationTool.verify_field_exist_in_json_output(output_dictionary, [ignore_str]).verify_result()
