import logging

from ngts.cli_wrappers.nvue.nvue_chassis_clis import NvueChassisCli
from ngts.cli_wrappers.sonic.sonic_hw_mgmt_cli import SonicHwMgmtCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()


class NvueCli():
    def __init__(self, topology):
        self.chassis = NvueChassisCli()
        # self.branch = topology.players['dut'].get('branch')
        self.engine = topology.players['dut']['engine']
        self._general = None
        self._hw_mgmt = None

    @property
    def general(self):
        if self._general is None:
            self._general = NvueGeneralCli(engine=self.engine, device=None)
        return self._general

    @property
    def hw_mgmt(self):
        if self._hw_mgmt is None:
            self._hw_mgmt = SonicHwMgmtCli(engine=self.engine)
        return self._hw_mgmt
