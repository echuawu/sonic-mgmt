from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_tools.platform.Firmware import Firmware


class Platform(BaseComponent):
    firmware = None

    def __init__(self, parent_obj=None):
        self.firmware = Firmware(self)
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/platform'
        self.parent_obj = parent_obj

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /platform")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /platform")
