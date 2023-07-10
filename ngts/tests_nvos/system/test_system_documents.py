import logging
import allure
import pytest
import random
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import DocumentsConsts

logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.simx
def test_show_document(engines):
    """
    Run nv show system documentation command and verify the docs paths and types
        Test flow:
            1. run nv show system documentation
            2. for each file validate: the right path and type
    """
    system = System()
    with allure.step('Run nv show system documentation'):
        output = OutputParsingTool.parse_json_str_to_dictionary(system.documentation.show()).verify_result()
    with allure.step('Verify all the documents paths'):
        verify_documents_path(output, 'path')
    with allure.step('Verify all the documents types'):
        verify_documents_type(output, 'type')


@pytest.mark.system
@pytest.mark.simx
def test_show_document_files(engines):
    """
    Run nv show system documentation files command and verify the docs paths
        Test flow:
            1. run nv show system documentation
            2. for each file validate: the right path
    """
    system = System()
    with allure.step('Run nv show system documentation files'):
        output_files = OutputParsingTool.parse_json_str_to_dictionary(system.documentation.show('files')).verify_result()
    with allure.step('Verify all the documents paths'):
        verify_documents_path(output_files, 'path')
    with allure.step('Verify all the documents size'):
        verify_documents_size(engines.dut)


@pytest.mark.system
@pytest.mark.simx
def test_upload_document(engines):
    """
    Test flow:
        1. pick randomly one of the user docs save as <random_file>
        2. upload to valid_url using nv action upload system documentation files <random_file> <invalid_url>
        3. verify the success message
        4. invalid_url_1 : using invalid url format <invalid_url1>
        5. invalid_url_2 : using invalid opt <invalid_url2>
        6. run nv action upload system documentation files <random_file> <invalid_url1> and verify error message
        7. run nv action upload system documentation files <random_file> <invalid_url2> and verify error message
    :param engines:
    :return:
    """
    system = System(None)
    expected_msg_upload = "File upload successfully"
    player = engines['sonic_mgmt']
    invalid_url_1 = 'scp://{}:{}{}/tmp/'.format(player.username, player.password, player.ip)
    invalid_url_2 = 'ffff://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)
    upload_path = 'scp://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)

    random_file = random.choice([DocumentsConsts.FILE_NAME_RELEASE_NOTES, DocumentsConsts.FILE_NAME_OPEN_SOURCE_LICENSES, DocumentsConsts.FILE_NAME_USER_MANUAL, DocumentsConsts.FILE_NAME_EULA])
    with allure.step('try to upload one of the user docs - Positive Flow'):
        output = system.documentation.action_upload(file_name=random_file, upload_path=upload_path)
        with allure.step('verify the upload message'):
            assert expected_msg_upload in output.returned_value, "Failed to upload {}".format(random_file)

    with allure.step('try to upload {} to invalid url - url is not in the right format'.format(random_file)):
        output = system.documentation.action_upload(file_name=random_file, upload_path=invalid_url_1)
        assert "is not a" in output.info, "URL was not in the right format"

    with allure.step('try to upload {} to invalid url - using non supported transfer protocol'.format(random_file)):
        output = system.documentation.action_upload(file_name=random_file, upload_path=invalid_url_2)
        assert "is not a" in output.info, "URL used non supported transfer protocol"


def verify_documents_type(output, validation_key):
    """

    :param output:
    :param validation_key:
    :return:
    """
    types = [DocumentsConsts.TYPE_EULA, DocumentsConsts.TYPE_RELEASE_NOTES, DocumentsConsts.TYPE_USER_MANUAL,
             DocumentsConsts.TYPE_OPEN_SOURCE_LICENSES]
    verify_documents(output, validation_key, types)


def verify_documents_path(output, validation_key):
    """

    :param output:
    :param validation_key:
    :return:
    """
    paths = [DocumentsConsts.PATH_EULA, DocumentsConsts.PATH_RELEASE_NOTES, DocumentsConsts.PATH_USER_MANUAL, DocumentsConsts.PATH_OPEN_SOURCE_LICENSES]
    verify_documents(output, validation_key, paths)


def verify_documents_size(engine):
    files_list = [DocumentsConsts.PATH_EULA, DocumentsConsts.PATH_RELEASE_NOTES, DocumentsConsts.PATH_USER_MANUAL]
    error_msg = ''
    for file in files_list:
        temp = int(engine.run_cmd('stat -c %s {}'.format(file)).splitlines()[0])
        if DocumentsConsts.MIN_FILES_SIZE > temp:
            error_msg += "The {} expected size should be more than {} and the current size is {}".format(file, DocumentsConsts.MIN_FILES_SIZE, temp)
    assert not error_msg, error_msg


def verify_documents(output, validation_key, expected_list):
    """

    :param output: the dic of nv show system documentation
    :param validation_key: could be path or type
    :param expected_list: the expected list
    :return:
    """
    with allure.step('validate the output contains the expected list'):
        assert len(output.keys()) == len(expected_list), 'the expected out is {}, the output is {}'.format(output.keys(), expected_list)
    for key, value in zip(output.keys(), expected_list):
        assert validation_key in output[key].keys(), 'no {}'.format(validation_key)
        assert output[key][validation_key] == value, 'the {validation_key} of {key} is {val} not as expected {value}'.format(validation_key=validation_key, key=key, val=output[key][validation_key], value=value)
