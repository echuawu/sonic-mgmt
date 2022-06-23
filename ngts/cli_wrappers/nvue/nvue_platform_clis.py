import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli

logger = logging.getLogger()


class NvuePlatformCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "Platform"
