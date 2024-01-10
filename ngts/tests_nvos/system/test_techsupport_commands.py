import pytest
import datetime
import json
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime


@pytest.mark.system
def test_techsupport_show(engines, test_name):
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
    operation = 'generate tech-support'
    duration = 0
    with allure.step('Run show/action system tech-support and verify that each results updated as expected'):
        output_dictionary_before_actions = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_list(
            system.techsupport.show()).get_returned_value()
        folder, duration = system.techsupport.action_generate(test_name=test_name)
        assert OperationTime.verify_operation_time(duration, operation), \
            '{op} took more time than threshold value'.format(op=operation)
        folder, duration = system.techsupport.action_generate()
        assert OperationTime.verify_operation_time(duration, operation), \
            '{op} took more time than threshold value'.format(op=operation)
        output_dictionary_after_actions = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_list(
            system.techsupport.show()).get_returned_value()
        validate_techsupport_output(output_dictionary_before_actions, output_dictionary_after_actions, 2)

    with allure.step('Validate show tech-support command format'):
        show_output = system.techsupport.show()
        tech_support_files_list_with_path = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_list(show_output).get_returned_value()
        output_dictionary_json = json.loads(show_output).keys()
        techsupport_names_without_path = [file.replace('/host/dump/', '') for file in tech_support_files_list_with_path]
        assert output_dictionary_json != techsupport_names_without_path, "The show tech-support command format is not as expected, output: {} expected: {}".format(output_dictionary_json, techsupport_names_without_path)


@pytest.mark.system
def test_techsupport_since(engines, test_name):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv action generate system tech-support since <today_time>
        2. run nv show system tech-support files
        3. validate new tar.gz file exist
    """
    system = System(None)
    operation = 'generate tech-support'
    with allure.step('Run show/action system tech-support and verify that each results updated as expected'):
        yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y%m%d")
        tech_support_folder, duration = system.techsupport.action_generate(engines.dut, SystemConsts.ACTIONS_GENERATE_SINCE,
                                                                           yesterday_str, test_name=test_name)
        output_dictionary = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_list(
            system.techsupport.show()).get_returned_value()
        validate_techsupport_since(output_dictionary, tech_support_folder)
        assert OperationTime.verify_operation_time(duration, operation), \
            '{op} took more time than threshold value'.format(op=operation)


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
        output_dictionary, duration = system.techsupport.action_generate(option=SystemConsts.ACTIONS_GENERATE_SINCE,
                                                                         since_time=invalid_date_syntax)
        assert 'Command failed with the following output' in output_dictionary, ""

    invalid_date_syntax = 'aabbccdd'
    with allure.step('Validating the generate command failed because '
                     'of Invalid date {invalid_date_syntax}'.format(invalid_date_syntax=invalid_date_syntax)):
        output_dictionary, duration = system.techsupport.action_generate(option=SystemConsts.ACTIONS_GENERATE_SINCE,
                                                                         since_time=invalid_date_syntax)
        assert 'Command failed with the following output' in output_dictionary, ""


@pytest.mark.system
def test_techsupport_delete(engines):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv action generate system tech-support save as <first_file>
        2. run nv action generate system tech-support save as <second_file>
        3. run nv action delete system techsupport file <first_file>
        4. verify "File delete successfully" message
        5. run nv show system techsupport files
        6. verify <second_file> still exist and <first_file> has been deleted
        7. run nv action delete system techsupport file <first_file>
        8. File not found: <first_file>
    """
    system = System(None)
    success_message = 'File delete successfully'
    with allure.step('Run action delete system tech-support and verify that each results updated as expected'):

        with allure.step('Generate two tech-support files'):
            first_file, duration = system.techsupport.action_generate()
            second_file, duration = system.techsupport.action_generate()

        with allure.step('Delete the first created tech-support file'):
            output = system.techsupport.action_delete(first_file.replace('/host/dump/', '')).get_returned_value()

        assert success_message in output, 'failed to delete'
        output_dictionary_after_delete = Tools.OutputParsingTool.parse_show_system_techsupport_output_to_list(
            system.techsupport.show()).get_returned_value()

        with allure.step('Check {} has been deleted and {} still exist'.format(first_file, second_file)):
            assert first_file not in output_dictionary_after_delete, "{} still exist even after deleting it".format(first_file)
            assert second_file in output_dictionary_after_delete, "{} does not exist".format(second_file)

        with allure.step('Delete non exist tech-support file {}'.format(first_file)):
            res_obj = system.techsupport.action_delete(first_file.replace('/host/dump/', ''))
            res_obj.verify_result(should_succeed=False)
            assert 'Action failed with the following issue:' in res_obj.info, "Can not delete non exist file!"


