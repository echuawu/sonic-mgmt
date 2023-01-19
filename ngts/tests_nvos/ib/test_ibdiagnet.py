import pytest
import allure
import random
import logging
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import IbConsts

logger = logging.getLogger()


@pytest.mark.ib
def test_ibdiagnet_run(engines):
    """
    Test flow:
            1. run nv show ibdiagnet
            2. verify file not exist message
            3. run cd /var/tmp/ibdiagnet2
            4. verify "no such file or directory" message
            5. nv action run ib cmd ”ibdiagnet --get_phy_info“
            6. verify the  "message about action success"
            7. nv show ib ibdiagnet
            8. Verify it’s not empty and check file size (use splitlines and constant min_lines)
            9. run cd /var/tmp/ibdiagnet2
            11. Check if ibdiagnet_output.tgz exist
            12. verify all expected files in ibdiagnet_output.tgz
            13. run nv action reboot system
            14. nv show ib ibdiagnet verify it’s not empty and check file size (use splitlines and constant min_lines)
            15. run nv action delete ib ibdiagnet ibdiagnet_output.tgz
    :param engines:
    :return:
    """
    ib = Ib(None)
    with allure.step('Validate ibdiagnet files does not exist by default'):
        error_message = "file not exist message"
        assert error_message in ib.ibdiagnet.show(), "ibdiagnet dump files should be deleted"

    with allure.step('Validate ibdiagnet directory does not exist'):
        output = engines.dut.run_cmd('cd {path}'.format(path=IbConsts.IBDIAGNET_PATH))
        error_message = "file not exist message"
        assert error_message in output, "ibdiagnet temp directory should be deleted"

    expected_msg = 'WE NEED TO ADD THE RIGHT MESSAGE'
    ib.ibdiagnet.action_run(command=IbConsts.IBDIAGNET_COMMAND, option=IbConsts.IBDIAGNET_PHY_INFO, expected_str=expected_msg)

    with allure.step('Make sure the files are created under the right expected path'):
        show_output = ib.ibdiagnet.show()
        with allure.step('check the ibdiagnet.log file size'):
            assert len(show_output.splitlines()) > IbConsts.IBDIAGNET_LOG_FINE_MIN_LINES, "the ibdiagnet log file is not good enough"

        with allure.step('validate the ibdiagnet path'):
            output = engines.dut.run_cmd('ls {path}'.format(path=IbConsts.IBDIAGNET_PATH))
            assert IbConsts.IBDIAGNET_FILE_NAME in output, "the ibdiagnet file is missing"

        with allure.step('verify all expected files in ibdiagnet_output.tgz'):
            ValidationTool.verify_all_files_in_compressed_folder(engines.dut, IbConsts.IBDIAGNET_FILE_NAME, IbConsts.IBDIAGNET_EXPECTED_FILES_LIST).verify_result()

    with allure.step('Make sure all ibdiagnet files still available after reboot'):
        system = System(None)
        system.reboot.action_reboot()
        show_output = ib.ibdiagnet.show()
        with allure.step('check the ibdiagnet.log file size'):
            assert len(
                show_output.splitlines()) > IbConsts.IBDIAGNET_LOG_FINE_MIN_LINES, "the ibdiagnet log file is not good enough"

    with allure.step('Delete the ibdiagnet file'):
        ib.ibdiagnet.action_delete(file_name=IbConsts.IBDIAGNET_FILE_NAME)


@pytest.mark.ib
def test_ibdiagnet_run_multiple_times(engines):
    """
    Validate only one ibdianget file will be exist after generating it many times
    :param engines:
    :return:
    """
    ib = Ib(None)
    expected_msg = 'WE NEED TO ADD THE RIGHT MESSAGE'
    tries_number = 5
    with allure.step('try to generate ibdiagnet file {tries} times'.format(tries=tries_number)):
        for i in range(0, tries_number):
            ib.ibdiagnet.action_run(command=IbConsts.IBDIAGNET_COMMAND, option=IbConsts.IBDIAGNET_PHY_INFO, expected_str=expected_msg)

    with allure.step('Validate only one ibdianget file will be exist after generating it {tries} times'.format(tries=tries_number)):
        engines.dut.run_cmd('cd {path}'.format(path=IbConsts.IBDIAGNET_PATH))
        output = engines.dut.run_cmd('ls')
        assert len(output.splitlines()) == 1, "more than ibdiagnet files are exist"


@pytest.mark.ib
def test_ibdiagnet_negative(engines):
    """
    Will validate the two invalid cases to run the ibdiagnet generating command "nv action run ib cmd"
    case1: using string != ibdiagnet
    case2: using invalid option, for now the valid optoions = [get_phy_info, get_ cable_info]
    Test flow:
            1. generate invalid command
            2. run nv action run ib cmd <invalid_cmd>
            3. verify error message
            4. generate <invalid_opt>
            5. run nv action run ib cmd "ibdiagnet --<invalid_opt>"
            6. verify error message
    :param engines:
    :return:
    """
    ib = Ib(None)
    invalid_cmd = "ibdiagnetfile"
    invalid_opt = "--ibdiagnetfile"
    error_message = "UPDATE THE MESSAGE AND MAYBE DIFFERENT MESSAGES"
    with allure.step('try to generate ibdiagnet using invalid commands'):

        with allure.step('try to use ibdiagnet generating command with invalid string {invalid_cmd} and verify error message'.format(invalid_cmd=invalid_cmd)):
            ib.ibdiagnet.action_run(command=invalid_cmd, expected_str=error_message)

        with allure.step('try to use ibdiagnet generating command with invalid option {invalid_opt} and verify error message'.format(
                invalid_opt=invalid_opt)):
            ib.ibdiagnet.action_run(command=IbConsts.IBDIAGNET_COMMAND, option=invalid_opt, expected_str=error_message)


