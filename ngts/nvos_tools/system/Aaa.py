from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Authentication import Authentication
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.system.Radius import Radius
from ngts.nvos_tools.system.Ldap import Ldap


class Aaa(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/aaa')
        self.user = User(self)
        self.role = BaseComponent(self, path='/role')
        self.radius = Radius(self)
        self.ldap = Ldap(self)
        self.tacacs = RemoteAaaResource(parent_obj=self, resource_name='/tacacs')
        self.authentication = Authentication(self)
