from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Asic(BaseComponent):
    asic_component = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/asic/{asic_component}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(asic_component=self.asic_component).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /asic/{asic_component}")

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /asic/{asic_component}")
