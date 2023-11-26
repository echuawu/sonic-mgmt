import logging
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime

logger = logging.getLogger()


class TechSupport(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/tech-support/files')

    def action_upload(self, upload_path, file_name):
        with allure.step("Upload techsupport {file} to '{path}".format(file=file_name, path=upload_path)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload, TestToolkit.engines.dut,
                                                   self.get_resource_path(), file_name, upload_path)

    def action_delete(self, file_name):
        with allure.step("Delete tech-support: {}".format(file_name)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_delete, TestToolkit.engines.dut,
                                                   self.get_resource_path(), file_name)

    def action_generate(self, engine="", option="", since_time="", test_name=''):
        """
        in the future the command will be nv action generate system tech-support (without files)
        changes to do :
            update self._resource_path in the init method
            remove self.get_resource_path().replace('/files', ' ') in this method
        """
        with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            if not engine:
                engine = TestToolkit.engines.dut

            cmd_out, duration = OperationTime.save_duration('generate tech-support', option, test_name, SendCommandTool.execute_command,
                                                            NvueSystemCli.action_generate_techsupport, engine,
                                                            self.get_resource_path().replace('/files', ' '), option, since_time)
            return TechSupport.get_techsupport_folder_name(cmd_out)

    @staticmethod
    def get_techsupport_folder_name(techsupport_res):
        if 'Command failed' in techsupport_res.info:
            return techsupport_res.info
        techsupport_res_list = techsupport_res.returned_value.split('\n')
        files_name = "".join([name for name in techsupport_res_list if '.tar.gz' in name])
        files_name = files_name.replace('Generated tech-support', '').split(' ')
        return SystemConsts.TECHSUPPORT_FILES_PATH + files_name[-1]

    @staticmethod
    def get_techsupport_files_list(engine, tech_support_folder, tech_folder):
        """
        :param engine: engine
        :param techsupport: the techsupport .tar.gz name
        :return: list of the required dump files in the tech-support
        """
        with allure.step('Get all tech-support dump files'):
            engine.run_cmd('sudo tar -xf ' + tech_support_folder + ' -C /host/dump')
            full_path = tech_support_folder.replace('.tar.gz', "")
            output = engine.run_cmd('sudo ls ' + full_path + '/' + tech_folder)
            engine.run_cmd('sudo rm -rf ' + full_path)
            return output.split()
