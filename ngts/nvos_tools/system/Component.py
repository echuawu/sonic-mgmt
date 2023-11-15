import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, ComponentsConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
logger = logging.getLogger()


class Component(BaseComponent):
    componentName = {}

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/component'
        self.parent_obj = parent_obj

        for name in ComponentsConsts.COMPONENTS_LIST:
            self.componentName.update({name: ComponentName(self, name)})


class ComponentName(BaseComponent):
    def __init__(self, parent_obj, component_name):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{component_name}'.format(component_name=component_name)
        self.parent_obj = parent_obj
