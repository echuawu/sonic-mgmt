from ngts.nvos_tools.ib.InterfaceConfiguration.Stats import *


class MgmtStats(ConfigurationBase):
    in_bytes = None
    in_drops = None
    in_errors = None
    in_symbol_errors = None
    in_pkts = None
    out_bytes = None
    out_drops = None
    out_errors = None
    out_pkts = None
    out_wait = None

    def __init__(self, port_obj):
        ConfigurationBase.__init__(self, port_obj=port_obj,
                                   label=IbInterfaceConsts.LINK_STATS,
                                   description="interface stats",
                                   field_name_in_db={},
                                   output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS))

        self.in_bytes = InBytes(port_obj)
        self.in_drops = InDrops(port_obj)
        self.in_errors = InErrors(port_obj)
        self.in_pkts = InPkts(port_obj)
        self.out_bytes = OutBytes(port_obj)
        self.out_drops = OutDrops(port_obj)
        self.out_errors = OutDrops(port_obj)
        self.out_pkts = OutPkts(port_obj)
        self.carrier_transition = CarrierTransition(port_obj)

    def clear_stats(self, dut_engine):
        """
        Clears interface counters
        """
        if not dut_engine:
            dut_engine = TestToolkit.engines.dut

        with allure.step('Clear stats for {port_name}'.format(port_name=self.port_obj.name)):
            return SendCommandTool.execute_command(Port.api_obj[TestToolkit.tested_api].clear_stats,
                                                   dut_engine, self.port_obj.name)

    def show_interface_link_stats(self, dut_engine=None, output_format=OutputFormat.json):
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
                                                   dut_engine, self.port_obj.name, self.output_hierarchy,
                                                   output_format).get_returned_value()


class CarrierTransition(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_CARRIER_TRANSITION,
                           description="Number of times the interface state has transitioned between up and down",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_CARRIER_TRANSITION))
