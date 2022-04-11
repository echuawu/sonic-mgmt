from .ConfigurationBase import ConfigurationBase
from .nvos_consts import IbInterfaceConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from .nvos_consts import ApiObject
import logging
import allure
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat

logger = logging.getLogger()


class Stats(ConfigurationBase):
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
        self.in_symbol_errors = InSymbolErrors(port_obj)
        self.in_pkts = InPkts(port_obj)
        self.out_bytes = OutBytes(port_obj)
        self.out_drops = OutDrops(port_obj)
        self.out_errors = OutDrops(port_obj)
        self.out_pkts = OutPkts(port_obj)
        self.out_wait = OutWait(port_obj)

    def clear_stats(self, dut_engine):
        """
        Clears interface counters
        """
        with allure.step('Clear stats'):
            return ApiObject[TestToolkit.api_ib].clear_stats(engine=dut_engine,
                                                             port_name=self.port_obj.name)

    def show_interface_link_stats(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface counters
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface stats'):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return ApiObject[TestToolkit.api_show].show_interface(engine=dut_engine,
                                                                  port_name=self.port_obj.name,
                                                                  interface_hierarchy=self.output_hierarchy,
                                                                  output_format=output_format)


class StatsBase(ConfigurationBase):
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
        output_str = self.port_obj.show_output_dictionary[IbInterfaceConsts.LINK][IbInterfaceConsts.LINK_STATS][self.label]
        return output_str


class InBytes(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_IN_BYTES,
                           description="total number of bytes received on the interface",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_IN_BYTES))


class OutBytes(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_OUT_BYTES,
                           description="total number of bytes transmitted out of the interface",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_OUT_BYTES))


class InDrops(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_IN_DROPS,
                           description="total number of incoming VL15 packets dropped due to resource limitations",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_IN_DROPS))


class OutDrops(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_OUT_DROPS,
                           description="total number of packets dropped because the port is down or congested",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_OUT_DROPS))


class InErrors(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_IN_ERRORS,
                           description="total number of received packets with errors",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_IN_ERRORS))


class OutErrors(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_OUT_ERRORS,
                           description="The number of outbound packets that could not be transmitted because of errors",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_OUT_ERRORS))


class InSymbolErrors(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_IN_SYMBOL_ERRORS,
                           description="total number of minor errors detected on  one or more physical lanes",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_IN_SYMBOL_ERRORS))


class InPkts(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_IN_PKTS,
                           description="total number of packets received on the interface",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_IN_PKTS))


class OutPkts(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_OUT_PKTS,
                           description="total number of packets transmitted out of the interface",
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_OUT_PKTS))


class OutWait(StatsBase):
    def __init__(self, port_obj):
        StatsBase.__init__(self, port_obj=port_obj,
                           label=IbInterfaceConsts.LINK_STATS_OUT_WAIT,
                           description='The number of ticks during which the port selected by PortSelect' +
                                       'had data to transmit but no data was sent',
                           field_name_in_db={},
                           output_hierarchy="{level1} {level2}".format(
                                       level1=IbInterfaceConsts.LINK,
                                       level2=IbInterfaceConsts.LINK_STATS_OUT_WAIT))
