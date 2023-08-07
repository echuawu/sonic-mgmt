from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tools.test_utils import allure_utils as allure


class Restrictions(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/restrictions'
        self.parent_obj = parent_obj

    def action_clear(self, user_to_clear=''):
        rsrc_path = self.get_resource_path()

        with allure.step(f'Execute action clear for {rsrc_path} \tParam: "{user_to_clear}"'):

            if TestToolkit.tested_api == ApiType.OPENAPI:  # todo: find out about the OM of action command
                if user_to_clear:
                    params = {'user': user_to_clear}
                else:
                    params = {}
            else:
                params = f'user {user_to_clear}' if user_to_clear else ''

            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_clear,
                                                   TestToolkit.engines.dut, rsrc_path, params)
