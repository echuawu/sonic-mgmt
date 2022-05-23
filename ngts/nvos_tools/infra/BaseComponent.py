import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool


class BaseComponent:
    parent_obj = None
    api_obj = None
    _resource_path = ''

    def __init__(self):
        pass

    def get_resource_path(self):
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self._resource_path)

    def show(self, op_param=""):
        with allure.step('Execute show for {}'.format(self.get_resource_path())):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param).get_returned_value()

    def set(self, op_param=""):
        with allure.step('Execute set for {resource_path}'.format(resource_path=self.get_resource_path())):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param).get_returned_value()

    def unset(self, op_param=""):
        with allure.step('Execute unset for {resource_path}'.format(resource_path=self.get_resource_path())):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param).get_returned_value()
