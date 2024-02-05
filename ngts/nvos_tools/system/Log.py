import logging
from typing import Dict

import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.system.Component import Component

logger = logging.getLogger()


class Log(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/log')
        self.files = Files(self)
        self.component = Component(self)
        self.rotation = BaseComponent(self, path='/rotation')

    def show_log(self, log_type='', param='', exit_cmd='', expected_str=''):
        with allure.step('Execute nv show system {type}log {param} and exit cmd {exit_cmd}'.
                         format(type=log_type, param=param, exit_cmd=exit_cmd)):
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].show_log,
                                                                expected_str, TestToolkit.engines.dut, log_type,
                                                                param, exit_cmd).get_returned_value()

    def write_to_log(self):
        with allure.step('Write content to logs'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_write_to_logs,
                                                   TestToolkit.engines.dut).get_returned_value()

    def rotate_logs(self):
        with allure.step('Rotate logs'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_rotate_logs,
                                                   TestToolkit.engines.dut).get_returned_value()

    def verify_expected_logs(self, logs_to_find, engine=None):
        """

        :param logs_to_find: list of logs to find
        :return:
        """
        with allure.step('Verify expected logs'):
            log_search_errors: Dict[str, str] = {log: f'log "{log}" was not found' for log in logs_to_find}

            log_files = OutputParsingTool.parse_json_str_to_dictionary(self.files.show()).get_returned_value().keys()
            grep_logs = '|'.join(logs_to_find)
            for log_file in log_files:
                if not log_search_errors:
                    break

                output = self.files.file_name[log_file].show(op_param=f'| grep -E "{grep_logs}"', output_format='',
                                                             dut_engine=engine)
                if output:
                    for log in logs_to_find:
                        if log in output and log in log_search_errors:
                            del log_search_errors[log]

            err = ',\n'.join(list(log_search_errors.values()))
            assert not log_search_errors, f"The following logs weren't found:\n{err}"
