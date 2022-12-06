import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
logger = logging.getLogger()


class Files(BaseComponent):
    file_name = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/files/{file_name}'
        self.parent_obj = parent_obj
        self.parent_type = self.get_parent_type()

    def get_resource_path(self):
        self_path = self._resource_path.format(file_name=self.file_name).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def get_parent_type(self):
        if TestToolkit.tested_api == ApiType.NVUE:
            return self.parent_obj.get_resource_path().lstrip("/")
        return self.get_resource_path()

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /files/{file_name}")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /files/{file_name}")

    def show_log_files(self, log_type='', param='', exit_cmd=''):
        with allure.step('Execute show for log file'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_log,
                                                   TestToolkit.engines.dut, log_type,
                                                   param, exit_cmd).get_returned_value()

    def action_upload(self, file_name, upload_path, expected_str=""):
        with allure.step("Upload {type} file {file} to '{path}'".format(type=self.parent_type, file=file_name,
                                                                        path=upload_path)):
            logging.info("Upload {type} file {file} to '{path}'".format(type=self.parent_type, file=file_name,
                                                                        path=upload_path))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_upload,
                                                                expected_str, TestToolkit.engines.dut, self.parent_type,
                                                                file_name, upload_path).get_returned_value()

    def action_delete(self, file, expected_str=""):
        with allure.step("Delete {parent_type} file {file}".format(parent_type=self.parent_type, file=file)):
            logging.info("Delete {parent_type} file {file}".format(parent_type=self.parent_type, file=file))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_delete,
                                                                expected_str, TestToolkit.engines.dut, self.parent_type,
                                                                file).get_returned_value()

    def action_rename(self, original_name, new_name, expected_str=""):
        with allure.step("Rename {parent_type} file {original_name}, new name: {new_name}"
                         .format(parent_type=self.parent_type, original_name=original_name, new_name=new_name)):
            logging.info("Rename {parent_type} file {original_name}, new name: {new_name}".
                         format(parent_type=self.parent_type, original_name=original_name, new_name=new_name))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_rename,
                                                                expected_str, TestToolkit.engines.dut, self.parent_type,
                                                                original_name, new_name).get_returned_value()

    def action_file_install(self, file, expected_str=""):
        with allure.step("Install {parent_type} file '{file}'".format(parent_type=self.parent_type, file=file)):
            logging.info("Trying to install {parent_type} '{file}'".format(parent_type=self.parent_type, file=file))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_install,
                                                                expected_str, TestToolkit.engines.dut, self.parent_type,
                                                                file).get_returned_value()

    def get_files(self):
        with allure.step("Get system files"):
            logging.info("Get system files")
            files = OutputParsingTool.parse_json_str_to_dictionary(self.show()).get_returned_value()
            return files

    def verify_show_files_output(self, expected_files=[], unexpected_files=[]):
        with allure.step("Verify system files are as expected"):
            logging.info("Verify system files are as expected")
            files = self.get_files()
            for file in expected_files:
                assert file in files, "File: {} is not in the files output: {}".format(file, files)
            for file in unexpected_files:
                assert file not in files, "File: {} is in the files output {}".format(file, files)

    def delete_system_files(self, files_to_delete=[], expected_str=''):
        with allure.step("Delete files"):
            logging.info("Delete files")
            for file in files_to_delete:
                self.action_delete(file, expected_str)

    def rename_and_verify(self, original_name, new_name):
        self.action_rename(original_name, new_name)
        self.verify_show_files_output(expected_files=[new_name], unexpected_files=[original_name])
