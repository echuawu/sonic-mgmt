import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
logger = logging.getLogger()


class Files(BaseComponent):
    file_name = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/files/{file_name}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(file_name=self.file_name).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /files/{file_name}")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /files/{file_name}")

    def show_log_files(self, log_type='', param='', exit_cmd=''):
        with allure.step('Execute show for log file'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_log,
                                                   TestToolkit.engines.dut, log_type,
                                                   param, exit_cmd).get_returned_value()

    def action_upload(self, log_file_type="", logging_file="", upload_path=""):
        with allure.step("Upload {type}log file {file} to '{path}'".format(type=log_file_type,
                                                                           file=log_file_type,
                                                                           path=upload_path)):
            logging.info("Upload {type}log file {file} to '{path}'".format(type=log_file_type,
                                                                           file=log_file_type,
                                                                           path=upload_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload,
                                                   TestToolkit.engines.dut, log_file_type,
                                                   logging_file, upload_path).get_returned_value()

    def action_delete(self, log_file_type="", logging_file=""):
        with allure.step("Delete {type}log file {file}".format(type=log_file_type, file=logging_file)):
            logging.info("Delete {type}log file {file}".format(type=log_file_type, file=logging_file))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_delete,
                                                   TestToolkit.engines.dut, log_file_type,
                                                   logging_file).get_returned_value()
