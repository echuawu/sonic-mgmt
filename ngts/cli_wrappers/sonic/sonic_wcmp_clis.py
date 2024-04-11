import logging
import json

from ngts.cli_wrappers.common.wcmp_clis_common import WcmpCliCommon
logger = logging.getLogger()


class SonicWcmpCli(WcmpCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def config_wcmp_cli(self, status):
        """
        Configure WCMP using SONIC cli.

        Example:
        admin@r-ocelot-02:~$ sudo config bgp device-global wcmp enabled
        """
        logger.info(f'Config WCMP status: {status}')
        return self.engine.run_cmd(f'sudo config bgp device-global wcmp {status}')

    def config_wcmp_redis_cli(self, status):
        """
        Configure WCMP using redis-cli.

        Example:
        admin@r-ocelot-02:~$ redis-cli -n 4 HSET "BGP_DEVICE_GLOBAL|STATE" "wcmp_enabled" "true"
        (integer) 0
        """
        logger.info(f'Config WCMP status: {status}')
        return self.engine.run_cmd(f'redis-cli -n 4 HSET "BGP_DEVICE_GLOBAL|STATE" "wcmp_enabled" {status}')

    def get_wcmp_status(self):
        """
        Execute command 'sudo show bgp device-global --json' to get wcmp status
        """
        logger.info('Get WCMP status')
        result = self.engine.run_cmd('sudo show bgp device-global --json')
        return json.loads(result).get('wcmp', 'unknown')

    def get_frr_bgp_config(self):
        """
        Execute command 'vtysh -c "show running-config bgp"' to BGP config on FRR
        """
        logger.info('Get WCMP status')
        result = self.engine.run_cmd('vtysh -c "show running-config bgp"').split('\n')
        frr_bgp_config = [line.strip() for line in result]
        logger.info(f'The FRR bgp config is {frr_bgp_config}')
        return frr_bgp_config
