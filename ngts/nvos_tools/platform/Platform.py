from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.platform.Environment import Environment
from ngts.nvos_tools.platform.Hardware import Hardware
from ngts.nvos_tools.platform.Software import Software


class Platform(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli},
                               path='/platform')
        self.firmware = BaseComponent(self, path='/firmware')
        self.environment = Environment(self)
        self.software = Software(self)
        self.hardware = Hardware(self)

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /platform")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /platform")
