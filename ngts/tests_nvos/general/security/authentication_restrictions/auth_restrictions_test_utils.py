import sys
import time
from retry import retry
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tools.test_utils import allure_utils as allure
import logging
import pexpect


def configure_resource(engines, resource_obj: BaseComponent, configuration={}):
    """
    @summary: Configure fields within the given resource
    @param engines: engines object
    @param resource_obj: A resource object (from class inherits from BaseComponent)
    @param configuration: The desired configuration for the resource.
        * Given as dictionary of: { field: value } format.
    """
    with allure.step(f'Configure resource: {resource_obj.get_resource_path()}'):
        for field, val in configuration.items():
            with allure.step(f'Set field "{field}" with value "{val}"'):
                resource_obj.set(field, val).verify_result()

        with allure.step('Apply configuration'):
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut,
                                            True).verify_result()


class Authenticator:
    def __init__(self, username, password, ip, port=22):
        logging.info(f'Start user authenticator with:\nUser: {username}\nPassword: {password}\nIp: {ip}\nPort: {port}')
        self.username = username
        self.password = password
        self.ip = ip
        self.port = port
        self.session_process = None
        self.attempt_timestamp = None
        self.num_sessions = 0
        self.spawn_cmd = '/bin/sh'  # command to just spawn with shell terminal

    def log(self, msg):
        logging.info(f'USER LOG [{self.username}] {msg}')

    def __del__(self):
        self.log('Delete authenticator object')
        self.close_session()

    def start_session(self):
        if self.session_process:
            self.close_session()

        self.log(f'Start terminal session with: {self.spawn_cmd}')
        self.session_process = pexpect.spawn(self.spawn_cmd, env={'TERM': 'dumb'})
        self.session_process.delaybeforesend = DefaultConnectionValues.PEXPECT_DELAYBEFORESEND
        self.session_process.delayafterclose = DefaultConnectionValues.PEXPECT_DELAYAFTERCLOSE
        self.log('\n')

        self.send_cmd('\r', DefaultConnectionValues.DEFAULT_PROMPTS)
        self.clear_leftover_prints()

    def clear_leftover_prints(self):
        assert self.session_process is not None, 'Session process is not started'
        self.log('Clear leftover prints to expect')
        self.session_process.expect('.*')
        self.log('\n')

    def send_cmd(self, cmd, expected_msg, timeout=RestrictionsConsts.MAX_TIMEOUT, send_line=True):
        assert self.session_process, 'There is no session spawned process. Should start one before send command'

        time.sleep(RestrictionsConsts.PEXPECT_DELAY)

        if send_line:
            self.log(f'Send line: {cmd}')
            self.session_process.sendline(cmd)
        else:
            self.log(f'Send: {cmd}')
            self.session_process.send(cmd)

        send_timestamp = time.time()
        self.log(f'Sending time: {send_timestamp}')

        time.sleep(RestrictionsConsts.PEXPECT_DELAY)

        self.log(f'Expect: {expected_msg}')
        respond_index = self.session_process.expect(expected_msg,
                                                    timeout=timeout * 1.75 if timeout > 0 else RestrictionsConsts.MAX_TIMEOUT)

        output = self.session_process.before.decode('utf-8', errors='ignore') + self.session_process.after.decode(
            'utf-8', errors='ignore')
        self.log(f'Respond index: {respond_index} ; Output:\n{output}')

        self.log('\n')

        self.clear_leftover_prints()

        return send_timestamp, respond_index, output

    def close_session(self):
        if self.session_process:
            self.log('Close session process')
            self.session_process.close()
            self.session_process = None
            self.log('\n')

    def print_expect_results(self, response_index=None):
        if response_index is not None:
            self.log(f'Response index: {response_index}')
        self.log(f'Matched string:\n{self.session_process.match.group(0).decode("utf-8")}')
        # self.log(f'Before:\n{self.session_process.before.decode("utf-8")}')
        # self.log(f'After:\n{self.session_process.after.decode("utf-8")}')
        self.log(f'Entire prompt (before and after matched string):\n'
                 f'{(self.session_process.before + self.session_process.after).decode("utf-8")}')

    def clear_buffer(self):
        self.log('Clear child process buffer')
        if self.session_process is not None:
            self.session_process.expect_exact(self.session_process.buffer)
            self.session_process.buffer = b''
            self.session_process.before = b''
            self.session_process.after = b''


