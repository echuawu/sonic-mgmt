import allure
import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.platform.Voltage import Voltage


class Environment(BaseComponent):
    platform_component_id = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self.voltage = Voltage(self)
        self._resource_path = '/environment'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(platform_component_id=self.platform_component_id).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def show(self, op_param="", output_format=OutputFormat.json):
        with allure.step('Execute show for {}'.format(self.get_resource_path())):
            if TestToolkit.tested_api == ApiType.OPENAPI:
                op_param = op_param.replace('/', "%2F").replace(' ', "/")
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param,
                                                   output_format).get_returned_value()

    def unset(self, op_param=""):
        raise Exception("unset is not implemented")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented")

    def action_turn(self, turn_type="", led=""):
        with allure.step("Turn {type} led {led}".format(type=turn_type, led=led)):
            logging.info("Turn {type} led {led}".format(type=turn_type, led=led))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_turn,
                                                   TestToolkit.engines.dut, turn_type, led)
