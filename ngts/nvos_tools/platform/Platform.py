from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_tools.platform.Firmware import Firmware
from ngts.nvos_tools.platform.Environment import Environment
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.platform.Software import Software
from ngts.nvos_tools.platform.Hardware import Hardware


class Platform(BaseComponent):
    firmware = None

    def __init__(self, parent_obj=None):
        self.firmware = Firmware(self)
        self.environment = Environment(self)
        self.software = Software(self)
        self.hardware = Hardware(self)
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/platform'
        self.parent_obj = parent_obj

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /platform")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /platform")

    def get_tab_output(self, str_comp="", engine=None):
        if not engine:
            engine = TestToolkit.engines.dut
        cmd = "nv show platform {}".format(str_comp) + '\x09'
        show_output = engine.run_cmd(cmd)
        if show_output:
            show_output = show_output.split('\t')
        return show_output
