import logging

from typing import Dict
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.acl.rule import Rule
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.DefaultDict import DefaultDict


logger = logging.getLogger()


class Acl(BaseComponent):

    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, api={ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}, path='/acl')
        self.acl_id: Dict[str, AclID] = DefaultDict(lambda acl_id: AclID(parent_obj=self, acl_id=acl_id))


class AclID(BaseComponent):

    def __init__(self, acl_id, parent_obj=None):
        super().__init__(parent=parent_obj, path=f'/{acl_id}')
        self.rule = Rule(self)
        self.inbound = BaseComponent(self, path='/inbound')
        self.outbound = BaseComponent(self, path='/outbound')
        self.statistics = BaseComponent(self, path='/statistics')
