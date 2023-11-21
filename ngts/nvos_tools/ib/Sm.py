import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent

logger = logging.getLogger()


class Sm(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/sm')
        self.log = BaseComponent(self, path='/log')
