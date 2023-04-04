from .LinkBase import *
from .Stats import Stats
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtStats import MgmtStats
import allure


class Link(ConfigurationBase):
    logical_port_state = None
    physical_port_state = None
    state = None
    diagnostics = None
    breakout = None
    ib_speed = None
    supported_ib_speeds = None
    speed = None
    supported_speeds = None
    lanes = None
    supported_lanes = None
    max_supported_mtu = None
    mtu = None
    vl_admin_capabilities = None
    operational_vls = None
    ib_subnet = None
    stats = None

    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.LINK,
                                   description="",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.LINK)

        self.logical_port_state = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_LOGICAL_PORT_STATE,
                                           description='The state shows if the HCA port is up, ' +
                                                       'and if it\'s been discovered by the subnet manager',
                                           field_name_in_db={},
                                           output_hierarchy="{level1} {level2}".format(
                                               level1=IbInterfaceConsts.LINK,
                                               level2=IbInterfaceConsts.LINK_LOGICAL_PORT_STATE))

        self.physical_port_state = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE,
                                            description="The state of the cable",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                        level1=IbInterfaceConsts.LINK,
                                                        level2=IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE))

        self.state = State(port_obj=self.port_obj)

        self.diagnostics = Diagnostics(port_obj=self.port_obj)

        self.breakout = Breakout(port_obj=self.port_obj)

        self.ib_speed = IbSpeed(port_obj=self.port_obj)

        self.supported_ib_speeds = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_IB_SPEEDS,
                                            description="interface infiniband negotiation speeds",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                level1=IbInterfaceConsts.LINK,
                                                level2=IbInterfaceConsts.LINK_SUPPORTED_IB_SPEEDS))

        self.speed = Speed(port_obj=self.port_obj)

        self.supported_speeds = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_SPEEDS,
                                         description="interface negotiation speeds",
                                         field_name_in_db={},
                                         output_hierarchy="{level1} {level2}".format(
                                             level1=IbInterfaceConsts.LINK,
                                             level2=IbInterfaceConsts.LINK_SUPPORTED_SPEEDS))

        self.supported_lanes = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_LANES,
                                        description="interface configured lanes",
                                        field_name_in_db={},
                                        output_hierarchy="{level1} {level2}".format(
                                            level1=IbInterfaceConsts.LINK,
                                            level2=IbInterfaceConsts.LINK_SUPPORTED_LANES))

        self.lanes = Lanes(port_obj=self.port_obj)

        self.max_supported_mtu = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_MAX_SUPPORTED_MTU,
                                          description="interface max mtu",
                                          field_name_in_db={},
                                          output_hierarchy="{level1} {level2}".format(
                                              level1=IbInterfaceConsts.LINK,
                                              level2=IbInterfaceConsts.LINK_MAX_SUPPORTED_MTU))

        self.mtu = Mtu(port_obj=self.port_obj)

        self.vl_admin_capabilities = LinkBase(port_obj=self.port_obj,
                                              label=IbInterfaceConsts.LINK_VL_ADMIN_CAPABILITIES,
                                              description="interface configured VL",
                                              field_name_in_db={},
                                              output_hierarchy="{level1} {level2}".format(
                                                  level1=IbInterfaceConsts.LINK,
                                                  level2=IbInterfaceConsts.LINK_VL_ADMIN_CAPABILITIES))

        self.operational_vls = OpVls(port_obj=self.port_obj)

        self.ib_subnet = LinkBase(port_obj=self.port_obj, label=IbInterfaceConsts.LINK_IB_SUBNET,
                                  description="interface infiniband subnet",
                                  field_name_in_db={},
                                  output_hierarchy="{level1} {level2}".format(
                                      level1=IbInterfaceConsts.LINK,
                                      level2=IbInterfaceConsts.LINK_IB_SUBNET))

        self.stats = Stats(port_obj=self.port_obj)

    def show_interface_link(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface link for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()


class LinkMgmt(ConfigurationBase):
    state = None
    diagnostics = None
    speed = None
    mtu = None
    breakout = None
    stats = None
    mac = None
    duplex = None
    auto_negotiate = None

    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.LINK,
                                   description="",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.LINK)
        self.state = State(port_obj=self.port_obj)
        self.diagnostics = Diagnostics(port_obj=self.port_obj)
        self.speed = Speed(port_obj=self.port_obj)
        self.mtu = Mtu(port_obj=self.port_obj)
        self.breakout = Breakout(port_obj=self.port_obj)
        self.stats = MgmtStats(port_obj=self.port_obj)
        self.mac = Mac(port_obj=self.port_obj)
        self.duplex = Duplex(port_obj=self.port_obj)
        self.auto_negotiate = AutoNegotiate(port_obj=self.port_obj)

    def show(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface link for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()
