import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.constants.constants_nvos import ApiType


class TechSupport(BaseComponent):
    api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self._resource_path = '/tech-support/files'
        self.parent_obj = parent_obj

    def action_generate(self, option="", time=""):
        """
        in the future the command will be nv action generate system tech-support (without files)
        changes to do :
            update self._resource_path in the init method
            remove self.get_resource_path().replace('/files', ' ') in this method
        """
        with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            return TechSupport.get_techsupport_folder_name(SendCommandTool.execute_command(
                self.api_obj[TestToolkit.tested_api].action_generate, TestToolkit.engines.dut,
                self.get_resource_path().replace('/files', ' '), option, time))

    @staticmethod
    def get_techsupport_folder_name(techsupport_res):
        if 'Invalid' in techsupport_res.info:
            return techsupport_res.info
        techsupport_folder = techsupport_res.returned_value.split('\n')
        file_name = "".join([name for name in techsupport_folder if '.tar.gz' in name])
        return file_name.replace('Generated tech-support ', '').replace(' ', '')
