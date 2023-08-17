import logging

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
        valid_mediums = AuthConsts.AUTH_MEDIUMS  # [AuthConsts.SSH, AuthConsts.OPENAPI, AuthConsts.RCON]
        assert medium in valid_mediums, f'Medium should be in {valid_mediums}'

        self.medium = medium
        self.api = ApiType.NVUE if medium in [AuthConsts.SSH, AuthConsts.RCON] else ApiType.OPENAPI
        self.test_engines = engines

        if medium in [AuthConsts.SSH, AuthConsts.OPENAPI]:
            logging.info(f'Create proxy ssh engine for user: {username}')
            self.engine = ProxySshEngine(device_type=engines.dut.device_type, ip=engines.dut.ip, username=username,
                                         password=password)
        elif medium == AuthConsts.RCON:
            logging.info(f'Create pexpect serial engine for user: {username}')
            self.engine = ConnectionTool.create_serial_connection(topology_obj=topology_obj, ip=engines.dut.ip,
                                                                  username=username, password=password)
        else:  # SCP
            self.engine = None

    def change_test_api(self, api=None):
        api = self.api if api is None else api
        logging.info(f'Change test api to: {api}')
        TestToolkit.tested_api = api

    def verify_authentication(self, expect_success=True):
        orig_test_api = TestToolkit.tested_api
        self.change_test_api()
        try:
            if self.medium == AuthConsts.SCP:
                with allure.step('For SCP - upload a dummy file into a non privileged location on the switch'):
                    scp_file(self.test_engines.dut, AuthConsts.DUMMY_FILE_SHARED_LOCATION,
                             AuthConsts.SWITCH_NON_PRIVILEGED_PATH)
            elif self.medium == AuthConsts.OPENAPI:
                with allure.step('For OpenApi - run show command with OpenApi request to verify authentication'):
                    System().version.show(dut_engine=self.engine)
            else:  # SSH or RCON
                with allure.step(f'For {self.medium} - run empty command on engine to trigger authentication'):
                    self.engine.run_cmd('')
        except Exception:
            logging.info('Authentication failed')
            assert not expect_success, 'Authentication failed, but expected success'
        finally:
            self.change_test_api(orig_test_api)

    def verify_authorization(self, user_is_admin):
        if self.medium == AuthConsts.SCP:
            with allure.step('Upload a dummy file into a non privileged location on the switch. Expect success: True'):
                scp_file(self.test_engines.dut, AuthConsts.DUMMY_FILE_SHARED_LOCATION,
                         AuthConsts.SWITCH_NON_PRIVILEGED_PATH)
            with allure.step(f'Upload a dummy file into a privileged location on the switch. '
                             f'Expect success: {user_is_admin}'):
                try:
                    scp_file(self.test_engines.dut, AuthConsts.DUMMY_FILE_SHARED_LOCATION,
                             AuthConsts.SWITCH_PRIVILEGED_PATH)
                except Exception:
                    assert not user_is_admin, 'Could not upload to a privileged path, but expected success'
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
