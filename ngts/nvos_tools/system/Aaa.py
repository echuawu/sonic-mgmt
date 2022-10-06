import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.User import User
from ngts.nvos_tools.system.Role import Role
from ngts.nvos_constants.constants_nvos import ApiType


class Aaa(BaseComponent):

    def __init__(self, parent_obj=None, username='admin'):
        self.user = User(self, username)
        self.role = Role(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/aaa'
        self.parent_obj = parent_obj
