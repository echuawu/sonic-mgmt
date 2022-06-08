import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Password_hardening import Password_hardening


class Security(BaseComponent):
    password_hardening = None

    def __init__(self, parent_obj):
        self.password_hardening = Password_hardening(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/security'
        self.parent_obj = parent_obj

    def unset(self, op_param=""): 
        raise Exception("unset is not implemented for /security")
