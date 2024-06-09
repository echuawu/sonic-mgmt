import logging
from typing import Dict
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.acl.match import Match
from ngts.nvos_tools.acl.action import Action
from ngts.nvos_constants.constants_nvos import AclConsts
from ngts.nvos_tools.infra.DefaultDict import DefaultDict


logger = logging.getLogger()


class Rule(BaseComponent):

    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/rule')
        self.rule_id: Dict[str, RuleID] = DefaultDict(lambda rule_id: RuleID(parent_obj=self, rule_id=rule_id))


class RuleID(BaseComponent):

    def __init__(self, rule_id=None, parent_obj=None):
        super().__init__(parent=parent_obj, path=f'/{rule_id}')
        self.match = Match(self)
        self.action = Action(self)

    def set_remark(self, remark):
        return self.set(AclConsts.REMARK, remark)
