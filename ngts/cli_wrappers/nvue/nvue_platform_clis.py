import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli

logger = logging.getLogger()


class NvuePlatformCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "Platform"

    @staticmethod
    def action_turn(engine, turn_type="", led=""):
        cmd = "nv action turn-{type} platform environment led {led}".format(type=turn_type, led=led)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
