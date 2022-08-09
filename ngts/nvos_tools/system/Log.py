import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Component import Component
logger = logging.getLogger()


class Log(BaseComponent):
    files = None
    component = None

    def __init__(self, parent_obj):
        self.files = Files(self)
        self.component = Component(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/log'
        self.parent_obj = parent_obj

    def show_log(self, log_type='', param='', exit_cmd=''):
        with allure.step('Execute nv show system {type}log {param} and exit cmd {exit_cmd}'.format(type=log_type, param=param, exit_cmd=exit_cmd)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_log,
                                                   TestToolkit.engines.dut, log_type, param, exit_cmd).get_returned_value()

    def rotate_logs(self):
        with allure.step('Rotate logs'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_rotate_logs,
                                                   TestToolkit.engines.dut).get_returned_value()
