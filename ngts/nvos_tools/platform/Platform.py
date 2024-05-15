import logging

from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.platform.Environment import Environment
from ngts.nvos_tools.platform.Inventory import Inventory
from ngts.nvos_tools.platform.Software import Software
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.platform.PS_Redundancy import PS_Redundancy

logger = logging.getLogger()


class Platform(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj,
                         api={ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli},
                         path='/platform')
        self.firmware = Firmware(self)
        self.environment = Environment(self)
        self.software = Software(self)
        self.inventory = Inventory(self)
        self.ps_redundancy = PS_Redundancy(self)
        self.transceiver = BaseComponent(self, path='/transceiver')

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /platform")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /platform")
