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
    def __init__(self, medium, username, password, engines, topology_obj):
        valid_mediums = AuthConsts.AUTH_MEDIUMS
        assert medium in valid_mediums, f'Medium should be in {valid_mediums}'

        self.medium = medium
        self.api = ApiType.OPENAPI if medium == AuthConsts.OPENAPI else ApiType.NVUE
        self.test_engines = engines

        if medium == AuthConsts.RCON:
            logging.info(f'Create pexpect serial engine for user: {username}')
            self.engine = ConnectionTool.create_serial_engine(topology_obj=topology_obj, ip=engines.dut.ip,
                                                              username=username, password=password)
        else:
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
            if self.medium == AuthConsts.OPENAPI:
                with allure.step('For OpenApi - run show command with OpenApi request to verify authentication'):
                    System().version.show(dut_engine=self.engine)
            elif self.medium == AuthConsts.RCON:
                with allure.step('For RCON - start rcon connection and force new login'):
                    assert isinstance(self.engine, PexpectSerialEngine), 'engine should be pexpect serial engine'
                    self.engine.create_serial_engine(disconnect_existing_login=True)
            elif self.medium == AuthConsts.SSH:
                with allure.step('For SSH - run empty command on engine to trigger authentication'):
                    self.engine.run_cmd('')
            elif self.medium == AuthConsts.SCP:
                with allure.step(f'Download a dummy file from non-privileged location on the switch. '
                                 f'Expect success: {expect_success}'):
                    scp_file(player=self.engine,
                             src_path=f'{AuthConsts.SWITCH_NON_PRIVILEGED_PATH}/{AuthConsts.DUMMY_FILE_NAME}',
                             dst_path=AuthConsts.DOWNLOADED_FILES_SHARED_LOCATION,
                             download_from_remote=True)
                    logging.info('Download using SCP success')
        except Exception:
            logging.info('Authentication failed')
            authentication_success = False
        finally:
            self.change_test_api(orig_test_api)
            assert expect_success == authentication_success, 'Authentication result not as expected'

    def verify_authorization(self, user_is_admin):
        if self.medium == AuthConsts.SCP:
            with allure.step(f'Upload a dummy file into a non privileged location on the switch. '
                             f'Expect success: {user_is_admin}'):
                pass  # until scp session with nadav & yarden
                # try:
                #     scp_file(self.engine, AuthConsts.DUMMY_FILE_SHARED_LOCATION, AuthConsts.SWITCH_NON_PRIVILEGED_PATH)
                #     scp_success = True
                # except Exception:
                #     scp_success = False
                # finally:
                #     logging.info(f'SCP success: {scp_success}')
                #     assert scp_success == user_is_admin, 'SCP success depends on whether the user is admin or not'
        else:
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