@pytest.mark.ib
def test_ibdiagnet_upload(engines):
    """
    Test flow:
        1. upload non exist ibdiagnet file
        2. verify the error message
        3. generate ibdiagnet
        4. upload to valid_url
        5. verify the success message
        6. check the size of tgz in target path
        7. run nv show ib ibdiagnet and verify the log file len
        8. invalid_url_1 : using invalid format nv action upload ib ibdiagnet ibdiagnet_output.tgz <invalid_url1>
        9. invalid_url_2 : using invalid opt nv action upload ib ibdiagnet ibdiagnet_output.tgz <invalid_url2>
        10. run nv action upload ib ibdiagnet with invalid1 and verify error message
        11. run nv action upload ib ibdiagnet with invalid1 and verify error message
    :param engines:
    :return:
    """
    ib = Ib(None)
    expected_msg = "MSG"
    expected_msg_upload = "MSG"
    player = engines['sonic_mgmt']
    invalid_url_1 = 'scp://{}:{}{}/tmp/'.format(player.username, player.password, player.ip)
    invalid_url_2 = 'ffff://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)
    upload_path = 'scp://{}:{}@{}/tmp/'.format(player.username, player.password, player.ip)
    with allure.step('try to upload non exist ibdiagnet file'):
        output = ib.ibdiagnet.action_upload(upload_path=upload_path)
        assert "error message" in output, "we can not upload a non exist file!"
        ib.ibdiagnet.action_run(command=IbConsts.IBDIAGNET_COMMAND, option=IbConsts.IBDIAGNET_PHY_INFO,
                                expected_str=expected_msg)

    with allure.step('try to upload ibdiagnet to - Positive Flow'):
        output = ib.ibdiagnet.action_upload(upload_path=upload_path)
        with allure.step('verify the upload message'):
            assert expected_msg_upload in output, "Failed to upload the ibdiagnet file"

        with allure.step('verify file size in target directory'):
            ValidationTool.verify_all_files_in_compressed_folder(engines.dut, '/tmp/' + IbConsts.IBDIAGNET_FILE_NAME, IbConsts.IBDIAGNET_EXPECTED_FILES_LIST).verify_result()

        with allure.step('verify file size in target directory'):
            show_output = ib.ibdiagnet.show()
            assert len(show_output.splitlines()) == IbConsts.IBDIAGNET_LOG_FINE_MIN_LINES, "the ibdiagnet log file size has been change after uploading"

    with allure.step('try to upload ibdiagnet to inalid url - url is not in the right format'):
        output = ib.ibdiagnet.action_upload(upload_path=invalid_url_1)
        assert "ERROR MESSAGE" in output, "URL was not in the right format"

    with allure.step('try to upload ibdiagnet to inalid url - using non supported transfer protocol'):
        output = ib.ibdiagnet.action_upload(upload_path=invalid_url_2)
        assert "ERROR MESSAGE" in output, "URL used non supported transfer protocol"


@pytest.mark.ib
def test_ibdiagnet_delete(engines):
    """
    Test flow:
            1. run nv action run ib cmd ”ibdiagnet --get_cable_info“
            2. verify “message about action success” message
            3. try to delete with invalid file name
            4. verify error message and files still exist
            5. run nv action delete ib ibdiagnet ibdiagnet_output.tgz
            6. nv show ib ibdiagnet
            7. verify file not exists
            8. run cd /var/tmp/ibdiagnet2
            9. verify “no such file or directory”  message
            9. try to delete non exist ibdiagnet files
            10. verify error message
    :param engines:
    :return:
    """
    ib = Ib(None)
    success_message = "NEED TO ADD THE RIGHT MESSAGE"
    ib.ibdiagnet.action_run(command=IbConsts.IBDIAGNET_COMMAND, option='--get_cable_info', expected_str=success_message)

    with allure.step('Try to delete with invalid file name'):
        output = ib.ibdiagnet.action_delete(file_name='ibdiagnetfile')
        assert "INVALID MESSAGE - NEED TO UPDATE" in output, "ibdiagnet name should be {file_name}".format(file_name=IbConsts.IBDIAGNET_FILE_NAME)

    with allure.step('Validate we can delete ibdiagnet files'):
        output = ib.ibdiagnet.action_delete(file_name=IbConsts.IBDIAGNET_FILE_NAME)
        assert 'message about action success' in output, "ibdiagnet delete action failed"

        with allure.step('verify ibdiagnet file does not exist using show command'):
            show_output = ib.ibdiagnet.show()
            assert "" in show_output, "the ibdiagnet file should be deleted"

        with allure.step('Validate ibdiagnet directory does not exist anymore'):
            assert "no such file or directory" in engines.dut.run_cmd('cd {path}'.format(path=IbConsts.IBDIAGNET_PATH)), "ibdiagnet directory should be deleted"

    with allure.step('Try to delete non exist ibdiagnet file'):
        output = ib.ibdiagnet.action_delete(file_name=IbConsts.IBDIAGNET_FILE_NAME)
        assert "UPDATE MESSAGE" in output, "can not delete non exist ibdiagnet file".format(file_name=IbConsts.IBDIAGNET_FILE_NAME)
