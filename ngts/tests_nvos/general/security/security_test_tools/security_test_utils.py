import time
import logging

from typing import List

from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.AuthVerifier import *
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthConsts, AaaConsts
from ngts.tools.test_utils import allure_utils as allure
from ngts.tools.test_utils.nvos_general_utils import loganalyzer_ignore


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


def verify_user_auth(engines, topology_obj, user: UserInfo, expect_login_success: bool = True,
                     verify_authorization: bool = True, skip_auth_mediums: List[str] = None):
    """
    @summary: Verify authentication and authorization for the given user.
        Authentication will be verified via all possible mediums - SSH, OpenApi, rcon, SCP.
    @param engines: test engines object
    @param topology_obj: test topology object
    @param user: Details of the given user.
        User is a dictionary in the format:
        {
            username: str,
            password: str,
            role: admin/monitor (str)
        }
    @param expect_login_success: boolean flag, whether login expected to succeed (True) or fail (False).
        Default is True.
    @param verify_authorization: Whether to verify also authorization or not (authentication test only)
    @param skip_auth_mediums: auth mediums to skip from the test (optional)
    """
    with loganalyzer_ignore(False and (not expect_login_success)):
        with allure.step(f'Verify auth: User: {user.username} , Password: {user.password} , Role: {user.role} , '
                         f'Expect login success: {expect_login_success}'):
            wait_time_before_auth_test = 3
            logging.info(f'Wait {wait_time_before_auth_test} seconds')
            time.sleep(wait_time_before_auth_test)

            # for ssh, openapi, rcon: test authentication, and then verify role by running show, set, unset commands
            user_is_admin = user.role == AaaConsts.ADMIN
            for medium in AuthMedium.ALL_MEDIUMS:
                if skip_auth_mediums and medium in skip_auth_mediums:
                    continue

                with allure.step(f'Verify auth with medium: {medium}'):
                    medium_obj = AUTH_VERIFIERS[medium](user.username, user.password, engines, topology_obj)

                    with allure.step(f'Verify authentication. Expect login success: {expect_login_success}'):
                        medium_obj.verify_authentication(expect_login_success)

                    if verify_authorization and expect_login_success:
                        with allure.step(f'Verify authorization. Role: {user.role}'):
                            medium_obj.verify_authorization(user_is_admin=user_is_admin)
        logging.info('\n')


def verify_users_auth(engines, topology_obj, users: List[UserInfo], expect_login_success: List[bool] = None,
                      verify_authorization: bool = True, skip_auth_mediums: List[str] = None):
    """
    @summary: Verify authentication and authorization for the given users.
        Authentication will be verified via all possible mediums - SSH, OpenApi, rcon, SCP.
    @param engines: test engines object
    @param topology_obj: test topology object
    @param users: list of users to verify.
        User is a dictionary in the format:
        {
            username: str,
            password: str,
            role: admin/monitor (str)
        }
    @param expect_login_success: list of boolean flags, whether login expected to succeed (True) or fail (False).
        Default is True for all users.
    @param verify_authorization: Whether to verify also authorization or not (authentication test only)
    @param skip_auth_mediums: auth mediums to skip from the test (optional)
    """
    expect_login_success = [True] * len(users) if not expect_login_success else expect_login_success

    for i, user in enumerate(users):
        verify_user_auth(engines, topology_obj, user, expect_login_success[i], verify_authorization, skip_auth_mediums)


def validate_users_authorization_and_role(engines, users, login_should_succeed=True, check_nslcd_if_login_failed=False):
    """
    @summary:
        in this function we want to iterate on all users given and validate that access to switch
        and role as expected.
        We will restore the engine to default credentials afterwards
    """
    for user in users:
        username = user[AaaConsts.USERNAME]
        password = user[AaaConsts.PASSWORD]
        role = user[AaaConsts.ROLE]
        with allure.step(f"Check user: {username} , password: {password} , role: {role}"):
            with allure.step(f'Try login - expect: {"success" if login_should_succeed else "fail"}'):
                try:
                    new_engine = ProxySshEngine(device_type=engines.dut.device_type, ip=engines.dut.ip,
                                                username=username, password=password)
                    new_engine.run_cmd('')
                    # engines.dut.update_credentials(username=username, password=password)
                except Exception:
                    logging.info("Got an exception - can not connect to switch")
                    if check_nslcd_if_login_failed:
                        check_nslcd_service(engines)
                    assert not login_should_succeed, 'Login fail, expect success'
                    continue
                assert login_should_succeed, 'Login success, expect fail'

            SLEEP_BEFORE_EXECUTING_CMDS = 1
            with allure.step("Sleeping {} secs before executing commands".format(SLEEP_BEFORE_EXECUTING_CMDS)):
                time.sleep(SLEEP_BEFORE_EXECUTING_CMDS)
                if role == AaaConsts.ADMIN:
                    with allure.step('FOR DEBUG - after login, run: sudo stat /var/log/audit.log'):
                        new_engine.run_cmd('sudo stat /var/log/audit.log')

            with allure.step("Running show command - expect: success"):
                system = System(None)
                try:
                    system.version.show(dut_engine=new_engine)
                except Exception as ex:
                    logging.info("Got an exception - can not run show command")
                    raise ex

            is_admin = role == SystemConsts.DEFAULT_USER_ADMIN

            with allure.step(f'Run set command - expect: {"success" if is_admin else "fail"}'):
                system.message.set(op_param_name=SystemConsts.PRE_LOGIN_MESSAGE, op_param_value='"NVOS TESTS"',
                                   apply=is_admin, dut_engine=new_engine).verify_result(should_succeed=is_admin)

            with allure.step(f'Run unset command - expect: {"success" if is_admin else "fail"}'):
                system.message.unset(op_param=SystemConsts.PRE_LOGIN_MESSAGE, apply=is_admin,
                                     dut_engine=new_engine).verify_result(should_succeed=is_admin)

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


