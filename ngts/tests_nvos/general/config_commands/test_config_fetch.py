import time
import pytest
import logging
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.system.System import System
from ngts.constants.constants import MarsConstants
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import NvosConst
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()
YAML_FILES_PATH = MarsConstants.SONIC_MGMT_DIR + "/ngts/tests_nvos/general/config_commands/yaml_files"
YAML_FILES_LIST = ['/hostname_config.yaml', '/post_login_message_config.yaml', '/pre_login_message_config.yaml']


@pytest.mark.general
@pytest.mark.simx
def test_show_fetch_file(engines):
    """
    Test flow:
        1. Run nv show system config files
        2. verify it's empty
        3. Run nv action fetch system config <remote_url>/YAML_FILES_PATH/YAML_FILES_LIST[0]
        4. Expected success message: Fetching file: <file_name> ... File fetched successfully Action succeeded
        5. Run nv show system config files
        6. Expected output: "< file_name >": {
                                                "path": /host/config_files /<file_name> "
                                              }
        7. Run nv show system config files <file_name>
        8. Expected output: set: system: hostname: <new_hostname>
    """
    system = System(None)
    assert '{}' == system.config.files.show(), "the config files list should be empty"

    with allure.step('get remote server engine'):
        remote_server_engine = engines[NvosConst.SONIC_MGMT]

    yaml_file = YAML_FILES_LIST[0]
    logger.info('the yaml file name is {}'.format(yaml_file))

    with allure.step('get the remote url'):
        remote_url = DutUtilsTool.get_url(engine=remote_server_engine, command_opt='scp', file_full_path=YAML_FILES_PATH + yaml_file).verify_result()

    action_expected_str = "Fetching file: {} ...\nFile fetched successfully\nAction succeeded".format(yaml_file)

    expected_dict = {
        "path": '/host/config_files/{}'.format(yaml_file)
    }

    with allure.step('fetch {}'.format(yaml_file)):
        system.config.action_fetch(remote_url, action_expected_str)

    with allure.step('verify nv show system config files command after fetch'):
        assert expected_dict == OutputParsingTool.parse_json_str_to_dictionary(system.config.files.show()).verify_result()[yaml_file], "the dictionary should include only {}".format(yaml_file)

    with allure.step('verify nv show system config files <file_name> command after fetch'):
        output = OutputParsingTool.parse_json_str_to_dictionary(system.config.files.show(yaml_file)).verify_result()
        assert expected_dict == output[yaml_file], "the dictionary should include only {}".format(yaml_file)


@pytest.mark.general
@pytest.mark.simx
def test_export_applied_configurations(engines):
    """
    1. Run nv action export system config <file_name>.yaml
    2. Run nv set system message pre-login “TESTING”
    3. Run nv action export system config <before_apply>.yaml
    4. Run nv config apply
    5. Run nv action export system config <after_apply>.yaml
    6. compare <file_name> with <before_apply> - should be equal
    7. compare <before_apply> with <after_apply> - should not be equal
    :param engines:
    :return:
    """
    system = System(None)
    files_path = '/host/config_files/'
    action_expected_str = "Exporting completed\nAction succeeded"
    with allure.step('export {}'.format('current_conf.yaml')):
        system.config.action_export('current_conf.yaml', action_expected_str)

    with allure.step('set system pre-login message without apply'):
        system.message.set("EXPORT TESTS", engines.dut, field_name='pre-login', apply=False).verify_result(should_succeed=True)

    with allure.step('export {}'.format('before_apply.yaml')):
        system.config.action_export('before_apply.yaml', action_expected_str)

    with allure.step('apply message configuration'):
        NvueGeneralCli.apply_config(engines.dut)

    with allure.step('export {}'.format('after_apply.yaml')):
        system.config.action_export('after_apply.yaml', action_expected_str)

    with allure.step('verify current_conf.yaml equals to before_apply.yaml'):
        assert not engines.dut.run_cmd('diff {} {}'.format(files_path + 'current_conf.yaml',
                                                           files_path + 'before_apply.yaml')), "the two files should be equal"

    with allure.step('verify before_apply.yaml not equals to after_apply.yaml'):
        assert engines.dut.run_cmd('diff {} {}'.format(files_path + 'before_apply.yaml',
                                                       files_path + 'after_apply.yaml')), "the two files should not be equal"


@pytest.mark.general
@pytest.mark.simx
def test_rename_and_upload(engines):
    """
    1. Run nv action fetch system config <remote_url>/YAML_FILES_PATH/YAML_FILES_LIST[0]
    2. Run nv action rename system config files <file_name> <new_file_name
    3. Expected message :
                    config file <file_name> renamed to <new_file_name>
                    Action succeeded
    4. nv action upload system config files <new_file_name> <remote_url>
    5. Action succeeded
    6. compare the file in target and the config file
    :param engines:
    :return:
    """
    logger.info('ADD TEST')


@pytest.mark.general
@pytest.mark.simx
def test_patch_replace_delete(engines):
    """

    :param engines:
    :return:
    """
    logger.info('ADD TEST')


@pytest.mark.general
@pytest.mark.simx
def test_config_bad_flow(engines):
    """

    :param engines:
    :return:
    """
    logger.info('ADD TEST')
