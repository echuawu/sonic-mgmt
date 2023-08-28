import logging
from retry import retry
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.constants.constants import GnmiConsts

logger = logging.getLogger()


class Gnmi_server(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/gnmi-server'
        self.parent_obj = parent_obj

    def enable_gnmi_server(self, apply=True):
        return self.set(GnmiConsts.GNMI_STATE_FIELD, GnmiConsts.GNMI_STATE_ENABLED, apply=apply)

    def disable_gnmi_server(self, apply=True):
        return self.set(GnmiConsts.GNMI_STATE_FIELD, GnmiConsts.GNMI_STATE_DISABLED, apply=apply)

    def unset_gnmi_server(self, apply=True):
        return self.unset(apply=apply)

    def parsed_show_gnmi(self):
        return OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()

    @retry(Exception, tries=3, delay=2)
    def compare_show_gnmi_output(self, expected={GnmiConsts.GNMI_STATE_FIELD: GnmiConsts.GNMI_STATE_ENABLED,
                                                 GnmiConsts.GNMI_IS_RUNNING_FIELD: GnmiConsts.GNMI_IS_RUNNING}):
        show_output = self.parsed_show_gnmi()
        msg = ''
        for key, value in show_output.items():
            if show_output[key] != expected[key]:
                msg += f"{key} field is different than expected: \n" \
                       f"Expected: {expected[key]}, but got: {value}\n"
        assert not msg, f"The output of show gnmi-server is different than expected:\n{msg}"
