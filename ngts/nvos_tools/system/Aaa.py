from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Authentication import Authentication
from ngts.nvos_tools.system.Tacacs import Tacacs
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.system.Radius import Radius
from ngts.nvos_tools.system.Ldap import Ldap


class Aaa(BaseComponent):
    def __init__(self, parent_obj=None, username='admin'):
        BaseComponent.__init__(self, parent=parent_obj, path='/aaa')
        self.user = User(self, username)
        self.role = BaseComponent(self, path='/role')
        self.radius = Radius(self)
        self.ldap = Ldap(self)
        self.authentication = Authentication(self)
        self.tacacs = Tacacs(self)
