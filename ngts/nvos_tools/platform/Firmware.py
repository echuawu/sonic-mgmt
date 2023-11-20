from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli


class Firmware(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}
        self._resource_path = '/firmware'
        self.parent_obj = parent_obj

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /firmware/{platform_component_id}")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented for /firmware/{platform_component_id}")
