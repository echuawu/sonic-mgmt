import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.acl.match import Match
from ngts.nvos_tools.acl.action import Action
from ngts.nvos_constants.constants_nvos import ApiType, AclConsts


logger = logging.getLogger()


class Rule(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/rule')
        self.rules_dict = {}

    def set(self, rule_id, expected_str='', apply=False, ask_for_confirmation=False):
        rule_value = {} if TestToolkit.tested_api == ApiType.OPENAPI else ""
        result_obj = BaseComponent.set(self, op_param_name=rule_id, op_param_value=rule_value, expected_str=expected_str,
                                       apply=apply, ask_for_confirmation=ask_for_confirmation)
        if result_obj.result:
            rule_id_obj = RuleID(rule_id=rule_id, parent_obj=self)
            self.rules_dict.update({rule_id: rule_id_obj})
        return result_obj

    def unset(self, rule_id="", expected_str="", apply=False, ask_for_confirmation=False):
        if rule_id:
            result_obj = BaseComponent.unset(self.rules_dict[rule_id], expected_str=expected_str, apply=apply,
                                             ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.rules_dict.pop(rule_id)
        else:
            result_obj = BaseComponent.unset(self, expected_str=expected_str, apply=apply,
                                             ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.rules_dict = {}
        return result_obj


class RuleID(BaseComponent):

    def __init__(self, rule_id=None, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path=f'/{rule_id}')
        self.match = Match(self)
        self.action = Action(self)
        self.recent_list = RecentList(self)

    def set_remark(self, remark):
        return self.set(AclConsts.REMARK, remark)


class RecentList(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/recent-list')

    def set_action(self, action):
        return self.set(AclConsts.ACTION, action)
