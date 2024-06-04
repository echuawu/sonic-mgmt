from typing import Dict

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DefaultDict import DefaultDict


class LldpInterface(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/lldp')
        self.neighbor = LldpInterface.Neighbor(self)

    class Neighbor(BaseComponent):
        def __init__(self, parent_obj=None):
            super().__init__(parent=parent_obj, path=f'/neighbor')

        def show_neighbor_id(self, engine, neighbor_id):
            return self.show(neighbor_id)
