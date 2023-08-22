from typing import Dict

from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.DefaultDict import DefaultDict


class Hostname(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/hostname'
        self.parent_obj = parent_obj
        self.hostname_id: Dict[str, HostnameId] = DefaultDict(lambda hostname_id: HostnameId(self, hostname_id))


class HostnameId(BaseComponent):
    def __init__(self, parent_obj, hostname_id):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = f'/{hostname_id}'
        self.parent_obj = parent_obj
