import logging
from typing import Dict

import allure

from ngts.nvos_tools.infra.DefaultDict import DefaultDict
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
logger = logging.getLogger()


class Files(BaseComponent):
    def __init__(self, parent_obj=None, path=None):
        file_path = path if path else '/files'
        BaseComponent.__init__(self, parent=parent_obj, path=file_path)
        self.file_name: Dict[str, BaseComponent] = DefaultDict(lambda file_name: BaseComponent(self, path=f'/{file_name}'))

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /files")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /files")

    def show_log_files(self, log_type='', param='', exit_cmd=''):
        with allure.step('Execute show for log file'):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_log,
                                                   TestToolkit.engines.dut, log_type,
                                                   param, exit_cmd).get_returned_value()

    def show_file(self, file='', exit_cmd=''):
        with allure.step('Execute show for {file} file and exit cmd {exit_cmd}'.
                         format(file=file, exit_cmd=exit_cmd)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_file,
                                                   TestToolkit.engines.dut, file, exit_cmd).get_returned_value()

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

    def delete_system_files(self, files_to_delete=[], expected_str='', engine=None):
        with allure.step("Delete files"):
            logging.info("Delete files: {}".format(files_to_delete))
            for file in files_to_delete:
                File(self, file).action_delete(expected_str, engine=engine)

    def action_file(self, action_str, file, remote_url=""):
        resource = self.get_resource_path() + '/' + file
        return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_files,
                                               TestToolkit.engines.dut, action_str, resource, remote_url)


class File(Files):
    def __init__(self, parent_obj=None, file_name=''):
        Files.__init__(self, parent_obj=parent_obj, path='/' + file_name)
        self.file_name = file_name

    def action_upload(self, upload_path, expected_str=""):
        resource_path = self.get_resource_path()
        with allure.step("Upload {type} file {file} to '{path}'".format(type=resource_path, file=self.file_name,
                                                                        path=upload_path)):
            logging.info("Upload {type} file {file} to '{path}'".format(type=resource_path, file=self.file_name,
                                                                        path=upload_path))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                                expected_str, TestToolkit.engines.dut, 'upload',
                                                                resource_path, upload_path).get_returned_value()

    def action_delete(self, expected_str="", engine=None):
        engine = engine if engine else TestToolkit.engines.dut
        resource_path = self.get_resource_path()
        with allure.step("Delete {resource_path} file {file}".format(resource_path=resource_path, file=self.file_name)):
            logging.info("Delete {resource_path} file {file}".format(resource_path=resource_path, file=self.file_name))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                                expected_str, engine, 'delete',
                                                                resource_path).get_returned_value()

    def action_rename(self, new_name, expected_str="", rewrite_file_name=True):
        resource_path = self.get_resource_path()
        with allure.step("Rename {resource_path} file {original_name}, new name: {new_name}"
                         .format(resource_path=resource_path, original_name=self.file_name, new_name=new_name)):
            logging.info("Rename {resource_path} file {original_name}, new name: {new_name}".
                         format(resource_path=resource_path, original_name=self.file_name, new_name=new_name))
            result = SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                                  expected_str, TestToolkit.engines.dut, 'rename',
                                                                  resource_path, new_name).get_returned_value()
            if result and rewrite_file_name:
                self.file_name = new_name
                self._resource_path = '/{file_name}'.format(file_name=self.file_name)
            return result

    def action_file_install(self, expected_str="", op_param="force"):
        resource_path = self.get_resource_path()
        with allure.step("Install {resource_path} file '{file}'".format(resource_path=resource_path, file=self.file_name)):
            logging.info("Trying to install {resource_path} '{file}'".format(resource_path=resource_path, file=self.file_name))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_files,
                                                                expected_str, TestToolkit.engines.dut, 'install',
                                                                resource_path, op_param)

    def action_file_install_with_reboot(self, expected_str="", op_param="force"):
        resource_path = self.get_resource_path()
        with allure.step("Install {resource_path} file '{file}'".format(resource_path=resource_path, file=self.file_name)):
            logging.info("Trying to install {resource_path} '{file}'".format(resource_path=resource_path, file=self.file_name))
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_install_image_with_reboot,
                                                                expected_str, TestToolkit.engines.dut, 'install',
                                                                resource_path, op_param)

    def rename_and_verify(self, new_name, expected_str=""):
        original_name = self.file_name
        self.action_rename(new_name, expected_str)
        self.parent_obj.verify_show_files_output(expected_files=[new_name], unexpected_files=[original_name])

    def rename_and_verify_firmware(self, new_name):
        original_name = self.file_name
        self.action_rename(new_name)
        self.parent_obj.verify_show_files_output(expected_files=[new_name], unexpected_files=[original_name])
