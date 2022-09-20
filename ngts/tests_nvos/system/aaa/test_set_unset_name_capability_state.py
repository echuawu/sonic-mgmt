import logging
import pytest
import allure
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()


@pytest.mark.system
def test_set_unset_full_name(engines):
    """

        Test flow:
            1. nv set system aaa user admin full-name <new_full_name>
            2. nv set system aaa user monitor full-name <new_full_name>
            3. nv show system aaa user
            4. verify full names
            5. nv unset system aaa user admin full-name
            6. nv unset system aaa user monitor full-name
            7. nv show system aaa user
            8. verify default full names
            9. try to connect as admin - should succeed
            10. try to connect as monitor - should succeed
    """
    system = System(None)
    new_full_name = 'TESTING'
    system.aaa.user.set(SystemConsts.USER_FULL_NAME, new_full_name).verify_result()
    system.aaa.user.set_username(SystemConsts.DEFAULT_USER_MONITOR)
    system.aaa.user.set(SystemConsts.USER_FULL_NAME, new_full_name).verify_result()
    NvueGeneralCli.apply_config(engines.dut)
    verify_full_name(system, SystemConsts.DEFAULT_USER_ADMIN, SystemConsts.USER_FULL_NAME, new_full_name)
    verify_full_name(system, SystemConsts.DEFAULT_USER_MONITOR, SystemConsts.USER_FULL_NAME, new_full_name)
    ConnectionTool.create_ssh_conn(engines.dut.ip, SystemConsts.DEFAULT_USER_ADMIN, engines.dut.password).verify_result()
    ConnectionTool.create_ssh_conn(engines.dut.ip, SystemConsts.DEFAULT_USER_MONITOR, engines.dut.password).verify_result()


@pytest.mark.system
def test_set_unset_full_name_newuser(engines):
    """

        Test flow:
            1. create new user (configurator)
            2. create new user (viewer)
            3. nv set system aaa user <new_user_configurator> full-name <new_full_name>
            4. nv set system aaa user <new_user_viewer> full-name <new_full_name>
            5. nv show system aaa user
            6. verify full name
            7. nv unset system aaa user <new_user_configurator> full-name
            8. nv unset system aaa user <new_user_viewer> full-name
            9. nv show system aaa user
            10. verify full name is '' for both
            11. try to connect as <new_user_configurator>
            12. try to connect as <new_user_viewer>
    """
    system = System(None)
    new_full_name = 'TESTING'
    viewer_name, viewer_password = system.create_new_user(engine=engines.dut, role=SystemConsts.ROLE_VIEWER)
    configurator_name, configurator_password = system.create_new_user(engine=engines.dut)
    system.aaa.user.set_username(configurator_name)
    system.aaa.user.set(SystemConsts.USER_FULL_NAME, new_full_name).verify_result()
    system.aaa.user.set_username(viewer_name)
    system.aaa.user.set(SystemConsts.USER_FULL_NAME, new_full_name).verify_result()
    NvueGeneralCli.apply_config(engines.dut)
    verify_full_name(system, viewer_name, SystemConsts.USER_FULL_NAME, new_full_name)
    verify_full_name(system, configurator_name, SystemConsts.USER_FULL_NAME, new_full_name)
    ConnectionTool.create_ssh_conn(engines.dut.ip, viewer_name, viewer_password).verify_result()
    ConnectionTool.create_ssh_conn(engines.dut.ip, configurator_name, configurator_password).verify_result()


@pytest.mark.system
def test_set_unset_state(engines):
    """

        Test flow:
            1. create new user (configurator)
            2. create new user (viewer)
            3. nv set system aaa user <new_user_configurator> state disable
            4. nv set system aaa user <new_user_viewer> state disable
            5. nv show system aaa user
            6. verify roles
            7. nv unset system aaa user <new_user_configurator> role
            8. nv unset system aaa user <new_user_viewer> role
            9. nv show system aaa user
            10. verify role is configurator for both
            11. try to connect as <new_user_configurator>
            12. try to connect as <new_user_viewer>

    """
    system = System(None)
    viewer_name, viewer_password = system.create_new_user(engine=engines.dut, role=SystemConsts.ROLE_VIEWER)
    configurator_name, configurator_password = system.create_new_user(engine=engines.dut)
    system.aaa.user.set_username(configurator_name)
    system.aaa.user.set(SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED).verify_result()
    system.aaa.user.set_username(viewer_name)
    system.aaa.user.set(SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED).verify_result()
    NvueGeneralCli.apply_config(engines.dut)
    verify_full_name(system, viewer_name, SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED)
    verify_full_name(system, configurator_name, SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED)


@pytest.mark.system
def test_set_unset_capability(engines):
    """

        Test flow:
            1. create new user (configurator)
            2. create new user (viewer)
            3. nv set system aaa user <new_user_configurator> role viewer
            4. nv set system aaa user <new_user_viewer> role configurator
            5. nv show system aaa user
            6. verify roles
            7. nv unset system aaa user <new_user_configurator> role
            8. nv unset system aaa user <new_user_viewer> role
            9. nv show system aaa user
            10. verify role is configurator for both
            11. try to connect as <new_user_configurator>
            12. try to connect as <new_user_viewer>

    """
    system = System(None)
    viewer_name, viewer_password = system.create_new_user(engine=engines.dut, role=SystemConsts.ROLE_VIEWER)
    configurator_name, configurator_password = system.create_new_user(engine=engines.dut)
    system.aaa.user.set_username(configurator_name)
    system.aaa.user.set(SystemConsts.USER_ROLE, SystemConsts.ROLE_VIEWER).verify_result()
    system.aaa.user.set_username(viewer_name)
    system.aaa.user.set(SystemConsts.USER_ROLE, SystemConsts.ROLE_CONFIGURATOR).verify_result()
    NvueGeneralCli.apply_config(engines.dut)
    verify_full_name(system, viewer_name, SystemConsts.USER_ROLE, SystemConsts.ROLE_CONFIGURATOR)
    verify_full_name(system, configurator_name, SystemConsts.USER_ROLE, SystemConsts.ROLE_VIEWER)


def verify_full_name(system, username, label, new_fullname):
    with allure.step('verify user {username} fullname value'.format(username=username)):
        system.aaa.user.set_username(username)
        output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).verify_result()
        assert output[label] == new_fullname, "the new user {username} full name is {fullname} not {new_fullname} as expected".format(username=username, fullname=output[SystemConsts.USER_ADMIN_DEFAULT_FULL_NAME], new_fullname=new_fullname)
