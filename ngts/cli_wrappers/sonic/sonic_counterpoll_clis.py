from ngts.cli_wrappers.common.counterpoll_clis_common import CounterpollCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicCounterpollCli(CounterpollCliCommon):
    """
    This class is for counterpoll cli commands for sonic only
    """

    @staticmethod
    def disable_counterpoll(engine):
        """
        Disable counterpoll on SONIC
        :param engine: ssh engine object
        """
        cmd = 'sudo counterpoll config-db disable'
        return engine.run_cmd(cmd)

    @staticmethod
    def enable_counterpoll(engine):
        """
        Enable counterpoll on SONIC
        :param engine: ssh engine object
        """
        cmd = 'sudo counterpoll config-db enable'
        return engine.run_cmd(cmd)

    @staticmethod
    def show(engine):
        """
        Run command "counterpoll show" on SONIC
        :param engine: ssh engine object
        :return: cmd output
        """
        cmd = 'sudo counterpoll show'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_counterpoll_show(engine):
        """
        Run command "counterpoll show" on SONIC and parse output to dict
        :param engine: ssh engine object
        :return: dictionary with parsed output
        """
        counterpoll_show_output = SonicCounterpollCli.show(engine)
        counterpoll_show_dict = generic_sonic_output_parser(counterpoll_show_output,
                                                            headers_ofset=0,
                                                            len_ofset=1,
                                                            data_ofset_from_start=2,
                                                            data_ofset_from_end=None,
                                                            column_ofset=2,
                                                            output_key='Type')
        return counterpoll_show_dict

    @staticmethod
    def enable_flowcnt_trap(engine):
        """
        Run command "counterpoll flowcnt-trap enable" on SONIC
        :param engine: ssh engine object
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap enable'
        return engine.run_cmd(cmd)

    @staticmethod
    def disable_flowcnt_trap(engine):
        """
        Run command "counterpoll flowcnt-trap disable" on SONIC
        :param engine: ssh engine object
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap disable'
        return engine.run_cmd(cmd)

    @staticmethod
    def set_trap_interval(engine, interval):
        """
        Run command "counterpoll flowcnt-trap interval <time_in_msec>" on SONIC
        :param engine: ssh engine object
        :param interval: polling interval for trap flow counters
        :return: cmd output
        """
        cmd = 'sudo counterpoll flowcnt-trap interval {}'.format(interval)
        return engine.run_cmd(cmd)
