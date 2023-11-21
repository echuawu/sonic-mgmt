from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType


class Interface(BaseComponent):
    def __init__(self):
        BaseComponent.__init__(self, api={ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli},
                               path='/interface')
