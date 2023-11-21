import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent

logger = logging.getLogger()


class PortFastRecovery(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/fast-recovery')
        self.trigger = BaseComponent(self, path='/trigger')
