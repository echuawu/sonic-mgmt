from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource


class Ldap(RemoteAaaResource):
    def __init__(self, parent_obj=None):
        super().__init__(parent_obj)
        self._resource_path = '/ldap'
        self.ssl = Ssl(self)
        # self.hostname = LdapHostname(self)

    def set_hostname_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} priority ".format(hostname), priority, apply=apply,
                        ask_for_confirmation=ask_for_confirmation)


class LdapHostname(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/hostname'
        self.parent_obj = parent_obj

    def set_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
        ldap_hostname = LdapHostnameResource(self, hostname_id=hostname)
        return ldap_hostname.set("priority", priority, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
        ldap_hostname = LdapHostnameResource(self, hostname_id=hostname)
        return ldap_hostname.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)

    def show_hostname(self, hostname):
        ldap_hostname = LdapHostnameResource(self, hostname_id=hostname)
        return ldap_hostname.show()


class LdapHostnameResource(BaseComponent):
    def __init__(self, parent_obj, hostname_id):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{id}'.format(id=hostname_id)
        self.parent_obj = parent_obj


class Ssl(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/ssl'
        self.parent_obj = parent_obj
