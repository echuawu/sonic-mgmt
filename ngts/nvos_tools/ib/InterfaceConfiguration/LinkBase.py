from .ConfigurationBase import ConfigurationBase
from .nvos_consts import IbInterfaceConsts
from .CmdBase import CmdBase
from .IbInterfaceDecorators import *
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.constants.constants_nvos import ApiType
import logging
import allure

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

    def set(self, value, dut_engine=None, apply=True, ask_for_confirmation=False):
        """
        Set current field with provided value
        :param value: value to set
        :param dut_engine: ssh dut engine
        :param apply: true to apply configuration
        :return: ResultObj
        """
        with allure.step('Set ‘{field}‘ to ‘{value}’ for {port_name}'.format(field=self.label, value=value,
                                                                             port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.set_interface(engine=dut_engine, field_name=self.label,
                                         output_hierarchy=self.output_hierarchy,
                                         value=value, apply=apply, port_obj=self.port_obj,
                                         ask_for_confirmation=ask_for_confirmation)

    def unset(self, dut_engine=None, apply=True, ask_for_confirmation=False):
        """
        Unset current field
        :param dut_engine: ssh dut engine
        :param apply: true to apply configuration
        :return: ResultObj
        """
        with allure.step('Unset ‘{field}‘ for {port_name}'.format(field=self.label, port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut
            return CmdBase.unset_interface(engine=dut_engine, field_name=self.label,
                                           output_hierarchy=self.output_hierarchy,
                                           apply=apply, port_obj=self.port_obj,
                                           ask_for_confirmation=ask_for_confirmation)


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

    def set(self, value, dut_engine=None, apply=True, ask_for_confirmation=False):
        return LinkBaseOperational.set(self, int(value), dut_engine, apply, ask_for_confirmation)


class OpVls(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_OPERATIONAL_VLS,
                                     description="interface VLs",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_OPERATIONAL_VLS))


class Mac(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_MAC,
                                     description="MAC Address on an interface",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_MAC))


class Duplex(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_DUPLEX,
                                     description="Link duplex",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_DUPLEX))


class AutoNegotiate(LinkBaseOperational):
    def __init__(self, port_obj):
        LinkBaseOperational.__init__(self, port_obj=port_obj,
                                     label=IbInterfaceConsts.LINK_AUTO_NEGOTIATE,
                                     description="Link speed and characteristic auto negotiation",
                                     field_name_in_db={},
                                     output_hierarchy="{level1} {level2}".format(
                                         level1=IbInterfaceConsts.LINK,
                                         level2=IbInterfaceConsts.LINK_AUTO_NEGOTIATE))


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
        with allure.step('Execute show interface link for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, TestToolkit.tested_ports, self.output_hierarchy,
                                                   output_format).get_returned_value()

    def set(self, value, dut_engine=None, apply=True, ask_for_confirmation=False):
        with allure.step('Set ‘state‘ to ‘{value}’ for {port_name}'.format(value=value, port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            value_to_use = value
            field_name_to_use = self.label
            if TestToolkit.tested_api == ApiType.OPENAPI:
                value_to_use = {}
                field_name_to_use = value

            return CmdBase.set_interface(engine=dut_engine, field_name=field_name_to_use,
                                         output_hierarchy=self.output_hierarchy,
                                         value=value_to_use, apply=apply, port_obj=self.port_obj,
                                         ask_for_confirmation=ask_for_confirmation)
