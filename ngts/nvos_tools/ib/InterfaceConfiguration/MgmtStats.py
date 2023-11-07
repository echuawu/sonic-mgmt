from ngts.nvos_tools.ib.InterfaceConfiguration.Stats import *
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType


class MgmtStats(BaseComponent):

    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/counters'
        self.parent_obj = port_obj

    def clear_stats(self, dut_engine=None, fae_param=""):
        """
        Clears interface counters
        """
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        with allure.step('Clear stats for {port_name}'.format(port_name=self.parent_obj.parent_obj.parent_obj.name)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].clear_stats,
                                                   dut_engine, self.parent_obj.parent_obj.parent_obj.name, fae_param)
