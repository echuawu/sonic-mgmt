from ngts.cli_wrappers.common.bgp_clis_common import BgpCliCommon


class SonicBgpCli(BgpCliCommon):
    """
    This class is for bgp cli commands for sonic only
    """

    @staticmethod
    def startup_bgp_all(engine):
        """
        Startup BGP on SONIC
        :param engine: ssh engine object
        """
        cmd = 'sudo config bgp startup all'
        return engine.run_cmd(cmd)

    @staticmethod
    def shutdown_bgp_all(engine):
        """
        Shutdown BGP on SONIC
        :param engine: ssh engine object
        """
        cmd = 'sudo config bgp shutdown all'
        return engine.run_cmd(cmd)
