from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Security import Security
from ngts.nvos_tools.system.Images import Images
from ngts.nvos_tools.system.Firmware import Firmware


class System(BaseComponent):
    security = None
    images = None
    firmware = None

    def __init__(self, parent_obj=None):
        self.security = Security(self)
        self.images = Images(self)
        self.firmware = Firmware(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/system'
        self.parent_obj = parent_obj

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /system")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /system")
