from ngts.nvos_tools.general.system.BaseSystem import BaseSystem
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli


class System(BaseSystem):
    def __init__(self, device):
        BaseSystem.__init__(self, device)
        self.message = Message(device)
        self.version = Version(device)
        self.reboot = Reboot(device)

    def set(self, value, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj.set,
                                        engine, value, self.resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj.unset,
                                        engine, self.resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)


class Message(BaseSystem):
    def __init__(self, device):
        BaseSystem.__init__(self, device, "message")

    def set(self, value, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj.set,
                                        engine, value, self.resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj.unset,
                                        engine, self.resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)


class Reboot(BaseSystem):
    def __init__(self, device):
        BaseSystem.__init__(self, device, "reboot")


class Version(BaseSystem):
    def __init__(self, device):
        BaseSystem.__init__(self, device, "version")
