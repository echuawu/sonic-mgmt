import logging
from typing import Dict

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DefaultDict import DefaultDict
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


class Files(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/files')
        self.file_name: Dict[str, File] = DefaultDict(lambda file_name: File(self, filename=file_name))

    def show_log_files(self, log_type='', param='', exit_cmd='', dut_engine=None):
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        with allure.step('Execute show for log file'):
            return SendCommandTool.execute_command(self._cli_wrapper.show_log, engine, log_type, param,
                                                   exit_cmd).get_returned_value()

    def get_files(self, dut_engine=None):
        with allure.step("Get files"):
            files = OutputParsingTool.parse_json_str_to_dictionary(
                self.show(dut_engine=dut_engine)).get_returned_value()
            return files

    def verify_show_files_output(self, expected_files=[], unexpected_files=[], dut_engine=None):
        with allure.step("Verify files are as expected"):
            files = self.get_files(dut_engine=dut_engine)
            for file in expected_files:
                assert file in files, "File: {} is not in the files output: {}".format(file, files)
            for file in unexpected_files:
                assert file not in files, "File: {} is in the files output {}".format(file, files)

    def delete_files(self, files_to_delete=[], expected_str='', engine=None):
        with allure.step("Delete files"):
            logging.info("Delete files: {}".format(files_to_delete))
            for file in files_to_delete:
                self.file_name[file].action_delete(expected_str, dut_engine=engine)


class File(BaseComponent):
    def __init__(self, parent=None, filename=''):
        super().__init__(parent=parent, path=f'/{filename}' if filename else '')
        self.file_name = filename

    def show_file(self, exit_cmd='', dut_engine=None) -> bool:
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        with allure.step(f'Execute show for file and exit cmd {exit_cmd}'):
            return SendCommandTool.execute_command(self._cli_wrapper.show_file, engine, self.file_name,
                                                   exit_cmd).get_returned_value()

    def action_upload(self, upload_path, expected_str="", dut_engine=None, should_succeed=True) -> bool:
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        device = TestToolkit.devices.dut
        resource_path = self.get_resource_path()
        with allure.step(f"Upload file {resource_path} to '{upload_path}'"):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action, expected_str,
                                                                engine, device, 'upload', resource_path,
                                                                upload_path).get_returned_value(should_succeed)

    def action_delete(self, expected_str="", dut_engine=None, should_succeed=True) -> bool:
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        device = TestToolkit.devices.dut
        resource_path = self.get_resource_path()
        with allure.step(f"Delete file: {resource_path}"):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action, expected_str,
                                                                engine, device, 'delete',
                                                                resource_path).get_returned_value(should_succeed)

    def action_rename(self, new_name, expected_str="", rewrite_file_name=True, dut_engine=None, should_succeed=True
                      ) -> bool:
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        device = TestToolkit.devices.dut
        resource_path = self.get_resource_path()
        with allure.step(f"Rename file: {resource_path} to: {new_name}"):
            result = SendCommandTool.execute_command_expected_str(self._cli_wrapper.action, expected_str, engine,
                                                                  device, 'rename', resource_path, new_name
                                                                  ).get_returned_value(should_succeed)
            if result and rewrite_file_name:
                parent: Files = self.parent_obj
                if self.file_name in parent.file_name:
                    del parent.file_name[self.file_name]
                parent.file_name[new_name] = self
                self.file_name = new_name
                self._resource_path = f'/{new_name}'
            return result

    def action_file_install(self, expected_str="", op_param="force", dut_engine=None) -> ResultObj:
        engine = dut_engine if dut_engine else TestToolkit.engines.dut
        device = TestToolkit.devices.dut
        resource_path = self.get_resource_path()
        with allure.step(f"Install file: {resource_path}"):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action, expected_str,
                                                                engine, device, 'install', resource_path, op_param)

    def action_file_install_with_reboot(self, expected_str="", op_param="force", engine=None, device=None,
                                        recovery_engine=None) -> ResultObj:
        engine = engine if engine else TestToolkit.engines.dut
        device = device if device else TestToolkit.devices.dut
        resource_path = self.get_resource_path()
        with allure.step(f"Install file: {resource_path}"):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action_install_image_with_reboot,
                                                                expected_str, engine, device, 'install',
                                                                resource_path, op_param, recovery_engine)

    def rename_and_verify(self, new_name, expected_str="", dut_engine=None):
        original_name = self.file_name
        self.action_rename(new_name, expected_str, dut_engine=dut_engine)
        self.parent_obj.verify_show_files_output(expected_files=[new_name], unexpected_files=[original_name],
                                                 dut_engine=dut_engine)
