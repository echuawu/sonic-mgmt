from .ConfigurationBase import ConfigurationBase
from .nvos_consts import IbInterfaceConsts
from .CmdBase import CmdBase
from .IbInterfaceDecorators import *
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
import logging

logger = logging.getLogger()


class LinkBase(ConfigurationBase):

    def __init__(self, port_obj, label, description, field_name_in_db, output_hierarchy):
        ConfigurationBase.__init__(self, port_obj, label, description, field_name_in_db, output_hierarchy)

    def _get_value(self, engine=None, renew_show_cmd_output=True):
        """
        Returns operational/applied value
        :param renew_show_cmd_output: If true - 'show' command will be executed before checking the value
                                      Else - results from the previous 'show' command will be used
        :param engine: ssh engine
        :return:
        """
        if not engine:
            engine = TestToolkit.engines.dut

        if renew_show_cmd_output:
            TestToolkit.update_port_output_dictionary(self.port_obj, engine)
        output_str = self.port_obj.show_output_dictionary[IbInterfaceConsts.LINK][self.label]
        return output_str


class LinkBaseOperational(LinkBase, CmdBase):
    def __init__(self, port_obj, label, description, field_name_in_db, output_hierarchy):
        LinkBase.__init__(self, port_obj, label, description, field_name_in_db, output_hierarchy)

    def set(self, value, dut_engine=None, apply=True):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut
        return CmdBase.set_interface(engine=dut_engine, field_name=self.label, output_hierarchy=self.output_hierarchy,
                                     value=value, apply=apply, port_name=self.port_obj.name)

    def unset(self, dut_engine=None, apply=True):
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut
        return CmdBase.unset_interface(engine=dut_engine, field_name=self.label, output_hierarchy=self.output_hierarchy,
                                       apply=apply, port_name=self.port_obj.name)


class Speed(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_SPEED,
                                     description="Link speed",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_SPEED))


class IbSpeed(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_IB_SPEED,
                                     description="interface infiniband speed",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_IB_SPEED))


class Lanes(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_LANES,
                                     description="interface lanes",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_LANES))


class Mtu(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_MTU,
                                     description="interface mtu",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_MTU))


class OpVls(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_OPERATIONAL_VLS,
                                     description="interface VLs",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_OPERATIONAL_VLS))


class State(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_STATE,
                                     description="The state of the interface",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_STATE))

    @operation_wrapper
    def show_interface_link_state(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :return: str output
        """
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        ApiObject[TestToolkit.api_show].show_interface(engine=dut_engine,
                                                       port_name=TestToolkit.tested_ports,
                                                       interface_hierarchy=self.output_hierarchy,
                                                       output_format=output_format)
