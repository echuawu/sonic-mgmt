from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, ActionConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
import allure
import logging

logger = logging.getLogger()


class Asic(BaseComponent):
    asic_component = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/asic/{asic_component}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(asic_component=self.asic_component).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /asic/{asic_component}")

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /asic/{asic_component}")

    def action_install(self, fw_file_path):
        with allure.step("Install system firmware asic: '{path}'".format(path=fw_file_path)):
            logger.info("Install system firmware asic: '{path}'".format(path=fw_file_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_firmware_install,
                                                   TestToolkit.engines.dut,
                                                   self.get_resource_path().replace("/", " "), fw_file_path).get_returned_value()
