from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli


class BaseSystem:
    api_obj = None
    output_dictionary = None
    resource_path = None

    def __init__(self, device, resource_path=""):
        self.api_obj = NvueSystemCli
        self.resource_path = resource_path

        self._init_output_dictionary(device)

    def _init_output_dictionary(self, device):
        const_path = self.resource_path if self.resource_path != "" else "system"
        system_constant_list = device.constants.system[const_path]
        none_values = len(system_constant_list) * [None]
        self.output_dictionary = dict(zip(system_constant_list, none_values))

    def update_output_dictionary(self, engine):
        output = OutputParsingTool.parse_show_output_to_dictionary(self.show(engine))
        for key in self.output_dictionary.keys():
            self.output_dictionary[key] = output[key]

    def show(self, engine):
        return SendCommandTool.execute_command(self.api_obj.show,
                                               engine, self.resource_path + " ").get_returned_value()
