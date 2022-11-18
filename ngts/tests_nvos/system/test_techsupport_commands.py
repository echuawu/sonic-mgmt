import pytest
import allure
import datetime
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import SystemConsts


@pytest.mark.system
def test_techsupport_show(engines):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv show system tech-support files
        2. run nv action generate system tech-support
        3. run nv action generate system tech-support
        4. validate new tar.gz files exist and first output < second output
    """
    system = System(None)
    with allure.step('Run show/action system tech-support and verify that each results updated as expected'):
        output_dictionary_before_actions = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_dictionary(
            system.techsupport.show()).get_returned_value()
        system.techsupport.action_generate()
        system.techsupport.action_generate()
        output_dictionary_after_actions = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_dictionary(
            system.techsupport.show()).get_returned_value()

    validate_techsupport_output(output_dictionary_before_actions, output_dictionary_after_actions)


@pytest.mark.system
def test_techsupport_since(engines):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv action generate system tech-support since <today_time>
        2. run nv show system tech-support files
        3. validate new tar.gz file exist
    """
    system = System(None)
    with allure.step('Run show/action system tech-support and verify that each results updated as expected'):
        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y%m%d")
        tech_support_folder = system.techsupport.action_generate(SystemConsts.ACTIONS_GENERATE_SINCE, yesterday_str)
        output_dictionary = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_dictionary(
            system.techsupport.show()).get_returned_value()

    validate_techsupport_since(output_dictionary, tech_support_folder)


@pytest.mark.system
def test_techsupport_since_invalid_date(engines):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv action generate system tech-support since <syntax_error>
        2. validate Invalid date in the output
    """
    system = System(None)
    invalid_date_syntax = '20206610'
    with allure.step('Validating the generate command failed because '
                     'of Invalid date {invalid_date_syntax}'.format(invalid_date_syntax=invalid_date_syntax)):
        output_dictionary = system.techsupport.action_generate(option=SystemConsts.ACTIONS_GENERATE_SINCE,
                                                               time=invalid_date_syntax)
        assert 'Command failed with the following output' in output_dictionary, ""

    invalid_date_syntax = 'aabbccdd'
    with allure.step('Validating the generate command failed because '
                     'of Invalid date {invalid_date_syntax}'.format(invalid_date_syntax=invalid_date_syntax)):
        output_dictionary = system.techsupport.action_generate(option=SystemConsts.ACTIONS_GENERATE_SINCE,
                                                               time=invalid_date_syntax)
        assert 'Command failed with the following output' in output_dictionary, ""


def validate_techsupport_output(output_dictionary_before, output_dictionary_after):
    with allure.step('Validating the generate command and show command working as expected'):
        new_folders = [file for file in output_dictionary_after if file not in output_dictionary_before]
        assert len(new_folders) == 2, "at least one of the new tech-support folders not found"


def validate_techsupport_since(output_dictionary, substring):
    with allure.step('Validating the generate command and show command working as expected'):
        assert substring in output_dictionary,\
            "at least one of the new tech-support folders not found, expected folders"
