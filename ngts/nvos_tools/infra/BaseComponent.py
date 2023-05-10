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

    def _set(self, param_name, param_value, expected_str='', apply=False, ask_for_confirmation=False):
        result_obj = SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].set,
                                                                  expected_str, TestToolkit.engines.dut,
                                                                  self.get_resource_path(), param_name, param_value)
        if result_obj.result and apply:
            with allure.step("Applying set configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, TestToolkit.engines.dut,
                                                             ask_for_confirmation)
        return result_obj

    def set(self, op_param_name="", op_param_value={}, expected_str='', apply=False, ask_for_confirmation=False):
        with allure.step('Execute set for {resource_path}'.format(resource_path=self.get_resource_path())):

            if op_param_name:
                if TestToolkit.tested_api == ApiType.OPENAPI:
                    if isinstance(op_param_value, str):
                        op_param_value = op_param_value.replace('"', '')
                    value = {op_param_name: op_param_value}
                    return self._set('', value, expected_str, apply, ask_for_confirmation)
                else:
                    if op_param_value == {}:
                        op_param_value = op_param_name
                        op_param_name = ''
                        return self._set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation)
                    elif isinstance(op_param_value, dict):
                        output = ''
                        for param_name, param_value in op_param_value.items():
                            res = self._set(param_name, param_value, expected_str, apply, ask_for_confirmation)
                            output = output + "\n" + res
                        return output

                    elif isinstance(op_param_value, str) or isinstance(op_param_value, int):
                        return self._set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation)
            else:
                raise Exception("Invalid param name or value")

    def unset(self, op_param="", expected_str="", apply=False, ask_for_confirmation=False):
        with allure.step('Execute unset {op_param} for {resource_path}'.format(op_param=op_param,
                                                                               resource_path=self.get_resource_path())):
            result_obj = SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].unset,
                                                                      expected_str, TestToolkit.engines.dut,
                                                                      self.get_resource_path(), op_param)
        if result_obj.result and apply:
            with allure.step("Applying unset configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, TestToolkit.engines.dut,
                                                             ask_for_confirmation)
        return result_obj
