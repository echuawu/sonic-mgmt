from .ConfigurationBase import ConfigurationBase
from .nvos_consts import IbInterfaceConsts
from .IbInterfaceDecorators import *
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
import allure


class Pluggable(ConfigurationBase):
    identifier = None
    cable_length = None
    vendor_name = None
    vendor_pn = None
    vendor_rev = None
    vendor_sn = None

    def __init__(self, port_obj):
        ConfigurationBase.__init__(self,
                                   port_obj=port_obj,
                                   label=IbInterfaceConsts.PLUGGABLE,
                                   description="An interface sfp details",
                                   field_name_in_db={},
                                   output_hierarchy=IbInterfaceConsts.PLUGGABLE)

        Pluggable.identifier = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_IDENTIFIER,
                                             description="The identifier of sfp module",
                                             field_name_in_db={},
                                             output_hierarchy="{level1} {level2}".format(
                                                 level1=IbInterfaceConsts.PLUGGABLE,
                                                 level2=IbInterfaceConsts.PLUGGABLE_IDENTIFIER))

        Pluggable.cable_length = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_CABLE_LENGTH,
                                               description="The cable length of sfp module",
                                               field_name_in_db={},
                                               output_hierarchy="{level1} {level2}".format(
                                                   level1=IbInterfaceConsts.PLUGGABLE,
                                                   level2=IbInterfaceConsts.PLUGGABLE_CABLE_LENGTH))

        Pluggable.vendor_name = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_VENDOR_NAME,
                                              description="The vendor name of sfp module",
                                              field_name_in_db={},
                                              output_hierarchy="{level1} {level2}".format(
                                                  level1=IbInterfaceConsts.PLUGGABLE,
                                                  level2=IbInterfaceConsts.PLUGGABLE_VENDOR_NAME))

        Pluggable.vendor_pn = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_VENDOR_PN,
                                            description="The vendor product name of sfp module",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                level1=IbInterfaceConsts.PLUGGABLE,
                                                level2=IbInterfaceConsts.PLUGGABLE_VENDOR_PN))

        Pluggable.vendor_rev = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_VENDOR_REV,
                                             description="The vendor revision of sfp module",
                                             field_name_in_db={},
                                             output_hierarchy="{level1} {level2}".format(
                                                 level1=IbInterfaceConsts.PLUGGABLE,
                                                 level2=IbInterfaceConsts.PLUGGABLE_VENDOR_REV))

        Pluggable.vendor_sn = PluggableBase(port_obj=port_obj, label=IbInterfaceConsts.PLUGGABLE_VENDOR_SN,
                                            description="The vendor serial number of sfp module",
                                            field_name_in_db={},
                                            output_hierarchy="{level1} {level2}".format(
                                                level1=IbInterfaceConsts.PLUGGABLE,
                                                level2=IbInterfaceConsts.PLUGGABLE_VENDOR_SN))

    def show_interface_pluggable(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface pluggable'):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(ApiObject[TestToolkit.api_show].show_interface,
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()


class PluggableBase(ConfigurationBase):

    def __init__(self, port_obj, label, description, field_name_in_db, output_hierarchy):
        ConfigurationBase.__init__(self, port_obj, label, description, field_name_in_db, output_hierarchy)

    def _get_value(self, engine=None, renew_show_cmd_output=True):
        """
        Returns operational/applied value
        :param renew_show_cmd_output: If true - 'show' command will be executed before checking the value
                                      Else - results from the previous 'show' command will be used
        :return:
        """
        if not engine:
            engine = TestToolkit.engines.dut

        if renew_show_cmd_output:
            TestToolkit.update_port_output_dictionary(self.port_obj, engine)
        output_str = self.port_obj.show_output_dictionary[IbInterfaceConsts.PLUGGABLE][self.label]
        return output_str
