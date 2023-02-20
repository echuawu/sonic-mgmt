from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Radius(BaseComponent):
    def __init__(self, parent_obj=None):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/radius'
        self.parent_obj = parent_obj

    def set_hostname_password(self, hostname, password, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} password".format(hostname), password, apply, ask_for_confirmation)

    def set_hostname_auth_port(self, hostname, auth_port, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} auth-port".format(hostname), auth_port, apply, ask_for_confirmation)

    def set_hostname_auth_type(self, hostname, auth_type, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} auth-type".format(hostname), auth_type, apply, ask_for_confirmation)

    def set_hostname_timeout(self, hostname, timeout, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} timeout".format(hostname), timeout, apply, ask_for_confirmation)

    def set_hostname_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
        return self.set("hostname {} priority".format(hostname), priority, apply, ask_for_confirmation)

    def show_hostname(self, hostname=''):
        return self.show("hostname {}".format(hostname))

    def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
        return self.unset("hostname {}".format(hostname), apply=apply, ask_for_confirmation=ask_for_confirmation)
