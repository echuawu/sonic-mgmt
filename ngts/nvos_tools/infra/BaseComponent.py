import logging

import allure

from ngts.nvos_constants.constants_nvos import ApiType, ConfState
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool


class BaseComponent:
    parent_obj = None
    api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
    _resource_path = ''

    def __init__(self, parent=None, api=None, path='', force_api=None):
        self.parent_obj = parent
        if self.parent_obj and not api:
            self.api_obj = self.parent_obj.api_obj
        else:
            self.api_obj = api
        self._resource_path = path
        assert force_api in ApiType.ALL_TYPES + [
            None], f'Argument "force_api" must be in {ApiType.ALL_TYPES + [None]}. Given: {force_api}'

        if force_api or not self.parent_obj:
            self._force_api = force_api
        else:
            self._force_api = self.parent_obj._force_api

    @property
    def _api_to_use(self):
        return self._force_api if self._force_api else TestToolkit.tested_api

    @property
    def _cli_wrapper(self):
        return self.api_obj[self._api_to_use]

    @property
    def _general_cli_wrapper(self):
        return TestToolkit.GeneralApi[self._api_to_use]

    def get_resource_path(self):
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self._resource_path)

    def show(self, op_param="", output_format=OutputFormat.json, dut_engine=None, should_succeed=True,
             rev=ConfState.OPERATIONAL):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        with allure.step('Execute show for {}'.format(self.get_resource_path())):
            if TestToolkit.tested_api == ApiType.OPENAPI:
                op_param = op_param.replace('/', "%2F").replace(' ', "/")
            if rev and rev != ConfState.OPERATIONAL:
                op_param += ('?rev=' + rev) if TestToolkit.tested_api == ApiType.OPENAPI else f' --{rev}'
            return SendCommandTool.execute_command(self._cli_wrapper.show, dut_engine,
                                                   self.get_resource_path(), op_param,
                                                   output_format).get_returned_value(should_succeed=should_succeed)

    def parse_show(self, op_param="", dut_engine=None, should_succeed=True):
        output = self.show(op_param, OutputFormat.json, dut_engine, should_succeed)
        return OutputParsingTool.parse_json_str_to_dictionary(output).returned_value

    def _set(self, param_name, param_value, expected_str='', apply=False, ask_for_confirmation=False, dut_engine=None):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        result_obj = SendCommandTool.execute_command_expected_str(self._cli_wrapper.set,
                                                                  expected_str, dut_engine,
                                                                  self.get_resource_path(), param_name, param_value)
        if result_obj.result and apply:
            with allure.step("Applying set configuration"):
                result_obj = SendCommandTool.execute_command(self._general_cli_wrapper.apply_config, dut_engine,
                                                             ask_for_confirmation)
        return result_obj

    def set(self, op_param_name="", op_param_value={}, expected_str='', apply=False, ask_for_confirmation=False,
            dut_engine=None):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut
        with allure.step('Execute set for {resource_path}'.format(resource_path=self.get_resource_path())):
            if op_param_name:
                if TestToolkit.tested_api == ApiType.OPENAPI:
                    if isinstance(op_param_value, str):
                        op_param_value = op_param_value.replace('"', '')
                    value = {op_param_name: op_param_value}
                    return self._set('', value, expected_str, apply, ask_for_confirmation, dut_engine)
                else:
                    if op_param_value == {}:
                        op_param_value = op_param_name
                        op_param_name = ''
                        return self._set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation,
                                         dut_engine)
                    elif isinstance(op_param_value, dict):
                        output = ''
                        for param_name, param_value in op_param_value.items():
                            res = self._set(param_name, param_value, expected_str, apply, ask_for_confirmation,
                                            dut_engine)
                            output = output + "\n" + res
                        return output
                    elif isinstance(op_param_value, str) or isinstance(op_param_value, int):
                        return self._set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation,
                                         dut_engine)
            else:
                logging.info('Run set with no params')
                op_param_value = '' if TestToolkit.tested_api == ApiType.NVUE else {}
                return self._set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation,
                                 dut_engine)

    def unset(self, op_param="", expected_str="", apply=False, ask_for_confirmation=False, dut_engine=None):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        with allure.step('Execute unset {op_param} for {resource_path}'.format(op_param=op_param,
                                                                               resource_path=self.get_resource_path())):
            result_obj = SendCommandTool.execute_command_expected_str(self._cli_wrapper.unset,
                                                                      expected_str, dut_engine,
                                                                      self.get_resource_path(), op_param)
        if result_obj.result and apply:
            with allure.step("Applying unset configuration"):
                result_obj = SendCommandTool.execute_command(self._general_cli_wrapper.apply_config, dut_engine,
                                                             ask_for_confirmation)
        return result_obj
