import time
import logging

from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.constants import AuthConsts, AaaConsts
from ngts.tests_nvos.infra.init_flow.init_flow import test_system_dockers, test_system_services
from ngts.tools.test_utils import allure_utils as allure


def connect_to_switch_and_validate_role(engines, username, password, role=SystemConsts.ROLE_VIEWER):
    """
    @summary:
        in this helper function, we will connect to switch using username, password & port
        and validate user role configurations
    """
    with allure.step("Using username: {}, role: {}".format(username, role)):
        engines.dut.update_credentials(username=username, password=password)

    SLEEP_BEFORE_EXECUTING_CMDS = 5
    with allure.step("Sleeping {} secs before executing commands".format(SLEEP_BEFORE_EXECUTING_CMDS)):
        time.sleep(SLEEP_BEFORE_EXECUTING_CMDS)

    system = System(None)
    SHOW_SYSTEM_VERSION_CMD = 'nv show system version'
    with allure.step("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD)):
        system.version.show()

    with allure.step("Validating role permissions are as expected"):
        if role == SystemConsts.DEFAULT_USER_ADMIN:
            logging.info("User has admin permissions and can set configurations")
            system.message.set("NVOS TESTS", engines.dut, field_name='pre-login').verify_result(should_succeed=True)
            system.message.unset(engines.dut, field_name='pre-login').verify_result(should_succeed=True)
        else:
            logging.info("User has monitor permissions and cannot set configurations")
            system.message.set("NVOS TESTS", engines.dut, field_name='pre-login').verify_result(
                should_succeed=False)


def validate_users_authorization_and_role(engines, users, login_should_succeed=True):
    """
    @summary:
        in this function we want to iterate on all users given and validate that access to switch
        and role as expected.
        We will restore the engine to default credentials afterwards
    """
    try:
        for user_info in users:
            logging.info(f'Check login and role for user {user_info["username"]}')
            connect_to_switch_and_validate_role(engines, user_info['username'], user_info['password'],
                                                user_info['role'])
    except Exception as err:
        logging.info("Got an exception while connection to switch and validating role")
        if login_should_succeed:
            logging.info('Failed due to authentication or permission error')
            raise err
    finally:
        restore_original_engine_credentials(engines)


def restore_original_engine_credentials(engines):
    """
    @summary:
        in this fixture we will restore default credentials to dut engine
    """
    logging.info("Restoring default credentials, and logging in to switch")
    engines.dut.update_credentials(username=DefaultConnectionValues.ADMIN,
                                   password=DefaultConnectionValues.DEFAULT_PASSWORD)


def validate_authentication_fail_with_credentials(engines, username, password):
    """
    @summary: in this helper function we want to validate authentication failure while using
    username and password credentials
    """
    with allure.step("Validating failed authentication with new credentials, username: {}".format(username)):
        ConnectionTool.create_ssh_conn(engines.dut.ip, username=username, password=password).verify_result(
            should_succeed=False)


def validate_services_and_dockers_availability(engines, devices):
    """
    @summary: validate all services and dockers are up
    """
    with allure.step("validating all services and dockers are up"):
        devices.dut.verify_dockers(engines.dut).verify_result()
        devices.dut.verify_services(engines.dut).verify_result()


def configure_authentication(engines, devices, order=None, failthrough=None, fallback=None):
    """
    @summary:
        Configure different authentication settings as given
    """
    if order == failthrough == fallback is None:
        return

    with allure.step('Configure authentication settings'):
        auth_obj = System().aaa.authentication
        if order:
            logging.info(f'Set authentication order: {order}')
            order = ','.join(order)
            auth_obj.set(AuthConsts.ORDER, order).verify_result()
        if failthrough:
            logging.info(f'Set authentication failthrough: {failthrough}')
            auth_obj.set(AuthConsts.FAILTHROUGH, failthrough).verify_result()
        if fallback:
            logging.info(f'Set authentication fallback: {fallback}')
            auth_obj.set(AuthConsts.FALLBACK, fallback).verify_result()

    with allure.step('Apply settings'):
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)\
            .verify_result()

    NVUED_SLEEP_FOR_RESTART = 4
    with allure.step("Sleep {} secs for nvued to start the restart".format(NVUED_SLEEP_FOR_RESTART)):
        time.sleep(NVUED_SLEEP_FOR_RESTART)
        NvueGeneralCli.wait_for_nvos_to_become_functional(engines.dut)

    with allure.step('Validate that services and dockers are up'):
        validate_services_and_dockers_availability(engines, devices)


def set_local_users(users):
    """
    @summary: Set the given users on local.
        * users should be a list of users.
        * a user should be a dictionary in the following format:
            {
                username: str ,
                password: str ,
                role: <admin, monitor>
            }
    @param users: users list (list of dictionaries)
    """
    with allure.step(f'Set {len(users)} local users'):
        for user in users:
            username = user[AaaConsts.USERNAME]
            password = user[AaaConsts.PASSWORD]
            role = user[AaaConsts.ROLE]
            with allure.step(f'Set user "{username}" with role: {role}'):
                user_obj = System(username=username).aaa.user
                logging.info(f'Set user: {username} , password: {password}')
                user_obj.set(AaaConsts.PASSWORD, password, apply=True).verify_result()
                logging.info(f'Set user: {username} , role: {role}')
                user_obj.set(AaaConsts.ROLE, role, apply=True).verify_result()


def user_lists_difference(users_a, users_b):
    """
    @summary: Get the difference of the two given user lists.
        * Difference (like sets difference): A - B = all elements of A that are not in B.
        * Here, the elements are users (dictionaries {username: str, password: str, role: <admin, monitor>}),
            then the result will be all users of A, that don't have the same username as any user of B.
    @param users_a: users list A
    @param users_b: users list B
    @return: list of the difference.
    """
    with allure.step('Get users lists difference'):
        a_usernames = [user[AaaConsts.USERNAME] for user in users_a]
        b_usernames = [user[AaaConsts.USERNAME] for user in users_b]
        logging.info(f'A: {a_usernames}\nB: {b_usernames}')

        usernames_diff = list(set(a_usernames) - set(b_usernames))
        logging.info(f'Diff: {usernames_diff}')

        return [user for user in users_a if user[AaaConsts.USERNAME] in usernames_diff]
