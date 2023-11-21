from ngts.nvos_tools.infra.BaseComponent import BaseComponent
import logging

logger = logging.getLogger()


class Ip(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/ip')
        self.address = BaseComponent(self, path='/address')
        self.gateway = BaseComponent(self, path='/gateway')
        self.dhcp_client = BaseComponent(self, path='/dhcp-client')
        self.dhcp_client6 = BaseComponent(self, path='/dhcp-client6')
