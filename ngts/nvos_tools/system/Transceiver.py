import logging

from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.Files import Files
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_constants.constants_nvos import ActionConsts

logger = logging.getLogger()


class Transceiver(BaseComponent):
    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/transceiver')
        self.files = Files(self)

    def action_reset(self, transceiver_name, expected_str="", dut_engine=None):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut
        with allure.step('Trying to reset {}'.format(transceiver_name)):
            return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_reset,
                                                                expected_str, dut_engine,
                                                                self.get_resource_path(), transceiver_name).verify_result()

    def action_install(self, transceiver_name, file_name, expected_str="", dut_engine=None):
        """nv action install platform transceiver firmware files <file-name> """
        return self.action(ActionConsts.INSTALL, transceiver_name + ' files ' + file_name)
