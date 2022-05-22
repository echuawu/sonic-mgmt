import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool


class BaseComponent:
    api_obj = None
    resource_path = ''

    def __init__(self):
        pass

    def show(self, op_param=""):
        with allure.step('Execute show for {}'.format(self.resource_path)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show, TestToolkit.engines.dut,
                                                   self.resource_path, op_param).get_returned_value()
