from typing import Dict

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DefaultDict import DefaultDict


class LldpInterface(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/lldp')
        self.neighbor = Neighbor(self)


class Neighbor(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path=f'/neighbor')
        self.neighbor_id: Dict[str, NeighborId] = DefaultDict(
            lambda neighbor_id: NeighborId(self, neighbor_id))


class NeighborId(BaseComponent):
    def __init__(self, parent_obj, neighbor_id):
        BaseComponent.__init__(self, parent=parent_obj, path='/' + neighbor_id)
