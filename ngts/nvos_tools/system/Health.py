import allure
import logging
import re
from retry import retry
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, HealthConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.Files import Files

logger = logging.getLogger()


class Health(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/health'
        self.parent_obj = parent_obj
        self.history = History(self)

    def show_detail(self):
        return self.show(" -w detail")

    def show_brief(self):
        return self.show(" -w brief")

    @retry(Exception, tries=12, delay=30)       # BUG 3355421 - after reboot it takes almost 5 min until the status change to OK
    def wait_until_health_status_change_after_reboot(self, expected_status):
        output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
        assert output[HealthConsts.STATUS] == expected_status


class History(Health):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/history'
        self.parent_obj = parent_obj
        self.files = Files(self)

    def show(self, param='', exit_cmd='q'):
        with allure.step('Execute nv show system health history {param} and exit cmd {exit_cmd}'.format(param=param, exit_cmd=exit_cmd)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_health_report,
                                                   TestToolkit.engines.dut, param, exit_cmd).get_returned_value()

    def show_health_report_file(self, file=HealthConsts.HEALTH_FIRST_FILE, exit_cmd='q'):
        return self.show(param="files {}".format(file), exit_cmd=exit_cmd)

    def upload_history_files(self, file_name, upload_path, expected_str=""):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                            expected_str, TestToolkit.engines.dut, 'upload',
                                                            "health history", file_name,
                                                            upload_path).get_returned_value()

    def delete_history_file(self, file, expected_str=""):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                            expected_str, TestToolkit.engines.dut, 'delete',
                                                            "health history", file).get_returned_value()

    def delete_history_files(self, files_to_delete=[], expected_str=''):
        with allure.step("Delete files"):
            logging.info("Delete files: {}".format(files_to_delete))
            for file in files_to_delete:
                self.delete_history_file(file, expected_str)

    def search_line(self, line_to_search, file_output=None):
        if not file_output:
            file_output = self.show()
        return re.findall(line_to_search, file_output)

    def get_last_status_from_health_file(self, file_output=None):
        last_status = self.search_line(HealthConsts.ADD_STATUS_TO_SUMMARY_REGEX + HealthConsts.OK, file_output)
        assert len(last_status) > 0, "Didn't find summary line in the health history file"
        last_status = last_status[-1]
        logger.info("last status line is: \n {}".format(last_status))
        return HealthConsts.NOT_OK if HealthConsts.NOT_OK in last_status else HealthConsts.OK

    @retry(Exception, tries=20, delay=30)
    def wait_until_health_history_file_rotation(self):
        line = self.search_line("health_history file deleted, creating new file")
        assert len(line) > 0
