import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.system.Health import Health
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli

logger = logging.getLogger()


class Fae(BaseComponent):

    def __init__(self, parent_obj=None):
        self._resource_path = '/fae'
        self.parent_obj = parent_obj
        self.firmware = Firmware(self)
        self.health = Health(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
