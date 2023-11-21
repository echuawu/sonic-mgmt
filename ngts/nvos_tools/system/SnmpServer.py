from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class SnmpServer(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/snmp-server')
        self.listening_address = BaseComponent(self, path='/listening-address')
        self.readonly_community = BaseComponent(self, path='/readonly-community')
