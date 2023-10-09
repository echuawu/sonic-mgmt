import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import OutputFormat


class IpoibMapping(BaseComponent):

    def __init__(self, parent_obj=None):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/ipoib-mapping'
        self.parent_obj = parent_obj

    def show_mapping(self, op_param="", output_format=OutputFormat.json):
        with allure.step('Execute nv show fae interface ipoib-mapping'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show,
                                                   TestToolkit.engines.dut, self.get_resource_path()).get_returned_value()
