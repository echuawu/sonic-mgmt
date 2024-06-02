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
            self.neighbor_ids: Dict[str, LldpInterface.NeighborId] = {}

        def show_neighbor_id(self, engine, neighbor_id):
            if neighbor_id not in self.neighbor_ids:
                self.neighbor_ids[neighbor_id] = LldpInterface.NeighborId(neighbor_id)
            return self.neighbor_ids[neighbor_id].show(dut_engine=engine)

    class NeighborId(BaseComponent):
        def __init__(self, neighbor_id, parent_obj=None):
            super().__init__(parent=parent_obj, path=f'/{neighbor_id}')
