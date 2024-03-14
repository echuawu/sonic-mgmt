import logging

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Asic import Asic

logger = logging.getLogger()


class Firmware(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/firmware')
        self.asic = Asic(self)
