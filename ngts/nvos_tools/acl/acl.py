import logging

from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.cli_wrappers.openapi.openapi_base_clis import OpenApiBaseCli
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.acl.rule import Rule
from ngts.nvos_constants.constants_nvos import ApiType


logger = logging.getLogger()


class Acl(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvueBaseCli, ApiType.OPENAPI: OpenApiBaseCli}, path='/acl')
        self.acl_dict = {}

    def set(self, acl_id, expected_str='', apply=False, ask_for_confirmation=False):
        acl_value = {} if TestToolkit.tested_api == ApiType.OPENAPI else ""
        result_obj = BaseComponent.set(self, op_param_name=acl_id, op_param_value=acl_value, expected_str=expected_str,
                                       apply=apply, ask_for_confirmation=ask_for_confirmation)
        if result_obj.result:
            acl_id_obj = AclID(acl_id=acl_id, parent_obj=self)
            self.acl_dict.update({acl_id: acl_id_obj})
        return result_obj

    def unset(self, acl_id="", expected_str="", apply=False, ask_for_confirmation=False):
        if acl_id:
            result_obj = BaseComponent.unset(self.acl_dict[acl_id], expected_str=expected_str, apply=apply,
                                             ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.acl_dict.pop(acl_id)
        else:
            result_obj = BaseComponent.unset(self, expected_str=expected_str, apply=apply, ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.acl_dict = {}
        return result_obj


class AclID(BaseComponent):

    def __init__(self, acl_id, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path=f'/{acl_id}')
        self.rule = Rule(self)
        self.inbound = BaseComponent(self, path='/inbound')
        self.outbound = BaseComponent(self, path='/outbound')
        self.statistics = BaseComponent(self, path='/statistics')
