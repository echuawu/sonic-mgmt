import logging

from ngts.cli_wrappers.nvue.nvue_chassis_clis import NvueChassisCli
# from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()


class NvueCli():
    def __init__(self, topology):
        self.chassis = NvueChassisCli()
        # self.branch = topology.players['dut'].get('branch')
        self.engine = topology.players['dut']['engine']
        self._general = None

    @property
    def general(self):
        if self._general is None:
            self._general = NvueGeneralCli(engine=self.engine)
        return self._general
