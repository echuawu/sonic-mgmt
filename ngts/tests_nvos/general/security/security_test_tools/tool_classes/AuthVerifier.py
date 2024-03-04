import logging
import os
import subprocess

from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from ngts.cli_wrappers.openapi.openapi_command_builder import OpenApiRequest
from ngts.nvos_constants.constants_nvos import ApiType, SystemConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthConsts, AuthMedium
from ngts.tools.test_utils import allure_utils as allure
from infra.tools.linux_tools.linux_tools import LinuxSshEngine, scp_file


class AuthVerifier:
    def __init__(self, username, password, engines, topology_obj):
        self.api = ApiType.NVUE
        logging.info(f'Create proxy ssh engine for user: {username}')
        self.engine = LinuxSshEngine(engines.dut.ip, username, password)

    def change_test_api(self, api=None):
        api = self.api if api is None else api
        logging.info(f'Change test api to: {api}')
        TestToolkit.tested_api = api

    def verify_authentication(self, expect_success=True):
        orig_test_api = TestToolkit.tested_api
        self.change_test_api()
        authentication_success = True
        try:
            self._authenticate(expect_success)
        except Exception as e:
            logging.info(f'Authentication failed\nException:\n{e}')
            authentication_success = False
        finally:
            self.change_test_api(orig_test_api)
            assert expect_success == authentication_success, 'Authentication result not as expected'

    def _authenticate(self, expect_success):
        raise Exception('Method not implemented!')

    def verify_authorization(self, user_is_admin):
        orig_test_api = TestToolkit.tested_api
        self.change_test_api()
        try:
            system = System()
            with allure.step(f'Run show command. Expect success: True'):
                system.version.show(dut_engine=self.engine)
            with allure.step(f'Run set command. Expect success: {user_is_admin}'):
                system.message.set(op_param_name=SystemConsts.PRE_LOGIN_MESSAGE, op_param_value='"NVOS TESTS"',
                                   dut_engine=self.engine).verify_result(should_succeed=user_is_admin)

            with allure.step(f'Run unset command. Expect success: {user_is_admin}'):
                system.message.unset(op_param=SystemConsts.PRE_LOGIN_MESSAGE,
                                     dut_engine=self.engine).verify_result(should_succeed=user_is_admin)
        finally:
            logging.info('Clear global OpenApi changeset and payload')
            OpenApiRequest.clear_changeset_and_payload()
            self.change_test_api(orig_test_api)


class SshAuthVerifier(AuthVerifier):
    def __init__(self, username, password, engines, topology_obj):
        super().__init__(username, password, engines, topology_obj)

    def _authenticate(self, expect_success):
        with allure.step('For SSH - run empty command on engine to trigger authentication'):
            self.engine.run_cmd('')


class OpenApiAuthVerifier(AuthVerifier):
    def __init__(self, username, password, engines, topology_obj):
        super().__init__(username, password, engines, topology_obj)
        self.api = ApiType.OPENAPI

    def _authenticate(self, expect_success):
        with allure.step('For OpenApi - run show command with OpenApi request to verify authentication'):
            System().version.show(dut_engine=self.engine)


class RconAuthVerifier(AuthVerifier):
    def __init__(self, username, password, engines, topology_obj):
        super().__init__(username, password, engines, topology_obj)
        logging.info(f'Create pexpect serial engine for user: {username}')
        self.engine = ConnectionTool.create_serial_engine(topology_obj=topology_obj, ip=engines.dut.ip,
                                                          username=username, password=password)

    def _authenticate(self, expect_success):
        with allure.step('For RCON - start rcon connection and force new login'):
            assert isinstance(self.engine, PexpectSerialEngine), 'engine should be pexpect serial engine'
            self.engine.create_serial_engine(disconnect_existing_login=True)
            self.engine.run_cmd_and_get_output('\r')


class ScpAuthVerifier(AuthVerifier):
    def __init__(self, username, password, engines, topology_obj):
        super().__init__(username, password, engines, topology_obj)

    def _authenticate(self, expect_success):
        with allure.step(f'Download a non-privileged file from the switch. Expect success: {expect_success}'):
            self._verify_scp_download(
                switch_dir=AuthConsts.SWITCH_MONITORS_DIR,
                expect_success=expect_success,
                check_result_in_caller_func=True
            )

    def __verify_scp(self, src_path, dst_path, download_from_remote, expect_success, check_result_in_caller_func=False):
        scp_success = True
        try:
            scp_file(player=self.engine,
                     src_path=src_path,
                     dst_path=dst_path,
                     download_from_remote=download_from_remote)
            logging.info('SCP success')

            if download_from_remote:
                logging.info('Remove downloaded file')
                os.remove(dst_path)
                logging.info('Downloaded file successfully removed')
            else:
                logging.info('Remove uploaded file')
                self.engine.run_cmd(f'rm {dst_path}')
                logging.info('Uploaded file successfully removed')
        except Exception as e:
            logging.info('SCP failed')
            if expect_success:
                logging.info(f'Exception:\n{e}')
            scp_success = False
            if check_result_in_caller_func:
                raise e

        if not check_result_in_caller_func:
            assert scp_success == expect_success, f'SCP success ({scp_success}) status ' \
                                                  f'not as expected ({expect_success})'

    def _verify_scp_download(self, switch_dir, expect_success, switch_filenme='', check_result_in_caller_func=False):
        with allure.step(f'Verify SCP download from the switch. Expect success: {expect_success}'):
            filename = AuthConsts.SWITCH_SCP_DOWNLOAD_TEST_FILE_NAME if not switch_filenme else switch_filenme
            self.__verify_scp(
                src_path=f'{switch_dir}/{filename}',
                dst_path=f'{AuthConsts.SHARED_VERIFICATION_SCP_DIR}/{filename}',
                download_from_remote=True,
                expect_success=expect_success,
                check_result_in_caller_func=check_result_in_caller_func
            )

    def _verify_scp_upload(self, switch_dir, expect_success):
        with allure.step(f'Verify SCP upload to the switch. Expect success: {expect_success}'):
            self.__verify_scp(
                src_path=f'{AuthConsts.SHARED_VERIFICATION_SCP_DIR}/'
                         f'{AuthConsts.SHARED_VERIFICATION_SCP_UPLOAD_TEST_FILE_NAME}',
                dst_path=f'{switch_dir}/{AuthConsts.SHARED_VERIFICATION_SCP_UPLOAD_TEST_FILE_NAME}',
                download_from_remote=False,
                expect_success=expect_success,
            )

    def _verify_scp_download_and_upload(self, switch_dir, expect_success):
        switch_filename = AuthConsts.SWITCH_ROOT_FILE_NAME if switch_dir == AuthConsts.SWITCH_ROOT_DIR else ''
        self._verify_scp_download(switch_dir, expect_success, switch_filenme=switch_filename)
        self._verify_scp_upload(switch_dir, expect_success)

    def verify_authorization(self, user_is_admin):
        with allure.step('Verify SCP with non privileged path on the switch. Expect success: True'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_MONITORS_DIR, expect_success=True)

        with allure.step(f'Verify SCP with admin privileged path on the switch. Expect success: {user_is_admin}'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_ADMINS_DIR, expect_success=user_is_admin)

        with allure.step('Verify SCP with root privileged path on the switch. Expect success: False'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_ROOT_DIR, expect_success=False)


AUTH_VERIFIERS = {
    AuthMedium.SSH: SshAuthVerifier,
    AuthMedium.OPENAPI: OpenApiAuthVerifier,
    AuthMedium.RCON: RconAuthVerifier,
    AuthMedium.SCP: ScpAuthVerifier
}
