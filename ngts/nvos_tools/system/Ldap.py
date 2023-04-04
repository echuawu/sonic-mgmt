from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Ldap(BaseComponent):
    def __init__(self, parent_obj=None):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/ldap'
        self.parent_obj = parent_obj
        self.hostname = LdapHostname(self)

    def set_hostname(self, hostname, apply=False, ask_for_confirmation=False):
        return self.set("hostname", hostname, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_hostname_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} priority ".format(hostname), priority, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_bind_dn(self, user, apply=False, ask_for_confirmation=False):
        return self.set("bind-dn", user, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_bind_password(self, password, apply=False, ask_for_confirmation=False):
        return self.set("password", password, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_port(self, port, apply=False, ask_for_confirmation=False):
        return self.set("auth-port", int(port), apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_base_dn(self, base, apply=False, ask_for_confirmation=False):
        return self.set("base-dn", base, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_login_attribute(self, login_attr, apply=False, ask_for_confirmation=False):
        return self.set("login-attribute", login_attr, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_group_attribute(self, group_attr, apply=False, ask_for_confirmation=False):
        return self.set("group-attribute", group_attr, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_scope(self, scope, apply=False, ask_for_confirmation=False):
        return self.set("scope", scope, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_version(self, version, apply=False, ask_for_confirmation=False):
        return self.set("version", int(version), apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_timeout_bind(self, timeout, apply=False, ask_for_confirmation=False):
        return self.set("timeout-bind", int(timeout), apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_timeout_search(self, timeout, apply=False, ask_for_confirmation=False):
        return self.set("timeout-search", int(timeout), apply=apply, ask_for_confirmation=ask_for_confirmation)


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
