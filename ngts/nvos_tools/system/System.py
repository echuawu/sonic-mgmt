import logging
import allure
import time
from retry import retry
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_tools.infra.ClockTestTools import ClockTestTools
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.system.Security import Security
from ngts.nvos_tools.system.Syslog import Syslog
from ngts.nvos_tools.system.Ntp import Ntp
from ngts.nvos_tools.system.Ssh_server import SshServer
from ngts.nvos_tools.system.Image import Image
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Reboot import Reboot
from ngts.nvos_tools.system.Profile import Profile
from ngts.nvos_tools.system.Log import Log
from ngts.nvos_tools.system.Debug_log import DebugLog
from ngts.nvos_tools.system.Component import Component
from ngts.nvos_tools.system.Rotation import Rotation
from ngts.nvos_tools.system.SnmpServer import SnmpServer
from ngts.nvos_tools.system.ListeningAddress import ListeningAddress
from ngts.nvos_tools.system.ReadonlyCommunity import ReadonlyCommunity
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Techsupport import TechSupport
from ngts.nvos_tools.system.Aaa import Aaa
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.system.Health import Health
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import OutputFormat
import datetime
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool

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

    def __init__(self, parent_obj=None, username='admin'):
        self._resource_path = '/system'
        self.parent_obj = parent_obj
        self.documentation = Documentation(self)
        self.aaa = Aaa(self, username)
        self.log = Log(self)
        self.debug_log = DebugLog(self)
        self.component = Component(self)
        self.rotation = Rotation(self)
        self.snmp_server = SnmpServer(self)
        self.listening_address = ListeningAddress(self)
        self.readonly_community = ReadonlyCommunity(self)
        self.security = Security(self)
        self.ssh_server = SshServer(self)
        self.syslog = Syslog(self)
        self.ntp = Ntp(self)
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
        self.timezone = Timezone(self)
        self.datetime = DateTime(self)

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

    def validate_health_status(self, expected_status):
        with allure.step("Validate health status with \"nv show system\" cmd"):
            logger.info("Validate health status with \"nv show system\" cmd")
            system_output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
            assert expected_status == system_output[SystemConsts.HEALTH_STATUS], \
                "Unexpected health status. \n Expected: {}, but got :{}".format(expected_status,
                                                                                system_output[SystemConsts.HEALTH_STATUS])

    @retry(Exception, tries=3, delay=2)
    def wait_until_health_status_change_to(self, expected_status):
        self.validate_health_status(expected_status)


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


class Documentation(BaseComponent):
    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/documentation'
        self.parent_obj = parent_obj

    def action_upload(self, upload_path, file_name):
        with allure.step("Upload {file} to '{path}".format(file=file_name, path=upload_path)):
            logging.info("Upload {file} to '{path}".format(file=file_name, path=upload_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload, TestToolkit.engines.dut,
                                                   self.get_resource_path(), 'files ' + file_name, upload_path)


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
            start_time = time.time()
            res_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_reset,
                                                      engine, "factory-default", param)
            end_time = time.time()
            duration = end_time - start_time

            with allure.step("Reset factory takes: {} seconds".format(duration)):
                logger.info("Reset factory takes: {} seconds".format(duration))

            NvueGeneralCli.wait_for_nvos_to_become_functional(engine)
            end_time = time.time()
            duration = end_time - start_time
            with allure.step("Reset factory till system is functional takes: {} seconds".format(duration)):
                logger.info("Reset factory till system is functional takes: {} seconds".format(duration))
            return res_obj


