from .MgmtInterface import MgmtInterface
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
import allure
import logging

logger = logging.getLogger()


class MgmtPort(BaseComponent):
    def __init__(self, name='eth0', parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}, path='')
        self.name = name
        self.show_output_dictionary = {}
        self.name_in_redis = ''
        self.interface = MgmtInterface(self, name)

    def update_output_dictionary(self):
        """
        Execute "show" command and create the output dictionary for the mgmt-port
        """
        with allure.step('Execute "show" command and create the output dictionary for {port_name}'.format(
                port_name=self.name)):
            logging.info("Updating output dictionary of '{port_name}'".format(port_name=self.name))
            self.show_output_dictionary = OutputParsingTool.parse_show_interface_output_to_dictionary(
                SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_interface,
                                                TestToolkit.engines.dut,
                                                self.name).get_returned_value()).get_returned_value()
