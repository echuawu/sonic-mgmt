import logging
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Files import Files

logger = logging.getLogger()


class Config(BaseComponent):
    files = None

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.files = Files(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/config'
        self.parent_obj = parent_obj

    def action_fetch(self, remote_url, expected_str=""):
        with allure.step('Trying to fetch {}'.format(remote_url)):
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_fetch,
                                                                expected_str, TestToolkit.engines.dut,
                                                                self.get_resource_path(),
                                                                remote_url).verify_result()

    def action_export(self, file_name, expected_str=""):
        with allure.step('Trying to export the applied configuration to {}'.format(file_name)):
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_export,
                                                                expected_str, TestToolkit.engines.dut,
                                                                self.get_resource_path(), file_name).verify_result()
