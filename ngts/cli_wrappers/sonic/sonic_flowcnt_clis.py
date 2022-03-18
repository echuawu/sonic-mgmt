from ngts.cli_wrappers.common.flowcnt_clis_common import FlowcntCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicFlowcntCli(FlowcntCliCommon):
    """
    This class is for flow counters cli commands for sonic only
    """

    def __init__(self, engine):
        self.engine = engine

    def show_trap_stats(self):
        """
        Show statistics of all traps matching the configured traps
        """
        cmd = 'show flowcnt-trap stats'
        return self.engine.run_cmd(cmd)

    def parse_trap_stats(self):
        flowcnt_trap_stats_output = self.show_trap_stats()
        flowcnt_trap_stats_dict = generic_sonic_output_parser(flowcnt_trap_stats_output,
                                                              headers_ofset=0,
                                                              len_ofset=1,
                                                              data_ofset_from_start=2,
                                                              data_ofset_from_end=None,
                                                              column_ofset=2,
                                                              output_key='Trap Name')
        return flowcnt_trap_stats_dict

    def clear_trap_counters(self):
        """
        Clear all trap counters
        """
        cmd = 'sonic-clear flowcnt-trap'
        return self.engine.run_cmd(cmd)
