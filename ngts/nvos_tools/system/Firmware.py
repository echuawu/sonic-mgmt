import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType, ActionConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.Asic import Asic
logger = logging.getLogger()


class Firmware(BaseComponent):
    asic = ''

    def __init__(self, parent_obj):
        self.asic = Asic(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/firmware'
        self.parent_obj = parent_obj

    def action_install(self, fw_file_path):
        with allure.step("Install system firmware: '{path}'".format(path=fw_file_path)):
            logging.info("Install system firmware: '{path}'".format(path=fw_file_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_firmware_install,
                                                   TestToolkit.engines.dut, ActionConsts.INSTALL,
                                                   "firmware asic", fw_file_path).get_returned_value()
