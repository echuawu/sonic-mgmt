from ngts.nvos_tools.system.Accounting import Accounting
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource


class Tacacs(RemoteAaaResource):
    def __init__(self, parent_obj=None):
        super().__init__(parent_obj)
        self._resource_path = '/tacacs'
        self.accounting = Accounting(self)
