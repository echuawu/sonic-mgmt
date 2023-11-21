from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Restrictions import Restrictions


class Authentication(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/authentication')
        self.restrictions = Restrictions(self)
