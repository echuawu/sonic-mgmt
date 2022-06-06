from ngts.nvos_tools.general.system.BaseSystem import BaseSystem
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


class System(BaseSystem):
    def __init__(self):
        BaseSystem.__init__(self)
        self.message = Message()
        self.version = Version()
        self.reboot = Reboot()

    def set(self, value, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                        engine, 'system ' + field_name, value)
        NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                        engine, 'system ' + field_name)
        NvueGeneralCli.apply_config(engine, True)


class Message(BaseSystem):
    def __init__(self):
        BaseSystem.__init__(self, "message")

    def set(self, value, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                        engine, 'system ' + self.resource_path + " " + field_name, value)
        NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                        engine, 'system ' + self.resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)


class Reboot(BaseSystem):
    def __init__(self):
        BaseSystem.__init__(self, "reboot")


class Version(BaseSystem):
    def __init__(self):
        BaseSystem.__init__(self, "version")
