from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.ListeningAddress import ListeningAddress
from ngts.nvos_tools.system.ReadonlyCommunity import ReadonlyCommunity


class SnmpServer(BaseComponent):
    listening_address = None
    readonly_community = None

    def __init__(self, parent_obj):
        self.listening_address = ListeningAddress(self)
        self.readonly_community = ReadonlyCommunity(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/snmp-server'
        self.parent_obj = parent_obj
