import logging
import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_opensm_clis import NvueOpenSmCli
from ngts.cli_wrappers.openapi.openapi_opensm_cli import OpenApiOpenSmCli
from ngts.nvos_tools.ib.Sm import Sm

logger = logging.getLogger()


class Ib(BaseComponent):
    sm = None
    device = None

    def __init__(self, parent_obj=None):
        self.sm = Sm(self)
        self.device = BaseComponent(self, {ApiType.NVUE: NvueOpenSmCli, ApiType.OPENAPI: OpenApiOpenSmCli}, '/device')
        self.api_obj = {ApiType.NVUE: NvueOpenSmCli, ApiType.OPENAPI: OpenApiOpenSmCli}
        self._resource_path = '/ib'
        self.parent_obj = parent_obj