@pytest.mark.system
def test_techsupport_upload(engines):
    """
    Test flow:
        1. upload non exist tech-support file
        2. verify the error message
        3. generate tech-support file save as tech_file
        4. upload to valid_url
        5. verify the success message
        6. check the size of tgz in target path
        7. invalid_url_1 : using invalid format nv action upload system techsupport files <tech_file> <invalid_url1>
        8. invalid_url_2 : using invalid opt nv action upload system techsupport files <tech_file> <invalid_url2>
        9. run nv action upload system techsupport files  <tech_file> <invalid_url1> and verify error message
        10. run nv action upload system techsupport files  <tech_file> <invalid_url2> and verify error message
    :param engines:
    :return:
    """
    system = System(None)
    with allure.step('generate valid and invalid urls'):
        player = engines['sonic_mgmt']
        invalid_url_1 = 'scp://{}:{}{}/tmp/'.format(player.username, player.password, player.ip)
        invalid_url_2 = 'ffff://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)
        upload_path = 'scp://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)

    with allure.step('Try to upload non exist tech-support file'):
        output = system.techsupport.action_upload(file_name='nonexist', upload_path=upload_path)
        assert "File not found: nonexist" in output.info, "we can not upload a non exist file!"

    with allure.step('Generate tech-support file'):
        result_obj, duration = system.techsupport.action_generate()
        tech_file = result_obj.replace('/host/dump/', '')

    with allure.step('try to upload techsupport {} to {} - Positive Flow'.format(tech_file, upload_path)):
        output = system.techsupport.action_upload(upload_path, tech_file).verify_result()
        with allure.step('verify the upload message'):
            assert "File upload successfully" in output, "Failed to upload the techsupport file"

        with allure.step('verify the uploaded file exist in target path'):
            output = player.run_cmd('ls /tmp/')
            assert tech_file in output

    with allure.step('try to upload techsupport to invalid url - url is not in the right format'):
        output = system.techsupport.action_upload(file_name='nonexist', upload_path=invalid_url_1)
        assert "is not a" in output.info, "URL was not in the right format"

    with allure.step('try to upload ibdiagnet to invalid url - using non supported transfer protocol'):
        output = system.techsupport.action_upload(file_name='nonexist', upload_path=invalid_url_2)
        assert "is not a" in output.info, "URL used non supported transfer protocol"


@pytest.mark.system
def test_techsupport_multiple_times(engines, test_name):
    """
    Run nv show system tech-support files command and verify the required fields are exist
    command: nv show system tech-support files

    Test flow:
        1. run nv action generate system tech-support 4 times in a row
    """
    system = System(None)
    operation = 'generate tech-support'
    with allure.step('Run show/action system tech-support 4 times in a row'):
        for i in range(0, 4):
            with allure.step("Generate Tech-Support for the {} time".format(i)):
                folder, duration = system.techsupport.action_generate(test_name=test_name)
                assert OperationTime.verify_operation_time(duration, operation), \
                    '{op} took more time than threshold value'.format(op=operation)


@pytest.mark.system
def test_techsupport_size(engines, test_name):
    """
    Run nv action generate system tech-support and verify output file size
    command: nv action generate system tech-support

    Test flow:
        1. run nv action generate system tech-support
        2. check file size by du -sh
        3. assert if size > 50 MB
    """
    engine = engines.dut
    system = System(None)
    with allure.step('Run generate tech-support'):
        tech_support_folder, duration = system.techsupport.action_generate()
        output = engine.run_cmd('sudo du -sh ' + tech_support_folder)
        size_in_MB = int(output.split("M")[0])
        assert size_in_MB < 50, f"{tech_support_folder} size ({size_in_MB}MB) should be less than 50MB"


def validate_techsupport_output(output_dictionary_before, output_dictionary_after, number_of_expected_files):
    with allure.step('Validating the generate command and show command working as expected'):
        new_folders = [file for file in output_dictionary_after if file not in output_dictionary_before]
        assert len(new_folders) == number_of_expected_files + 1, \
            "at least one of the new tech-support folders not found"


def validate_techsupport_since(output_dictionary, substring):
    with allure.step('Validating the generate command and show command working as expected'):
        assert substring in output_dictionary, \
            "at least one of the new tech-support folders not found, expected folders"


# ------------ Open API tests -----------------

@pytest.mark.system
@pytest.mark.openapi
def test_techsupport_show_openapi(engines, test_name):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_techsupport_show(engines, test_name)


@pytest.mark.system
@pytest.mark.openapi
def test_techsupport_since_openapi(engines, test_name):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_techsupport_since(engines, test_name)


@pytest.mark.system
@pytest.mark.openapi
def test_techsupport_since_invalid_date_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_techsupport_since_invalid_date(engines)


@pytest.mark.system
@pytest.mark.openapi
def test_techsupport_multiple_times_openapi(engines, test_name):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_techsupport_multiple_times(engines, test_name)
