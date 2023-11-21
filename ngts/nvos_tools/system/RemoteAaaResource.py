from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Hostname import Hostname


class RemoteAaaResource(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli})
        self.hostname = Hostname(self)
