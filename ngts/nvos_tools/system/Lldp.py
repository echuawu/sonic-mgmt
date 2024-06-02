from ngts.nvos_constants.constants_nvos import NtpConsts, NvosConst, SystemConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool


class Lldp(BaseComponent):
    def __init__(self, parent_obj):
        BaseComponent.__init__(self, parent=parent_obj, path='/lldp')

    def enable_lldp(self, apply=True):
        return self.set(SystemConsts.LLDP_STATE, NvosConst.ENABLED, apply=apply)

    def disable_lldp(self, apply=True):
        return self.set(SystemConsts.LLDP_STATE, NvosConst.DISABLED, apply=apply)

    def set_interval(self, interval_val=30, apply=True):
        return self.set(SystemConsts.LLDP_INTERVAL, interval_val, apply=apply)

    def set_multiplier(self, multiplier_val=4, apply=True):
        return self.set(SystemConsts.LLDP_MULTIPLIER, multiplier_val, apply=apply)

    def parsed_show(self, engine=None):
        return OutputParsingTool.parse_json_str_to_dictionary(self.show(dut_engine=engine)).get_returned_value()
