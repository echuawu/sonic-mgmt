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
        """nv action install platform transceiver firmware files <file-name> """
        return self.action(ActionConsts.RESET, transceiver_name, expected_output=expected_str)

    def action_install(self, transceiver_name, file_name, expected_str="", dut_engine=None):
        """nv action install platform transceiver firmware files <file-name> """
        return self.action(ActionConsts.INSTALL, transceiver_name + ' firmware files ' + file_name, expected_output=expected_str)
