import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli

logger = logging.getLogger()


class NvueOpenSmCli(NvueBaseCli):

    @staticmethod
    def enable(engine):
        cmd = 'sudo opensm &'
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
