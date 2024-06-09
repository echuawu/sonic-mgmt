import logging
import random
import time

import pexpect
import pytest

from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_tools.acl.acl import Acl
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.conftest import create_ssh_login_engine, \
    ssh_to_device_and_retrieve_raw_login_ssh_notification
from ngts.tests_nvos.general.security.test_login_ssh_notification.constants import LoginSSHNotificationConsts
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger(__name__)


@pytest.fixture()
def rand_ssh_port():
    all_ports = [port for port in range(SshConfigConsts.MIN_LOGIN_PORT, SshConfigConsts.MAX_LOGIN_PORT)]
    all_ports.remove(SshConfigConsts.DEFAULT_PORT)
    new_login_port = random.choice(all_ports)
    acl = Acl()
    with allure.step(f'add ACL rule to permit ssh through port {new_login_port}'):
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT'].rule.rule_id['9'].action.set('permit')
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT_IPV6'].rule.rule_id['9'].action.set('permit')
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT'].rule.rule_id['9'].match.ip.set('protocol', 'tcp')
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT_IPV6'].rule.rule_id['9'].match.ip.set('protocol', 'tcp')
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT'].rule.rule_id['9'].match.ip.tcp.set('dest-port', f'{new_login_port}')
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT_IPV6'].rule.rule_id['9'] \
            .match.ip.tcp.set('dest-port', f'{new_login_port}', apply=True, ask_for_confirmation=True)
    yield new_login_port
    with allure.step('remove test ACL rule'):
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT'].rule.rule_id['9'].unset()
        acl.acl_id['ACL_MGMT_INBOUND_CP_DEFAULT_IPV6'].rule.rule_id['9'].unset(apply=True, ask_for_confirmation=True)


@pytest.mark.checklist
@pytest.mark.ssh_config
def test_ssh_config_good_flow(engines, devices, rand_ssh_port):
    """
    @summary: we want to test the good flow of ssh-server config.
    we want to validate the following parameters: authentication-retries,
    login-timeout, ports. these parameters are used in ssh connection
    """
    system = System()

    with allure.step("Validating login authentication-retries"):
        auth_retries = random.randint(SshConfigConsts.MIN_AUTH_RETRIES, SshConfigConsts.MAX_AUTH_RETRIES)
        with allure.step("Configuring {} as number of authentication-retries".format(auth_retries)):
            system.ssh_server.set(SshConfigConsts.AUTH_RETRIES, auth_retries,
                                  apply=True, ask_for_confirmation=True).verify_result()
        with allure.step("Failing to Connect {} times to get logged out of session".format(auth_retries)):
            try:
                connection = create_ssh_login_engine(engines.dut.ip,
                                                     username=DefaultConnectionValues.ADMIN,
                                                     port=SshConfigConsts.DEFAULT_PORT,
                                                     custom_ssh_options=SshConfigConsts.SSH_CONFIG_CONNECTION_OPTIONS)
                for iteration in range(auth_retries):
                    random_password = RandomizationTool.get_random_string(
                        random.randint(LoginSSHNotificationConsts.PASSWORD_MIN_LEN,
                                       LoginSSHNotificationConsts.PASSWORD_MAX_LEN))
                    logger.info(
                        "Iteration {} - connecting using random password: {} for"
                        " user: {}".format(iteration, random_password, DefaultConnectionValues.ADMIN))
                    connection.expect(DefaultConnectionValues.PASSWORD_REGEX)
                    connection.sendline(random_password)

                with allure.step("Expecting to log out of authentication process and return to terminal"):
                    connection.expect('Too many authentication failures')
            finally:
                connection.close()

    with allure.step("Validating ssh login ports"):
        with allure.step("validating ssh login ports, in range [{}-{}]".format(SshConfigConsts.MIN_LOGIN_PORT,
                                                                               SshConfigConsts.MAX_LOGIN_PORT)):
            with allure.step("Configuring {} as new login port".format(rand_ssh_port)):
                system.ssh_server.set(SshConfigConsts.PORTS,
                                      '{},{}'.format(SshConfigConsts.DEFAULT_PORT, rand_ssh_port),
                                      apply=True, ask_for_confirmation=True).verify_result()
            with allure.step(f'check ssh login through port {rand_ssh_port}'):
                ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip,
                                                                      username=devices.dut.default_username,
                                                                      password=devices.dut.default_password,
                                                                      port=rand_ssh_port)

    with allure.step("Validating login timeout"):
        login_timeout = random.randint(SshConfigConsts.MIN_LOGIN_TIMEOUT, SshConfigConsts.MAX_LOGIN_TIMEOUT)
        with allure.step("Configuring {} as login timeout".format(login_timeout)):
            system.ssh_server.set(SshConfigConsts.LOGIN_TIMEOUT,
                                  login_timeout, apply=True, ask_for_confirmation=True).verify_result()
        try:
            connection = create_ssh_login_engine(dut_ip=engines.dut.ip,
                                                 username=DefaultConnectionValues.ADMIN,
                                                 custom_ssh_options=SshConfigConsts.SSH_CONFIG_CONNECTION_OPTIONS)
            time.sleep(login_timeout + 0.1)  # 0.1 represents a small delta after timeout
            connection.sendline(devices.dut.default_password)
            connection.expect(["Connection\\s+closed", "connection\\s+closed", pexpect.EOF])
        finally:
            connection.close()
