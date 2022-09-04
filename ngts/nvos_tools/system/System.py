from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Security import Security
from ngts.nvos_tools.system.Images import Images
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Reboot import Reboot
from ngts.nvos_tools.system.Log import Log
from ngts.nvos_tools.system.Debug_log import DebugLog
from ngts.nvos_tools.system.Component import Component
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Techsupport import TechSupport
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


class System(BaseComponent):
    security = None
    images = None
    firmware = None
    log = None
    debug_log = None
    component = None
    files = None

    def __init__(self, parent_obj=None):
        self.log = Log(self)
        self.debug_log = DebugLog(self)
        self.component = Component(self)
        self.files = Files(self)
        self.security = Security(self)
        self.techsupport = TechSupport(self)
        self.images = Images(self)
        self.firmware = Firmware(self)
        self.message = Message(self)
        self.version = Version(self)
        self.reboot = Reboot(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/system'
        self.parent_obj = parent_obj

    def set(self, value, engine, field_name="", apply=True):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                        engine, 'system ' + field_name, value)
        if apply:
            NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name="", apply=True):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                        engine, 'system ' + field_name)
        if apply:
            NvueGeneralCli.apply_config(engine, True)

    def get_expected_fields(self, device):
        return device.constants.system['system']


class Message(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/message'
        self.parent_obj = parent_obj

    def set(self, value, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                        engine, 'system ' + self._resource_path + " " + field_name, value)
        NvueGeneralCli.apply_config(engine, True)

    def unset(self, engine, field_name=""):
        SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset,
                                        engine, 'system ' + self._resource_path + " " + field_name)
        NvueGeneralCli.apply_config(engine, True)

    def get_expected_fields(self, device):
        return device.constants.system['message']


class Version(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/version'
        self.parent_obj = parent_obj

    def get_expected_fields(self, device):
        return device.constants.system['version']
