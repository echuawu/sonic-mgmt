import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Rotation import Rotation
logger = logging.getLogger()


class DebugLog(BaseComponent):
    files = None
    rotation = None

    def __init__(self, parent_obj):
        self.files = Files(self)
        self.rotation = Rotation(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/debug-log'
        self.parent_obj = parent_obj

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /debug_log")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /debug_log")

    def show_log(self, log_type='', param='', exit_cmd=''):
        with allure.step('Execute nv show system {type}log {param} and exit_cmd {exit_cmd}'.format(type=log_type,
                                                                                                   param=param,
                                                                                                   exit_cmd=exit_cmd)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_log,
                                                   TestToolkit.engines.dut, log_type,
                                                   param, exit_cmd).get_returned_value()

    def write_to_debug_log(self):
        with allure.step('Write content to debug-logs'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_write_to_debug_logs,
                                                   TestToolkit.engines.dut).get_returned_value()

    def rotate_debug_logs(self):
        with allure.step('Rotate debug-logs'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_rotate_debug_logs,
                                                   TestToolkit.engines.dut).get_returned_value()
