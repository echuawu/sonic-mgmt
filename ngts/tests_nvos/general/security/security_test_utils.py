import time
import logging

from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.system.System import System
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


def validate_users_authorization_and_role(engines, users):
    """
    @summary:
        in this function we want to iterate on all users given and validate that access to switch
        and role as expected.
        We will restore the engine to default credentials afterwards
    """
    try:
        for user_info in users:
            connect_to_switch_and_validate_role(engines, user_info['username'], user_info['password'],
                                                user_info['role'])
    except Exception as err:
        logging.info("Got an exception while connection to switch and validating role")
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
