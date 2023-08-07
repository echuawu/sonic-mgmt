from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, ActionConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
import allure
import logging

logger = logging.getLogger()


class Asic(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/asic'
        self.parent_obj = parent_obj
        self.files = Files(self)

    def get_resource_path(self):
        self_path = self._resource_path.rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def _action(self, action_type, op_param="", expected_str="Action succeeded"):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_firmware_image,
                                                            expected_str,
                                                            TestToolkit.engines.dut,
                                                            action_type, self.get_resource_path(), op_param).get_returned_value()

    def action_fetch(self, url="", expected_str="Action succeeded"):
        with allure.step("Image fetch {url} ".format(url=url)):
            logging.info("Image fetch {url} system image".format(url=url))
            if TestToolkit.tested_api == ApiType.OPENAPI and expected_str == "Action succeeded":
                expected_str = 'File fetched successfully'
            return self._action(ActionConsts.FETCH, url, expected_str)

    def action_install_fw(self, fw_file_path='', expected_str="Action succeeded"):
        with allure.step("Install system firmware: '{path}'".format(path=fw_file_path)):
            logging.info("Install system firmware: '{path}'".format(path=fw_file_path))
            return SendCommandTool.execute_command_expected_str(
                self.api_obj[TestToolkit.tested_api].action_firmware_install, expected_str,
                TestToolkit.engines.dut, fw_file_path).get_returned_value()
