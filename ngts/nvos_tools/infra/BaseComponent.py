import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_constants.constants_nvos import OutputFormat


class BaseComponent:
    parent_obj = None
    api_obj = None
    _resource_path = ''

    def __init__(self, parent=None, api=None, path=''):
        self.parent_obj = parent
        self.api_obj = api
        self._resource_path = path

    def get_resource_path(self):
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self._resource_path)

    def show(self, op_param="", output_format=OutputFormat.json):
        with allure.step('Execute show for {}'.format(self.get_resource_path())):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show, TestToolkit.engines.dut,
                                                   self.get_resource_path(), op_param,
                                                   output_format).get_returned_value()

    def _set(self, param_name, param_value, expected_str=''):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].set, expected_str,
                                                            TestToolkit.engines.dut, self.get_resource_path(),
                                                            param_name, param_value)

    def set(self, op_param_name="", op_param_value={}, expected_str=''):
        with allure.step('Execute set for {resource_path}'.format(resource_path=self.get_resource_path())):

            if op_param_name:
                if isinstance(op_param_value, dict):
                    if TestToolkit.tested_api == ApiType.OPENAPI:
                        return self._set(op_param_name, op_param_value, expected_str)
                    else:
                        output = ''
                        for param_name, param_value in op_param_value.items():
                            res = self._set(param_name, param_value, expected_str)
                            output = output + "\n" + res
                        return output

                elif isinstance(op_param_value, str) or isinstance(op_param_value, int):
                    if TestToolkit.tested_api == ApiType.OPENAPI:
                        value = {op_param_name: op_param_value}
                        return self._set(self._resource_path.replace("/", ""), value, expected_str)
                    else:
                        return self._set(op_param_name, op_param_value, expected_str)
            else:
                raise Exception("Invalid param name or value")

    def unset(self, op_param="", expected_str=""):
        with allure.step('Execute unset {op_param} for {resource_path}'.format(op_param=op_param,
                                                                               resource_path=self.get_resource_path())):
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].unset, expected_str,
                                                                TestToolkit.engines.dut, self.get_resource_path(), op_param)
