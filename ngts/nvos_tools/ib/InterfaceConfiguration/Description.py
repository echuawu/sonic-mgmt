from .ConfigurationBase import ConfigurationBase
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from .nvos_consts import IbInterfaceConsts
from ngts.nvos_constants.constants_nvos import ApiType
import logging

logger = logging.getLogger()


class Description(ConfigurationBase, BaseComponent):
    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.DESCRIPTION,
                                   description="Details about the interface",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.DESCRIPTION)
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/description'
        self.parent_obj = port_obj
