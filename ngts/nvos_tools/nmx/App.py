from typing import Dict

import allure
import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DefaultDict import DefaultDict
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.nmx.Loglevel import Loglevel
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_cluster_clis import NvueClusterCli
from ngts.cli_wrappers.openapi.openapi_cluster_clis import OpenApiClusterCli
from ngts.nvos_tools.nmx.Type import Type

logger = logging.getLogger()


class App(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj,
                         api={ApiType.NVUE: NvueClusterCli, ApiType.OPENAPI: OpenApiClusterCli},
                         path='/app')
        self.app_name: Dict[str, AppName] = DefaultDict(
            lambda app_name: AppName(parent=self, app_name=app_name))


class AppName(BaseComponent):
    def __init__(self, parent, app_name):
        super().__init__(parent=parent, path=f'/{app_name}')
        self.loglevel = Loglevel(self)
        self.type = Type()

    def action_start_cluster_app(self, engine=None):
        engine = engine if engine else TestToolkit.engines.dut
        with allure.step('Start App'):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action_start_cluster_app,
                                                                "Action succeeded", engine,
                                                                self.get_resource_path())

    def action_stop_cluster_app(self, engine=None):
        engine = engine if engine else TestToolkit.engines.dut
        with allure.step('Stop App'):
            return SendCommandTool.execute_command_expected_str(self._cli_wrapper.action_stop_cluster_app,
                                                                "Action succeeded", engine,
                                                                self.get_resource_path())