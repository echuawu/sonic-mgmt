from ngts.cli_wrappers.common.bgp_clis_common import BgpCliCommon


class SonicBgpCli(BgpCliCommon):
    """
    This class is for bgp cli commands for sonic only
    """

    def __init__(self, engine):
        self.engine = engine

    def startup_bgp_all(self):
        """
        Startup BGP on SONIC
        """
        cmd = 'sudo config bgp startup all'
        return self.engine.run_cmd(cmd)

    def shutdown_bgp_all(self):
        """
        Shutdown BGP on SONIC
        """
        cmd = 'sudo config bgp shutdown all'
        return self.engine.run_cmd(cmd)
