import allure
import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_tools.platform.Voltage import Voltage


class Environment(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self.voltage = Voltage(self)
        self.fan = Fan(self)
        self.led = Led(self)
        self.psu = Psu(self)
        self.temperature = Temperature(self)
        self._resource_path = '/environment'
        self.parent_obj = parent_obj

    def unset(self, op_param=""):
        raise Exception("unset is not implemented")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented")

    def action_turn(self, turn_type="", led=""):
        with allure.step("Turn {type} led {led}".format(type=turn_type, led=led)):
            logging.info("Turn {type} led {led}".format(type=turn_type, led=led))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_turn,
                                                   TestToolkit.engines.dut, turn_type, led)


class Fan(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/fan'
        self.parent_obj = parent_obj


class Led(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/led'
        self.parent_obj = parent_obj


class Psu(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/psu'
        self.parent_obj = parent_obj


class Temperature(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/temperature'
        self.parent_obj = parent_obj