class Timezone(BaseComponent):
    """
    @summary:
    Infra class for system.timezone field object

    NOTE:
        currently it's a mock, until design is ready.

        mock - set & unset don't really change anything,
        except for setting/unsetting a variable (parent_obj.timezone_val),
        which holds the current timezone during the test.

        parent_obj should always be MockSystem (until design ready).

        when design is ready, uncomment the real infra implementation.
    """

    def __init__(self, parent_obj):
        self.parent_obj = parent_obj
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/timezone'  # todo: verify this; not listed in HLD

    def set(self, op_param_name="", op_param_value={}, expected_str='', apply=False, ask_for_confirmation=False):
        result_obj = ResultObj(True)

        rsrc_path = self.get_resource_path()
        with allure.step('Execute set for {resource_path}\ttimezone param: {tz}'.format(resource_path=rsrc_path, tz=op_param_name)):
            logging.info('Execute set for {resource_path}\ttimezone param: {tz}'.format(resource_path=rsrc_path, tz=op_param_name))
            if op_param_name not in self.parent_obj.valid_timezones:
                return ResultObj(False, "Error:\tcommand 'nv set system timezone'\tresource {rsc}\tInvalid timezone arg".format(rsc=rsrc_path))
            if apply:
                with allure.step("Applying set configuration"):
                    logging.info("Applying set configuration")

                    self.parent_obj.timezone_val = op_param_name  # <-- the mock

            """result_obj = BaseComponent.set(self, op_param_name=op_param_name, op_param_value=op_param_value, expected_str=expected_str)
            if result_obj.result and apply:
                with allure.step("Applying set configuration"):
                    result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                                 TestToolkit.engines.dut, ask_for_confirmation)"""

        return result_obj

    def unset(self, op_param="", expected_str="", apply=False, ask_for_confirmation=False):
        from ngts.tests_nvos.system.clock_and_timezone.ClockConsts import ClockConsts

        result_obj = ResultObj(True)

        rsrc_path = self.get_resource_path()
        with allure.step('Execute set for {resource_path}'.format(resource_path=rsrc_path)):
            logging.info('Execute set for {resource_path}'.format(resource_path=rsrc_path))
            if apply:
                with allure.step("Applying set configuration"):
                    logging.info("Applying set configuration")

                    self.parent_obj.timezone_val = ClockConsts.DEFAULT_TIMEZONE  # <-- the mock

            """result_obj = BaseComponent.unset(self, op_param, expected_str)
            if result_obj.result and apply:
                with allure.step("Applying unset configuration"):
                    result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                                 TestToolkit.engines.dut, ask_for_confirmation)"""

        return result_obj


class DateTime(BaseComponent):
    """
    @summary:
    Infra class for system.date-time field object

    NOTE:
        currently it's a mock, until design is ready.

        mock - action change doesn't really change anything,
        except for setting/unsetting a variable (parent_obj.datetime_val),
        which holds the current date-time during the test.

        parent_obj should always be MockSystem (until design ready).

        when design is ready, uncomment the real infra implementation.
    """

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/date-time'  # todo: verify this
        self.parent_obj = parent_obj

    def action_change_datetime(self, engine=None, params=""):
        result_obj = ResultObj(True)

        rsrc_path = self.get_resource_path()
        with allure.step('Execute action change for {resource_path}'.format(resource_path=rsrc_path)):
            logging.info('Execute action change for {resource_path}'.format(resource_path=rsrc_path))
            result_obj.info = "action change system date-time success"
            try:
                logging.info('Execute action change for time only - {p}'.format(p=params))
                datetime.time.fromisoformat(params)
                cur_datetime = ClockTestTools.get_datetime_from_show_system_output(self.parent_obj.show())
                self.parent_obj.datetime_val = cur_datetime.split(' ')[0] + ' ' + params  # <-- the mock
                logging.info('Execute action change for time only - {p} - SUCCESS'.format(p=params))
            except ValueError:
                try:
                    logging.info('Execute action change for date & time - {p}'.format(p=params))
                    if not ClockTestTools.is_datetime_format(params):
                        raise ValueError()
                    dt_obj = datetime.datetime.fromisoformat(params)
                    min_range_dt_obj = datetime.datetime.fromisoformat(SystemConsts.MIN_SYSTEM_DATETIME)
                    max_range_dt_obj = datetime.datetime.fromisoformat(SystemConsts.MAX_SYSTEM_DATETIME)
                    if dt_obj < min_range_dt_obj or dt_obj > max_range_dt_obj:
                        raise ValueError()
                    self.parent_obj.datetime_val = params  # <-- the mock
                    logging.info('Execute action change for date & time - {p} - SUCCESS'.format(p=params))
                except ValueError:
                    logging.info('Execute action change for - {p} - FAIL'.format(p=params))
                    result_obj.result = False
                    result_obj.info = "Invalid date-time arg \nInvalid param for action date-time command: {p}"\
                        .format(p=params)

        """with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            if not engine:
                engine = TestToolkit.engines.dut
            # todo: implemented action_change_system_datetime() in NvueSystemCli. do this in OpenApiSystemCli too?
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_change_system_datetime,
                                                   engine,
                                                   self.get_resource_path().replace('/date-time', ' '), params)"""

        return result_obj
