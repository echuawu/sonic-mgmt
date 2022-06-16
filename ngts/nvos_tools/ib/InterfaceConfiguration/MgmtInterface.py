from .Description import Description
from .Type import Type
from .Ip import Ip
from .IfIndex import IfIndex
from .Link import LinkMgmt
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
import allure
import logging

logger = logging.getLogger()


class MgmtInterface:
    port_obj = None
    description = None
    ip = None
    link = None
    ifindex = None
    type = None

    def __init__(self, port_obj):
        self.port_obj = port_obj
        self.description = Description(self.port_obj)
        self.type = Type(self.port_obj)
        self.ifindex = IfIndex(self.port_obj)
        self.ip = Ip(self.port_obj)
        self.link = LinkMgmt(self.port_obj)

    def show(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface counters
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface stats for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, self.port_obj.name, output_format).get_returned_value()
