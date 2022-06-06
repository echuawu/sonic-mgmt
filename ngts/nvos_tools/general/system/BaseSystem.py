from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


class BaseSystem:
    api_obj = {ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}
    output_dictionary = None
    resource_path = None

    def __init__(self, resource_path=""):
        self.resource_path = resource_path

    def get_expected_fields(self, device):
        const_path = self.resource_path if self.resource_path != "" else "system"
        return device.constants.system[const_path]

    def update_output_dictionary(self, engine):
        self.output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(self.show(engine)).get_returned_value()

    def show(self, engine):
        return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show,
                                               engine, 'system ' + self.resource_path).get_returned_value()
