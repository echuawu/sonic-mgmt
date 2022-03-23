from ngts.cli_wrappers.common.counterpoll_clis_common import CounterpollCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicCounterpollCli(CounterpollCliCommon):
    """
    This class is for counterpoll cli commands for sonic only
    """

    def __init__(self, engine):
        self.engine = engine

    def disable_counterpoll(self):
        """
        Disable counterpoll on SONIC
        """
        cmd = 'sudo counterpoll config-db disable'
        return self.engine.run_cmd(cmd)

    def enable_counterpoll(self):
        """
        Enable counterpoll on SONIC
        """
        cmd = 'sudo counterpoll config-db enable'
        return self.engine.run_cmd(cmd)

    def show(self):
        """
        Run command "counterpoll show" on SONIC
        :return: cmd output
        """
        cmd = 'sudo counterpoll show'
        return self.engine.run_cmd(cmd)

    def parse_counterpoll_show(self):
        """
        Run command "counterpoll show" on SONIC and parse output to dict
        :return: dictionary with parsed output
        """
        counterpoll_show_output = self.show()
        counterpoll_show_dict = generic_sonic_output_parser(counterpoll_show_output,
                                                            headers_ofset=0,
                                                            len_ofset=1,
                                                            data_ofset_from_start=2,
                                                            data_ofset_from_end=None,
                                                            column_ofset=2,
                                                            output_key='Type')
        return counterpoll_show_dict

    def enable_flowcnt_trap(self):
        """
        Run command "counterpoll flowcnt-trap enable" on SONIC
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap enable'
        return self.engine.run_cmd(cmd)

    def disable_flowcnt_trap(self):
        """
        Run command "counterpoll flowcnt-trap disable" on SONIC
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap disable'
        return self.engine.run_cmd(cmd)

    def set_trap_interval(self, interval):
        """
        Run command "counterpoll flowcnt-trap interval <time_in_msec>" on SONIC
        :param interval: polling interval for trap flow counters
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap interval {}'.format(interval)
        return self.engine.run_cmd(cmd)
