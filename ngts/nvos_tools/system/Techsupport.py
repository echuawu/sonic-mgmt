import logging
import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


class TechSupport(BaseComponent):
    api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/tech-support/files'
        self.parent_obj = parent_obj

    def action_upload(self, upload_path, file_name):
        with allure.step("Upload techsupport {file} to '{path}".format(file=file_name, path=upload_path)):
            logging.info("Upload techsupport {file} to '{path}".format(file=file_name, path=upload_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload, TestToolkit.engines.dut,
                                                   self.get_resource_path(), file_name, upload_path)

    def action_delete(self, file_name):
        with allure.step("Delete tech-support: {}".format(file_name)):
            logging.info("Delete tech-support: {}".format(file_name))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_delete, TestToolkit.engines.dut,
                                                   self.get_resource_path(), file_name)

    def action_generate(self, engine="", option="", time=""):
        """
        in the future the command will be nv action generate system tech-support (without files)
        changes to do :
            update self._resource_path in the init method
            remove self.get_resource_path().replace('/files', ' ') in this method
        """
        with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            if not engine:
                engine = TestToolkit.engines.dut

            cmd_out = SendCommandTool.execute_command(NvueSystemCli.action_generate_techsupport, engine, self.get_resource_path().replace('/files', ' '), option, time)
            result = TechSupport.get_techsupport_folder_name(cmd_out)
            return result

    @staticmethod
    def get_techsupport_folder_name(techsupport_res):
        if 'Command failed' in techsupport_res.info:
            return techsupport_res.info
        techsupport_folder = techsupport_res.returned_value.split('\n')
        file_name = "".join([name for name in techsupport_folder if '.tar.gz' in name])
        return file_name.replace('Generated tech-support ', '').replace(' ', '')

    @staticmethod
    def get_techsupport_log_files_names(engine, techsupport):
        """
        :param engine: engine
        :param techsupport: the techsupport .tar.gz name
        :return: list of the dump files in the tech-support
        """
        with allure.step('Get all tech-support dump files'):
            engine.run_cmd('sudo tar -xf ' + techsupport + ' -C /host/dump')
            folder_name = techsupport.replace('.tar.gz', "")
            output = engine.run_cmd('ls ' + folder_name + '/log')
            engine.run_cmd('sudo rm -rf ' + folder_name)
            return output.split()
