import logging
import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Security import Security
from ngts.nvos_tools.system.Images import Images
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Reboot import Reboot
from ngts.nvos_tools.system.Log import Log
from ngts.nvos_tools.system.Debug_log import DebugLog
from ngts.nvos_tools.system.Component import Component
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Techsupport import TechSupport
from ngts.nvos_tools.system.Aaa import Aaa
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


class System(BaseComponent):
    security = None
    images = None
    firmware = None
    log = None
    debug_log = None
    component = None
    files = None

    def __init__(self, parent_obj=None, username='admin'):
        self.aaa = Aaa(self, username)
        self.log = Log(self)
        self.debug_log = DebugLog(self)
        self.component = Component(self)
        self.files = Files(self)
        self.security = Security(self)
        self.techsupport = TechSupport(self)
        self.images = Images(self)
        self.firmware = Firmware(self)
        self.message = Message(self)
        self.version = Version(self)
        self.reboot = Reboot(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/system'
        self.parent_obj = parent_obj

    def create_new_connected_user(self, engine, username=None, password=None, role=SystemConsts.ROLE_CONFIGURATOR):
        """

        :param username: if it's not a specific username we will generate one
        :param password:  if it's not a specific password we will generate one
        :param role: the user role
        :return: return new user
        """
        with allure.step('create new user with ssh connection'):
            username, password = self.create_new_user(engine, username, password, role)
            return ConnectionTool.create_ssh_conn(engine.ip, username, password).verify_result()

    def create_new_user(self, engine, username=None, password=None, role=SystemConsts.ROLE_CONFIGURATOR):
        """
        Create a new user
        :param engine: ssh angine
        :param username: if it's not a specific username we will generate one
        :param password:  if it's not a specific password we will generate one
        :param role: the user role
        :return: the user name and password of the created user
        """
        with allure.step('create new user'):
            if not username:
                username = User.generate_username()

            logger.info('the new username is {username}'.format(username=username))
            if not password:
                password = self.security.password_hardening.generate_password()

            logger.info('the new user password is {password}'.format(password=password))
            curr_username = self.aaa.user.username
            self.aaa.user.set_username(username)
            self.aaa.user.set('password', '"' + password + '"').verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, engine, True).verify_result()

            if role is not SystemConsts.ROLE_CONFIGURATOR:
                self.aaa.user.set('role', role)
                SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                apply_config, engine, True).verify_result()
            self.aaa.user.set_username(curr_username)
            logging.info("User created: \nuser_name: {} \npassword: {}".format(username, password))
            return username, password

    def set(self, value, engine, field_name="", apply=True):
        result_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                                     engine, self._resource_path, field_name, value)
        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, True)
        return result_obj

    def unset(self, engine, field_name="", apply=True):
        result_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                                     engine, self._resource_path + "/" + field_name)
        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, True)
        return result_obj

    def get_expected_fields(self, device):
        return device.constants.system['system']


class Message(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/message'
        self.parent_obj = parent_obj

    def set(self, value, engine, field_name="", apply=True):
        if TestToolkit.tested_api == ApiType.NVUE:
            value = '"{}"'.format(value)
        result_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                                     engine, self.get_resource_path(), field_name, value)
        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, True)
        return result_obj

    def unset(self, engine, field_name="", apply=True):
        result_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                                     engine, self.get_resource_path() + "/" + field_name)
        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, True)
        return result_obj

    def get_expected_fields(self, device):
        return device.constants.system['message']


class Version(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/version'
        self.parent_obj = parent_obj

    def get_expected_fields(self, device):
        return device.constants.system['version']
