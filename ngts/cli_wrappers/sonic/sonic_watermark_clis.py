
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicWatermarkCli:
    """
    This class is for Watermark cli commands
    """

    def __init__(self, engine):
        self.engine = engine

    def clear_watermarkstat(self, stat='pg_shared'):
        """
        Clear watermarkstat
        :param stat: statistic to clear. Choose from 'pg_headroom', 'pg_shared', 'q_shared_uni',
                        'q_shared_multi', 'buffer_pool', 'headroom_pool', 'q_shared_all'
        :return: the output of cli command
        """
        return self.engine.run_cmd(f'watermarkstat -t {stat} -c')

    def show_watermarkstat(self, stat='pg_shared'):
        """
        Show watermarkstat
        :param stat: statistic to clear. Choose from 'pg_headroom', 'pg_shared', 'q_shared_uni',
                        'q_shared_multi', 'buffer_pool', 'headroom_pool', 'q_shared_all'
        :return: the output of cli command
        """
        return self.engine.run_cmd(f'watermarkstat -t {stat}')

    def show_and_parse_watermarkstat(self, stat='pg_shared'):
        """
        Parse watermarkstat output.
        Support only pg_headroom', 'pg_shared', 'q_shared_uni', 'q_shared_multi'.
        The others stats have different output
        :param stat: statistic to clear. Choose from 'pg_headroom', 'pg_shared', 'q_shared_uni', 'q_shared_multi'
        :return: the output of cli command
        """
        stat_outout = self.show_watermarkstat(stat)
        return generic_sonic_output_parser(stat_outout, headers_ofset=1, len_ofset=2,
                                           data_ofset_from_start=3, output_key='Port')
