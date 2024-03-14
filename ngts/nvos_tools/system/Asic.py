import logging

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Files import Files

logger = logging.getLogger()


class Asic(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/ASIC')
        self.files = Files(self)
