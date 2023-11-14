from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Radius(BaseComponent):
    def __init__(self, parent_obj=None):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/radius'
        self.hostname = RadiusHostname(self)
        self.parent_obj = parent_obj


class RadiusHostname(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/hostname'
        self.parent_obj = parent_obj

    def set_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.set("priority", priority, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_password(self, hostname, password, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.set("secret", password, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_auth_port(self, hostname, auth_port, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.set("port", auth_port, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_auth_type(self, hostname, auth_type, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.set("auth-type", auth_type, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def set_timeout(self, hostname, timeout, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.set("timeout", timeout, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)

    def show_hostname(self, hostname):
        radius_hostname = RadiusHostnameResource(self, hostname_id=hostname)
        return radius_hostname.show()


class RadiusHostnameResource(BaseComponent):
    def __init__(self, parent_obj, hostname_id):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{id}'.format(id=hostname_id)
        self.parent_obj = parent_obj
