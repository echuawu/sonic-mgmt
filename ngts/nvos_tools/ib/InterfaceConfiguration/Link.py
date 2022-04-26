from .ConfigurationBase import ConfigurationBase
from .nvos_consts import IbInterfaceConsts
from .LinkBase import Speed, State, Lanes, Mtu, IbSpeed, OpVls, LinkBase
from .Stats import Stats
from .IbInterfaceDecorators import *
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
import allure


class Link(ConfigurationBase):
    logical_port_state = None
    physical_port_state = None
    state = None
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

        Link.logical_port_state = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_LOGICAL_PORT_STATE,
                                           description='The state shows if the HCA port is up, ' +
                                                       'and if it\'s been discovered by the subnet manager',
                                           field_name_in_db={},
                                           output_hierarchy="{level1} {level2}".format(
                                               level1=IbInterfaceConsts.LINK,
                                               level2=IbInterfaceConsts.LINK_LOGICAL_PORT_STATE))

        Link.physical_port_state = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE,
                                            description="The state of the cable",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                        level1=IbInterfaceConsts.LINK,
                                                        level2=IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE))

        Link.state = State(port_obj=port_obj)

        Link.breakout = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_BREAKOUT,
                                 description="sub-divide or disable ports (only valid on plug interfaces)",
                                 field_name_in_db={},
                                 output_hierarchy="{level1} {level2}".format(
                                     level1=IbInterfaceConsts.LINK,
                                     level2=IbInterfaceConsts.LINK_BREAKOUT))

        Link.ib_speed = IbSpeed(port_obj=port_obj)

        Link.supported_ib_speeds = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_IB_SPEEDS,
                                            description="interface infiniband negotiation speeds",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                level1=IbInterfaceConsts.LINK,
                                                level2=IbInterfaceConsts.LINK_SUPPORTED_IB_SPEEDS))

        Link.speed = Speed(port_obj=port_obj)

        Link.supported_speeds = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_SPEEDS,
                                         description="interface negotiation speeds",
                                         field_name_in_db={},
                                         output_hierarchy="{level1} {level2}".format(
                                             level1=IbInterfaceConsts.LINK,
                                             level2=IbInterfaceConsts.LINK_SUPPORTED_SPEEDS))

        Link.supported_lanes = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_SUPPORTED_LANES,
                                        description="interface configured lanes",
                                        field_name_in_db={},
                                        output_hierarchy="{level1} {level2}".format(
                                            level1=IbInterfaceConsts.LINK,
                                            level2=IbInterfaceConsts.LINK_SUPPORTED_LANES))

        Link.lanes = Lanes(port_obj=port_obj)

        Link.max_supported_mtu = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_MAX_SUPPORTED_MTU,
                                          description="interface max mtu",
                                          field_name_in_db={},
                                          output_hierarchy="{level1} {level2}".format(
                                              level1=IbInterfaceConsts.LINK,
                                              level2=IbInterfaceConsts.LINK_MAX_SUPPORTED_MTU))

        Link.mtu = Mtu(port_obj=port_obj)

        Link.vl_admin_capabilities = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_VL_ADMIN_CAPABILITIES,
                                              description="interface configured VL",
                                              field_name_in_db={},
                                              output_hierarchy="{level1} {level2}".format(
                                                  level1=IbInterfaceConsts.LINK,
                                                  level2=IbInterfaceConsts.LINK_VL_ADMIN_CAPABILITIES))

        Link.operational_vls = OpVls(port_obj=port_obj)

        Link.ib_subnet = LinkBase(port_obj=port_obj, label=IbInterfaceConsts.LINK_IB_SUBNET,
                                  description="interface infiniband subnet",
                                  field_name_in_db={},
                                  output_hierarchy="{level1} {level2}".format(
                                      level1=IbInterfaceConsts.LINK,
                                      level2=IbInterfaceConsts.LINK_IB_SUBNET))

        Link.stats = Stats(port_obj=port_obj)

    def show_interface_link(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface link'):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(dut_engine,
                                                   ApiObject[TestToolkit.api_show].show_interface,
                                                   '',
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()
