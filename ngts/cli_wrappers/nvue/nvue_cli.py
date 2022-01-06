import logging

from ngts.cli_wrappers.nvue.nvue_chassis_clis import NvueChassisCli

logger = logging.getLogger()


class NvueCli:
    def __init__(self):
        self.chassis = NvueChassisCli()
