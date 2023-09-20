import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.system.Firmware import Firmware
from ngts.nvos_tools.ib.IpoibMapping import IpoibMapping
from ngts.nvos_tools.system.Health import Health
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli

logger = logging.getLogger()


class Fae(BaseComponent):

    def __init__(self, parent_obj=None, port_name='eth0'):
        self._resource_path = '/fae'
        self.system = BaseComponent(self, {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}, '/system')
        self.parent_obj = parent_obj
        self.firmware = Firmware(self)
        self.ipoibmapping = IpoibMapping(self)
        self.health = Health(self)
        self.port = MgmtPort(port_name, self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