def find_server_admin_user(server_info):
    admin_user = None
    for user in server_info[AuthConsts.USERS]:
        if user[AaaConsts.ROLE] == AaaConsts.ADMIN:
            admin_user = user
    assert admin_user, "Couldn't find admin user, check server configuration"
    return admin_user


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


def configure_authentication(engines, devices, order=None, failthrough=None, fallback=None, apply=False,
                             dut_engine=None):
    """
    @summary:
        Configure different authentication settings as given
    """
    if order == failthrough == fallback is None:
        return

    dut_engine = engines.dut if not dut_engine else dut_engine

    with allure.step('Configure authentication settings'):
        auth_obj = System().aaa.authentication
        if order:
            logging.info(f'Set authentication order: {order}')
            order = ','.join(order)
            auth_obj.set(AuthConsts.ORDER, order, dut_engine=dut_engine).verify_result()
        if failthrough:
            logging.info(f'Set authentication failthrough: {failthrough}')
            auth_obj.set(AuthConsts.FAILTHROUGH, failthrough, dut_engine=dut_engine).verify_result()
        # if fallback:
        #     logging.info(f'Set authentication fallback: {fallback}')
        #     auth_obj.set(AuthConsts.FALLBACK, fallback).verify_result()

    if apply:
        with allure.step('Apply settings'):
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, dut_engine,
                                            True)

        if order:
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


def set_local_users(engines, users, apply=False):
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
            if isinstance(user, UserInfo):
                username = user.username
                password = user.password
                role = user.role
            else:
                username = user[AaaConsts.USERNAME]
                password = user[AaaConsts.PASSWORD]
                role = user[AaaConsts.ROLE]
            with allure.step(f'Set user "{username}" with role: {role}'):
                user_obj = System(username=username).aaa.user
                logging.info(f'Set user: {username} , password: {password}')
                user_obj.set(AaaConsts.PASSWORD, password).verify_result()
                logging.info(f'Set user: {username} , role: {role}')
                user_obj.set(AaaConsts.ROLE, role).verify_result()

    if apply:
        with allure.step('Apply changes together'):
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut,
                                            True)


def configure_resource(engines, resource_obj: BaseComponent, conf, apply=False, verify_apply=True, dut_engine=None):
    """
    @summary: Configure resource according to the given desired configuration
        * Configuration example:
            if we want:
            ldap
                bind-dn = abc
                auth-port = 123
            then configuration dictionary should be:
            {
                bind-dn: abc,
                auth-port: 123
            }
    @param engines: engines object
    @param resource_obj: resource object
    @param conf: the desired configuration (dictionary)
    @param apply: whether to apply the changes or not
    @param verify_apply: whether to verify the apply or not
    @param dut_engine: engine to run the set commands on (optional)
    """
    if not conf:
        return

    with allure.step(f'Set configuration for resource: {resource_obj.get_resource_path()}'):
        logging.info(f'Given configuration to set:\n{conf}')

        with allure.step('Set fields'):
            for key, value in conf.items():
                logging.info(f'Set field "{key}" to value "{value}"')
                value = int(value) if isinstance(value, int) or isinstance(value, str) and value.isnumeric() else value
                if not dut_engine:
                    resource_obj.set(key, value, apply=False).verify_result()
                else:
                    resource_obj.set(key, value, apply=False, dut_engine=dut_engine).verify_result()

        if apply:
            with allure.step('Apply changes'):
                if not dut_engine:
                    res = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                          engines.dut, True)
                else:
                    res = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                          dut_engine, True)
                if verify_apply:
                    res.verify_result()


def check_ldap_user_with_getent_passwd(engine: ProxySshEngine, username: str, user_should_exist: bool):
    with allure.step('Get getent passwd output'):
        output = engine.run_cmd('getent passwd | grep ldap')
    with allure.step(f'Verify "{username}" does not exist'):
        assert (username in output) == user_should_exist, \
            f'username "{username}" unexpectedly {"does not " if not user_should_exist else ""}exist ' \
            f'in getent passwd output\ngetent passwd output: {output}\n'


def check_ldap_user_groups_with_id(engine: ProxySshEngine, username: str, groupname: str, group_should_exist: bool):
    with allure.step('Get id output'):
        output = engine.run_cmd(f'id {username}')
    with allure.step(f'Verify "{groupname}" does not exist'):
        assert (groupname in output) == group_should_exist, \
            f'groupname "{groupname}" unexpectedly {"does not " if not group_should_exist else ""}exist ' \
            f'in id {username} output\nid {username} output: {output}\n'
