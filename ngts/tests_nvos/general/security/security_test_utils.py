import time
import logging

from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.constants import AuthConsts, AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.switch_authenticators import SshAuthenticator
from ngts.tools.test_utils import allure_utils as allure


def connect_to_switch_and_validate_role(engines, username, password, role=SystemConsts.ROLE_VIEWER):
    """
    @summary:
        in this helper function, we will connect to switch using username, password & port
        and validate user role configurations
    """
    with allure.step("Using username: {}, role: {}".format(username, role)):
        new_engine = ProxySshEngine(device_type=engines.dut.device_type, ip=engines.dut.ip, username=username,
                                    password=password)
        # engines.dut.update_credentials(username=username, password=password)

    if role == AaaConsts.ADMIN:
        with allure.step('FOR DEBUG - after login, run: sudo stat /var/log/audit.log'):
            new_engine.run_cmd('sudo stat /var/log/audit.log')

    SLEEP_BEFORE_EXECUTING_CMDS = 5
    with allure.step("Sleeping {} secs before executing commands".format(SLEEP_BEFORE_EXECUTING_CMDS)):
        time.sleep(SLEEP_BEFORE_EXECUTING_CMDS)

    system = System(None)
    SHOW_SYSTEM_VERSION_CMD = 'nv show system version'
    with allure.step("Running command: \'{}\'".format(SHOW_SYSTEM_VERSION_CMD)):
        system.version.show(dut_engine=new_engine)

    with allure.step("Validating role permissions are as expected"):
        if role == SystemConsts.DEFAULT_USER_ADMIN:
            logging.info("User has admin permissions and can set configurations")
            system.message.set("NVOS TESTS", new_engine, field_name='pre-login').verify_result(should_succeed=True)
            system.message.unset(new_engine, field_name='pre-login').verify_result(should_succeed=True)
        else:
            logging.info("User has monitor permissions and cannot set configurations")
            system.message.set("NVOS TESTS", new_engine, field_name='pre-login').verify_result(
                should_succeed=False)


def check_nslcd_service(engines):
    """
    @summary: Check the status of nslcd service, and restart it if needed (for next test cases):
    """
    exit_cmd = 'q'
    status_cmd = 'sudo service nslcd status'
    restart_cmd = 'sudo service nslcd restart'

    with allure.step('Check nslcd service status'):
        output = engines.dut.run_cmd_after_cmd([status_cmd, exit_cmd])
        if 'Active: failed' in output:
            logging.info('Service nslcd failed')
            with allure.step('Restart nslcd service'):
                engines.dut.run_cmd(restart_cmd)
            with allure.step('Check nslcd service status again'):
                output = engines.dut.run_cmd([status_cmd, exit_cmd])
                logging.info(f'Service nslcd is active: {"Active: active (running)" in output}')


def validate_users_authorization_and_role(engines, users, login_should_succeed=True, check_nslcd_if_login_failed=False):
    """
    @summary:
        in this function we want to iterate on all users given and validate that access to switch
        and role as expected.
        We will restore the engine to default credentials afterwards
    """
    should_check_nslcd_service = False
    try:
        for user_info in users:
            logging.info(f'Check login and role for user {user_info["username"]}')
            connect_to_switch_and_validate_role(engines, user_info['username'], user_info['password'],
                                                user_info['role'])
    except Exception as err:
        logging.info("Got an exception while connection to switch and validating role")
        if login_should_succeed:
            logging.info('Failed due to authentication or permission error')
            should_check_nslcd_service = check_nslcd_if_login_failed
            raise err
    finally:
        if should_check_nslcd_service:
            check_nslcd_service(engines)
        # restore_original_engine_credentials(engines)
        logging.info('Finally')

    # for user_info in users:
    #     username = user_info[AaaConsts.USERNAME]
    #     password = user_info[AaaConsts.PASSWORD]
    #     role = user_info[AaaConsts.ROLE]
    #
    #     with allure.step(f'Verify authentication {username}'):
    #         authenticator = SshAuthenticator(username, password, engines.dut.ip)
    #         login_succeeded, _ = authenticator.attempt_login_success(logout_if_succeeded=False)
    #         assert login_succeeded == login_should_succeed, \
    #             f'User {username} could {"" if login_succeeded else "not "}login'
    #
    #     if login_should_succeed:
    #         with allure.step(f'Verify role of {username}: {role}'):
    #             with allure.step(f'Verify user {username} can make show command'):
    #                 _, _, output = authenticator.send_cmd(AuthConsts.SHOW_COMMAND, AuthConsts.SWITCH_PROMPT_PATTERN)
    #                 assert AuthConsts.PERMISSION_ERROR not in output, \
    #                     f'User {username} do not have permission to run "{AuthConsts.SHOW_COMMAND}"'
    #
    #             can_set = role == AaaConsts.ADMIN
    #             with allure.step(f'Verify user {username} can {"" if can_set else "not "}make set command'):
    #                 _, _, output = authenticator.send_cmd(AuthConsts.SET_COMMAND, AuthConsts.SWITCH_PROMPT_PATTERN)
    #                 cond = AuthConsts.PERMISSION_ERROR not in output if can_set else AuthConsts.PERMISSION_ERROR in output
    #                 assert cond, f'User {username} do not have permission to run "{AuthConsts.SET_COMMAND}"'
    #
    #     del authenticator


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
        # if fallback:
        #     logging.info(f'Set authentication fallback: {fallback}')
        #     auth_obj.set(AuthConsts.FALLBACK, fallback).verify_result()

    with allure.step('Apply settings'):
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)

    with allure.step('Validate that services and dockers are up'):
        DutUtilsTool.wait_for_nvos_to_become_functional(engines.dut)


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


def mutual_users(users_a, users_b):
    """
    @summary: Get the mutual of the two given user lists.
    @param users_a: users list A
    @param users_b: users list B
    @return: list of the mutual users.
    """
    with allure.step('Get mutual users list'):
        a_usernames = [user[AaaConsts.USERNAME] for user in users_a]
        b_usernames = [user[AaaConsts.USERNAME] for user in users_b]
        logging.info(f'A: {a_usernames}\nB: {b_usernames}')

        mutual_usernames = list(set(a_usernames).intersection(set(b_usernames)))
        logging.info(f'Mutual users: {mutual_usernames}')

        return [user for user in users_a if user[AaaConsts.USERNAME] in mutual_usernames]


def set_local_users(engines, users):
    """
    @summary: Set the given users on local.
        * users should be a list of users.
        * a user should be a dictionary in the following format:
            {
                username: str ,
                password: str ,
                role: <admin, monitor>
            }
    @param engines: engines object
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
                user_obj.set(AaaConsts.PASSWORD, password).verify_result()
                logging.info(f'Set user: {username} , role: {role}')
                user_obj.set(AaaConsts.ROLE, role).verify_result()

    with allure.step('Apply changes together'):
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)
