import logging

logger = logging.getLogger()


class NvueOpenSmCli:

    @staticmethod
    def enable(engine):
        cmd = 'sudo opensm &'
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
