from .LinkBase import *
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtStats import MgmtStats


class LinkMgmt(BaseComponent):
    state = None
    diagnostics = None
    stats = None
    counters = None
    plan_ports = None

    def __init__(self, port_obj):
        self.state = State(self)
        self.diagnostics = Diagnostics(self)
        self.stats = MgmtStats(self)
        self.counters = Counters(self)
        self.plan_ports = PlanPorts(self)
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/link'
        self.parent_obj = port_obj
