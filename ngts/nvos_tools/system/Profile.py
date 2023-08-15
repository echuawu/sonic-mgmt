import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool


class Profile(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/profile'
        self.parent_obj = parent_obj

    def action_profile_change(self, engine=None, params=""):
        with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            if not engine:
                engine = TestToolkit.engines.dut

            marker = TestToolkit.get_loganalyzer_marker(engine)

            res = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_profile_change, engine,
                                                  self.get_resource_path().replace('/profile', ' '), params)

            TestToolkit.add_loganalyzer_marker(engine, marker)

            DutUtilsTool.wait_for_nvos_to_become_functional(engine)
            return res
