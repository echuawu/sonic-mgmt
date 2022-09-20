from .LinkBase import *
from .IbInterfaceDecorators import *
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import ApiType
import allure

logger = logging.getLogger()


class Ip(ConfigurationBase):
    vrf = None
    address = None
    gateway = None
    dhcp_client = None
    dhcp_client6 = None

    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.IP,
                                   description="",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.IP)
        self.vrf = Vrf(port_obj)
        self.address = Address(port_obj)
        self.gateway = Gateway(port_obj)
        self.dhcp_client = DhcpClient(port_obj, IbInterfaceConsts.IP_DHCP)
        self.dhcp_client6 = DhcpClient(port_obj, IbInterfaceConsts.IP_DHCP6)

    def show(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface ip for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()


class IpBase(ConfigurationBase):

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
        output_str = self.port_obj.show_output_dictionary[IbInterfaceConsts.IP][self.label]
        return output_str


class IpBaseOperational(IpBase, CmdBase):
    def __init__(self, port_obj, label, description, field_name_in_db, output_hierarchy):
        IpBase.__init__(self, port_obj, label, description, field_name_in_db, output_hierarchy)

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
                                         output_hierarchy=self.output_hierarchy, value=value,
                                         apply=apply, ask_for_confirmation=ask_for_confirmation,
                                         port_obj=self.port_obj)

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
                                           apply=apply, ask_for_confirmation=ask_for_confirmation,
                                           port_obj=self.port_obj)


class Vrf(IpBaseOperational):
    def __init__(self, port_obj):
        IpBase.__init__(self, port_obj=port_obj, label=IbInterfaceConsts.IP_VRF,
                        description="Virtual routing and forwarding",
                        field_name_in_db={}, output_hierarchy="{level1} {level2}".format(level1=IbInterfaceConsts.IP,
                                                                                         level2=IbInterfaceConsts.IP_VRF))


class Address(IpBaseOperational):
    def __init__(self, port_obj):
        IpBase.__init__(self, port_obj=port_obj, label=IbInterfaceConsts.IP_ADDRESS,
                        description="IPv4 and IPv6 address",
                        field_name_in_db={}, output_hierarchy="{level1} {level2}".
                        format(level1=IbInterfaceConsts.IP, level2=IbInterfaceConsts.IP_ADDRESS))

    def set(self, value, dut_engine=None, apply=True, ask_for_confirmation=False):
        if TestToolkit.tested_api == ApiType.OPENAPI:
            value = {value: {}}
        return IpBaseOperational.set(self, value, dut_engine, apply, ask_for_confirmation)


class Gateway(IpBaseOperational):
    def __init__(self, port_obj):
        IpBase.__init__(self, port_obj=port_obj, label=IbInterfaceConsts.IP_GATEWAY,
                        description="default IPv4 and IPv6 gateways",
                        field_name_in_db={}, output_hierarchy="{level1} {level2}".
                        format(level1=IbInterfaceConsts.IP, level2=IbInterfaceConsts.IP_GATEWAY))


class DhcpClient(IpBaseOperational):
    def __init__(self, port_obj, level2):
        IpBase.__init__(self, port_obj=port_obj, label=level2,
                        description="default IPv4 dhcp-client",
                        field_name_in_db={}, output_hierarchy="{level1} {level2}".
                        format(level1=IbInterfaceConsts.IP, level2=level2))

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