class SshAuthenticator(Authenticator):
    def __init__(self, username, password, ip, port=22):
        super().__init__(username, password, ip, port)
        self.ssn_command = f'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout={RestrictionsConsts.MAX_TIMEOUT} {self.username}@{self.ip}'
        self.ssh_session_already_started = False
        self.start_session()

    def start_ssn(self):
        if not self.ssh_session_already_started:
            self.log('Start SSH session with ssn command')
            self.log('\n')
            self.ssh_session_already_started = True
            return self.send_cmd(self.ssn_command, 'password:')

    def close_ssh_login_session(self):
        assert self.session_process, 'There is no spawned session'
        if self.ssh_session_already_started:
            self.log('Close SSH login session - Ctrl+C')
            self.session_process.sendintr()
            self.ssh_session_already_started = False
            self.log('\n')

    def logout_from_ssh(self):
        assert self.session_process, 'There is no spawned session'
        if self.ssh_session_already_started:
            self.log('Close SSH connection - logout')
            self.send_cmd('logout', '.*')
            self.ssh_session_already_started = False
            self.log('\n')

    def auth_attempt(self, password_to_send, timeout=RestrictionsConsts.MAX_TIMEOUT):
        if not self.ssh_session_already_started:
            self.start_ssn()

        expected_msg = ['.+@.+:.+\\$', 'password:',
                        'Permission denied \\(publickey,password\\)'] + DefaultConnectionValues.DEFAULT_PROMPTS
        self.log(f'Make auth attempt with password: {password_to_send} | Then, expect: {expected_msg}')
        send_timestamp, respond_index, output = self.send_cmd(password_to_send, expected_msg, timeout)

        if respond_index == 0:
            self.log('Login success')
            login_succeeded = True
            self.logout_from_ssh()
        elif respond_index == 1:
            self.log('Login failed. can try again')
            login_succeeded = False
        else:
            self.log('Login failed and SSH session killed')
            login_succeeded = False
            self.ssh_session_already_started = False

        self.log('\n')
        return login_succeeded, send_timestamp

    def attempt_login_success(self, timeout=RestrictionsConsts.MAX_TIMEOUT):
        self.close_ssh_login_session()  # make the attempt in new ssh session
        self.log(f'Make auth attempt with good credentials')
        return self.auth_attempt(self.password, timeout)

    def attempt_login_failure(self, timeout=RestrictionsConsts.MAX_TIMEOUT):
        self.log(f'Make auth attempt with bad credentials')
        return self.auth_attempt(RestrictionsConsts.BAD_PASSWORD, timeout)


class OpenapiAuthenticator(Authenticator):
    def __init__(self, username, password, ip, port=22):
        super().__init__(username, password, ip, port)
        self.start_session()
        # self.send_cmd('\r', DefaultConnectionValues.DEFAULT_PROMPTS)

    def auth_attempt(self, password_to_send, timeout=RestrictionsConsts.MAX_TIMEOUT):
        self.send_cmd('\r', DefaultConnectionValues.DEFAULT_PROMPTS)

        openapi_request = f"curl -k --user {self.username}:{password_to_send} " \
                          f"--request GET 'https://{self.ip}/nvue_v1/system/version'"
        expected_msg = ['}', '</html>'] + DefaultConnectionValues.DEFAULT_PROMPTS
        self.log(f'Make auth attempt with password: {password_to_send} | Then, expect: {expected_msg}')
        send_timestamp, respond_index, output = self.send_cmd(openapi_request, expected_msg, timeout)

        if respond_index == 0:
            self.log('Auth success')
            login_succeeded = True
        else:
            self.log('Login failed.')
            login_succeeded = False

        self.log('\n')
        return login_succeeded, send_timestamp, output

    def attempt_login_success(self, timeout=RestrictionsConsts.MAX_TIMEOUT):
        self.log(f'Make auth attempt with good credentials')
        return self.auth_attempt(self.password, timeout)

    def attempt_login_failure(self, timeout=RestrictionsConsts.MAX_TIMEOUT):
        self.log(f'Make auth attempt with bad credentials')
        return self.auth_attempt(RestrictionsConsts.BAD_PASSWORD, timeout)
