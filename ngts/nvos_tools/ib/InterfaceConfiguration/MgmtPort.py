from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtInterface import *
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import *
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool

import allure

logger = logging.getLogger()


class MgmtPort:
    name = ""
    show_output_dictionary = {}
    name_in_redis = ""
    interface = None
    api_obj = {ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli}

    def __init__(self, name='eth0'):
        self.name = name
        self.show_output_dictionary = None
        self.name_in_redis = ''
        self.interface = MgmtInterface(self)

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

    def show(self):
        with allure.step('Execute show for {}'.format(self.name)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].show_interface,
                                                   TestToolkit.engines.dut, self.name).get_returned_value()
