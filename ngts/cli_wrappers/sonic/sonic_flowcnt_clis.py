from ngts.cli_wrappers.common.flowcnt_clis_common import FlowcntCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicFlowcntCli(FlowcntCliCommon):
    """
    This class is for flow counters cli commands for sonic only
    """

    @staticmethod
    def show_trap_stats(engine):
        """
        Show statistics of all traps matching the configured traps
        :param engine: ssh engine object
        """
        cmd = 'show flowcnt-trap stats'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_trap_stats(engine):
        flowcnt_trap_stats_output = SonicFlowcntCli.show_trap_stats(engine)
        flowcnt_trap_stats_dict = generic_sonic_output_parser(flowcnt_trap_stats_output,
                                                              headers_ofset=0,
                                                              len_ofset=1,
                                                              data_ofset_from_start=2,
                                                              data_ofset_from_end=None,
                                                              column_ofset=2,
                                                              output_key='Trap Name')
        return flowcnt_trap_stats_dict

    @staticmethod
    def clear_trap_counters(engine):
        """
        Clear all trap counters
        :param engine: ssh engine object
        """
        cmd = 'sonic-clear flowcnt-trap'
        return engine.run_cmd(cmd)
