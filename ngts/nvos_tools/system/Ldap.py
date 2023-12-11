from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource


class Ldap(RemoteAaaResource):

    def __init__(self, parent_obj=None):
        super().__init__(parent_obj)
        self._resource_path = '/ldap'
        self.ssl = BaseComponent(self, path='/ssl')
        self.filter = BaseComponent(self, path='/filter')
        self.map = LdapMap(self)


class LdapMap(BaseComponent):

    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/map')
        self.passwd = BaseComponent(self, path='/passwd')
        self.group = BaseComponent(self, path='/group')
        self.shadow = BaseComponent(self, path='/shadow')


# class Ldap(BaseComponent):
#     def __init__(self, parent_obj=None):
#         BaseComponent.__init__(self, parent=parent_obj, path='/ldap')
#         self.hostname = LdapHostname(self)
#         self.ssl = BaseComponent(self, path='/ssl')
#
#
# class LdapHostname(BaseComponent):
#     def __init__(self, parent_obj=None):
#         BaseComponent.__init__(self, parent=parent_obj, path='/hostname')
#
#     def set_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.set("priority", priority, apply=apply, ask_for_confirmation=ask_for_confirmation)
#
#     def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)
#
#     def show_hostname(self, hostname):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.show()
