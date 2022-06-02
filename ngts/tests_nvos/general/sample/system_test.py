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

    snippet_name = "test-snippet-1"
    snippet_value = {
        "file": "/tmp/test-snippet-1",
        "content": "hello world - snippet-1",
        "permissions": "0777"
    }
    system.config.snippet.set(snippet_name, snippet_value)

    output = system.config.snippet.show()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()

    ValidationTool.verify_field_exist_in_json_output(output_dictionary, [snippet_name]).verify_result()
