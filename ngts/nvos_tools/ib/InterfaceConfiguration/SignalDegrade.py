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
        BaseComponent.__init__(self, parent=port_obj,
                               api={ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli},
                               path="{}/signal-degrade".format(port_obj.name))

    def show(self, op_param="", output_format=OutputFormat.json):
        with allure.step('Execute show for interface {} signal degrade'.format(self.parent_obj.name)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_interface,
                                                   TestToolkit.engines.dut, self.parent_obj.name,
                                                   IbConsts.SIGNAL_DEGRADE, output_format).get_returned_value()

    def set(self, state="", action="", apply=True):
        with allure.step('Set interface {} signal-degrade state={}, action={}'.format(self.parent_obj.name,
                                                                                      state, action)):
            if state:
                logging.info("Setting state to {}".format(state))
                SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set_interface,
                                                TestToolkit.engines.dut, self.parent_obj.name,
                                                IbConsts.SIGNAL_DEGRADE, IbConsts.SIGNAL_DEGRADE_STATE,
                                                state).verify_result()

            if action:
                logging.info("Setting action to {}".format(action))
                SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set_interface,
                                                TestToolkit.engines.dut, self.parent_obj.name,
                                                IbConsts.SIGNAL_DEGRADE, IbConsts.SIGNAL_DEGRADE_ACTION,
                                                action).verify_result()

            if apply:
                logging.info("Applying configuration")
                SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                TestToolkit.engines.dut, True).verify_result()

    def unset(self, comp="", apply=True):
        with allure.step('Unset interface {} signal-degrade {}'.format(self.parent_obj.name, comp)):

            logging.info("Un-setting signal degrade {}".format(comp))
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset_interface,
                                            TestToolkit.engines.dut, self.parent_obj.name,
                                            comp).verify_result()

            if apply:
                logging.info("Applying configuration")
                SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                TestToolkit.engines.dut, True).verify_result()

    def recover(self):
        with allure.step("Recover port {} after signal degrade action".format(self.parent_obj.name)):
            logging.info("Recover port {} after signal degrade action".format(self.parent_obj.name))
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_recover,
                                            TestToolkit.engines.dut, self.parent_obj.name,
                                            IbConsts.SIGNAL_DEGRADE).verify_result()
