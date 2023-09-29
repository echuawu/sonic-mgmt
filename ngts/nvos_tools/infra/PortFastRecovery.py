import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueBaseCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiBaseCli

logger = logging.getLogger()


class PortFastRecovery(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}
        self._resource_path = '/fast-recovery'
        self.parent_obj = parent_obj
        self.trigger = Trigger(self)


class Trigger(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}
        self._resource_path = '/trigger'
        self.parent_obj = parent_obj
