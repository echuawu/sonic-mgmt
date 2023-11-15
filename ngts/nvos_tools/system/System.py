import logging
import time
from retry import retry
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.system.Security import Security
from ngts.nvos_tools.system.Syslog import Syslog
from ngts.nvos_tools.system.Ntp import Ntp
from ngts.nvos_tools.system.Stats import Stats
from ngts.nvos_tools.system.Ssh_server import SshServer
from ngts.nvos_tools.system.Serial_console import SerialConsole
from ngts.nvos_tools.system.Image import Image
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Reboot import Reboot
from ngts.nvos_tools.system.Profile import Profile
from ngts.nvos_tools.system.Config import Config
from ngts.nvos_tools.system.Log import Log
from ngts.nvos_tools.system.Debug_log import DebugLog
from ngts.nvos_tools.system.SnmpServer import SnmpServer
from ngts.nvos_tools.system.Techsupport import TechSupport
from ngts.nvos_tools.system.Aaa import Aaa
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.system.Health import Health
from ngts.nvos_tools.system.Gnmi_server import Gnmi_server
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


class System(BaseComponent):
    security = None
    image = None
    firmware = None
    log = None
    debug_log = None
    component = None
    files = None
    rotation = None
    snmp_server = None
    listening_address = None
    readonly_community = None
    syslog = None
    ntp = None
    ssh_server = None
    health = None

    def __init__(self, parent_obj=None, username='admin', devices_dut=None):
        self._resource_path = '/system'
        self.parent_obj = parent_obj
        self.config = Config(self)
        self.documentation = Documentation(self)
        self.aaa = Aaa(self, username)
        self.log = Log(self)
        self.debug_log = DebugLog(self)
        self.snmp_server = SnmpServer(self)
        self.security = Security(self)
        self.ssh_server = SshServer(self)
        self.serial_console = SerialConsole(self)
        self.syslog = Syslog(self)
        self.ntp = Ntp(self)
        self.stats = Stats(self, devices_dut)
        self.techsupport = TechSupport(self)
        self.image = Image(self)
        self.firmware = Firmware(self)
        self.message = Message(self)
        self.version = Version(self)
        self.reboot = Reboot(self)
        self.factory_default = FactoryDefault(self)
        self.profile = Profile(self)
        self.health = Health(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self.datetime = DateTime(self)
        self.gnmi_server = Gnmi_server(self)
        self.web_server_api = WebServerAPI(self)

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

    @staticmethod
    def get_expected_fields(device):
        return device.constants.system['system']

    def validate_health_status(self, expected_status):
        with allure.step("Validate health status with \"nv show system\" cmd"):
            logger.info("Validate health status with \"nv show system\" cmd")
            system_output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
            assert expected_status == system_output[SystemConsts.HEALTH_STATUS], \
                "Unexpected health status. \n Expected: {}, but got :{}".\
                format(expected_status, system_output[SystemConsts.HEALTH_STATUS])

    @retry(Exception, tries=3, delay=2)
    def wait_until_health_status_change_to(self, expected_status):
        self.validate_health_status(expected_status)


class Message(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/message'
        self.parent_obj = parent_obj

    @staticmethod
    def get_expected_fields(device):
        return device.constants.system['message']


class Version(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/version'
        self.parent_obj = parent_obj

    @staticmethod
    def get_expected_fields(device):
        return device.constants.system['version']


class Documentation(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/documentation'
        self.parent_obj = parent_obj

    def action_upload(self, upload_path, file_name):
        with allure.step("Upload {file} to '{path}".format(file=file_name, path=upload_path)):
            logging.info("Upload {file} to '{path}".format(file=file_name, path=upload_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload,
                                                   TestToolkit.engines.dut, self.get_resource_path(),
                                                   'files ' + file_name, upload_path)


class FactoryDefault(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/factory-default'
        self.parent_obj = parent_obj

    def show(self, op_param="", output_format=OutputFormat.json):
        raise Exception("unset is not implemented for system/factory-default")

    def set(self, op_param_name="", op_param_value=None):
        raise Exception("unset is not implemented for system/factory-default")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for system/factory-default")

    def action_reset(self, engine=None, param=""):
        with allure.step("Execute factory reset {}".format(param)):
            logging.info("Execute factory reset {}".format(param))
            if not engine:
                engine = TestToolkit.engines.dut

            marker = TestToolkit.get_loganalyzer_marker(engine)

            start_time = time.time()

            res_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_reset,
                                                      engine, "factory-default", param)
            end_time = time.time()
            duration = end_time - start_time

            TestToolkit.add_loganalyzer_marker(engine, marker)

            with allure.step("Reset factory takes: {} seconds".format(duration)):
                logger.info("Reset factory takes: {} seconds".format(duration))

            DutUtilsTool.wait_for_nvos_to_become_functional(engine).verify_result()
            end_time = time.time()
            duration = end_time - start_time
            with allure.step("Reset factory till system is functional takes: {} seconds".format(duration)):
                logger.info("Reset factory till system is functional takes: {} seconds".format(duration))
            return res_obj


class DateTime(BaseComponent):
    """
    @summary:
    Infra class for system.date-time field object
    """

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/date-time'
        self.parent_obj = parent_obj

    def action_change(self, params=""):
        rsrc_path = self.get_resource_path()

        with allure.step('Execute action change for {rsrcp} \tparams: {prm}'.format(rsrcp=rsrc_path, prm=params)):
            logging.info('Execute action change for {rsrcp} \tparams: {prm}'.format(rsrcp=rsrc_path, prm=params))

            if TestToolkit.tested_api == ApiType.OPENAPI:
                params_list = params.split(' ')
                clock_date = params_list[0] if len(params_list) else ''
                clock_time = params_list[1] if len(params_list) > 1 else ''
                params = {'clock-date': clock_date, 'clock-time': clock_time}

            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_change,
                                                   TestToolkit.engines.dut, rsrc_path, params)


class WebServerAPI(BaseComponent):
    connections = None
    listen_address = None

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/api'
        self.parent_obj = parent_obj
        self.connections = Connections(self)
        self.listen_address = ListenAddress(self)

    @staticmethod
    def get_expected_fields(device):
        return device.constants.system['web_server_api']


class Connections(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/connections'
        self.parent_obj = parent_obj

    def get_expected_fields(self, device):
        return device.constants.system['connections']


class ListenAddress(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/listening-address'
        self.parent_obj = parent_obj

    def get_expected_fields(self, device):
        return device.constants.system['listen_address']
