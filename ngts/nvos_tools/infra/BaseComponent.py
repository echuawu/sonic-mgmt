import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.constants.constants_nvos import ApiType


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

    def _set(self, param_name, param_value):
        return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].set,
                                               TestToolkit.engines.dut,
                                               self.get_resource_path(), param_name,
                                               param_value).get_returned_value()

    def set(self, op_param_name="", op_param_value={}):
        with allure.step('Execute set for {resource_path}'.format(resource_path=self.get_resource_path())):

            if op_param_name:
                if isinstance(op_param_value, dict):
                    if TestToolkit.tested_api == ApiType.OPENAPI:
                        return self._set(op_param_name, op_param_value)
                    else:
                        output = ''
                        for param_name, param_value in op_param_value.items():
                            res = self._set(param_name, param_value)
                            output = output + "\n" + res
                        return output

                elif isinstance(op_param_value, str):
                    if TestToolkit.tested_api == ApiType.OPENAPI:
                        value = {op_param_name: op_param_value}
                        return self._set(self._resource_path.replace("/", ""), value)
                    else:
                        return self._set(op_param_name, op_param_value)
            else:
                raise Exception("Invalid param name or value")

    def unset(self, op_param=""):
        with allure.step('Execute unset for {resource_path}'.format(resource_path=self.get_resource_path())):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].unset, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param).get_returned_value()
