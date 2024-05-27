import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli, check_output

logger = logging.getLogger()


class NvueIbCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "Ib"

    @staticmethod
    @check_output
    def action_run(engine, command, op_param=""):
        cmd = "nv action run ib cmd {command} {param}".format(command=command, param=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    @check_output
    def action_upload(engine, path, file_name, url, op_param=""):
        path = path.replace('/', ' ')
        cmd = "nv action upload {path} {filename} {url}".format(path=path, filename=file_name, url=url)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    @check_output
    def action_delete(engine, path, file_name, op_param=""):
        path = path.replace('/', ' ')
        cmd = "nv action delete {path} {filename}".format(path=path, filename=file_name)
        cmd = " ".join(cmd.split())
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
