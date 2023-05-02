from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
import logging

logger = logging.getLogger()


class State(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/state'
        self.parent_obj = port_obj


class Diagnostics(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/diagnostics'
        self.parent_obj = port_obj
