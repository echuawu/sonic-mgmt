from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class Action(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli}, path='/action')

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /action")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /action")
