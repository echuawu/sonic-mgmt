import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
logger = logging.getLogger()


class Component(BaseComponent):
    component_name = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/component/{component_name}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(component_name=self.component_name).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def set_system_log_component(self, component, log_level=""):
        with allure.step("Set {component} to log level {log_level}".format(component=component, log_level=log_level)):
            logging.info("Set {component} to log level {log_level}".format(component=component, log_level=log_level))
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_set_system_log_component,
                                            TestToolkit.engines.dut, component, log_level).get_returned_value()
            TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut)

    def unset_system_log_component(self, component):
        with allure.step("Unset {component} component to default log level".format(component=component)):
            logging.info("Unset {component} component to default log level".format(component=component))
            SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_unset_system_log_component,
                                            TestToolkit.engines.dut, component).get_returned_value()
            TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut)
