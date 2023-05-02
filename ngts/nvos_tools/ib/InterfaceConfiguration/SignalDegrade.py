import allure
import logging
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import IbConsts


class SignalDegrade(BaseComponent):
    def __init__(self, port_obj):
        self.api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}
        self._resource_path = '/signal-degrade'
        self.parent_obj = port_obj

    def recover(self):
        with allure.step("Recover port {} after signal degrade action".format(self.parent_obj.name)):
            logging.info("Recover port {} after signal degrade action".format(self.parent_obj.name))
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_recover,
                                            TestToolkit.engines.dut, self.parent_obj.name,
                                            IbConsts.SIGNAL_DEGRADE).verify_result()
