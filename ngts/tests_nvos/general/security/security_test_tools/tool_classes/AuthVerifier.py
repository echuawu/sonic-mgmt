import logging
import subprocess

from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthConsts
from ngts.tools.test_utils import allure_utils as allure
from infra.tools.linux_tools.linux_tools import scp_file


class AuthVerifier:
    def __init__(self, username, password, engines, topology_obj):
        self.api = ApiType.NVUE
        logging.info(f'Create proxy ssh engine for user: {username}')
        self.engine = ProxySshEngine(device_type=engines.dut.device_type, ip=engines.dut.ip, username=username,
                                     password=password)

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
        except Exception:
            logging.info('Authentication failed')
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
                system.message.set(field_name='pre-login', value="NVOS TESTS", engine=self.engine,
                                   apply=user_is_admin).verify_result(should_succeed=user_is_admin)
            with allure.step(f'Run unset command. Expect success: {user_is_admin}'):
                system.message.unset(field_name='pre-login', engine=self.engine,
                                     apply=user_is_admin).verify_result(should_succeed=user_is_admin)
        finally:
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
            scp_file(player=self.engine,
                     src_path=f'{AuthConsts.SWITCH_NON_PRIVILEGED_DIR}/{AuthConsts.SWITCH_SCP_TEST_FILE_NAME}',
                     dst_path=AuthConsts.DOWNLOADED_FILES_SHARED_LOCATION,
                     download_from_remote=True)

    def __verify_scp(self, src_path, dst_path, should_download, expect_success, remove_file_after_scp=''):
        scp_success = True
        try:
            scp_file(player=self.engine,
                     src_path=src_path,
                     dst_path=dst_path,
                     download_from_remote=should_download)
            logging.info('SCP success')
            if not should_download and remove_file_after_scp:
                self.engine.run_cmd(f'rm {remove_file_after_scp}')
                logging.info('Removed uploaded file')
        except Exception as e:
            logging.info('SCP failed')
            if expect_success:
                logging.info(f'Error: {e}')
            scp_success = False
        finally:
            assert scp_success == expect_success, f'SCP success ({scp_success}) status ' \
                                                  f'not as expected ({expect_success})'

    def _verify_scp_download(self, switch_path, expect_success):
        with allure.step(f'Verify SCP download from the switch. Expect success: {expect_success}'):
            self.__verify_scp(
                src_path=AuthConsts.DUMMY_FILE_SHARED_LOCATION,
                dst_path=switch_path,
                should_download=False,
                expect_success=expect_success
            )

    def _verify_scp_upload(self, switch_path, expect_success):
        with allure.step(f'Verify SCP upload to the switch. Expect success: {expect_success}'):
            self.__verify_scp(
                src_path=AuthConsts.DUMMY_FILE_SHARED_LOCATION,
                dst_path=switch_path,
                should_download=False,
                expect_success=expect_success,
                remove_file_after_scp=f'{switch_path}/{AuthConsts.DUMMY_FILE_NAME}'
            )

    def _verify_scp_download_and_upload(self, switch_path, expect_success):
        self._verify_scp_download(switch_path, expect_success)
        self._verify_scp_upload(switch_path, expect_success)

    def verify_authorization(self, user_is_admin):
        with allure.step('Verify SCP with non privileged path on the switch. Expect success: True'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_NON_PRIVILEGED_DIR, expect_success=True)

        with allure.step(f'Verify SCP with admin privileged path on the switch. Expect success: {user_is_admin}'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_ADMIN_USERS_DIR, expect_success=user_is_admin)

        with allure.step('Verify SCP with root privileged path on the switch. Expect success: False'):
            self._verify_scp_download_and_upload(AuthConsts.SWITCH_ROOT_DIR, expect_success=False)


AUTH_VERIFIERS = {
    AuthConsts.SSH: SshAuthVerifier,
    AuthConsts.OPENAPI: OpenApiAuthVerifier,
    AuthConsts.RCON: RconAuthVerifier,
    AuthConsts.SCP: ScpAuthVerifier
}
