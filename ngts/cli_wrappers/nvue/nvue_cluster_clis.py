from ngts.cli_wrappers.sonic.sonic_general_clis import *
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli


logger = logging.getLogger()
server_ip = "10.237.116.60"


class NvueClusterCli(NvueBaseCli):

    """
    This class is for general cli commands for NVOS only
    """

    def __init__(self):
        self.cli_name = "Cluster"

    @staticmethod
    def action_start_cluster_app(engine, path):
        cmd = f"nv action start {path}"
        cmd = " ".join(cmd.split())
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=5)

    @staticmethod
    def action_stop_cluster_app(engine, path):
        cmd = f"nv action stop {path}"
        cmd = " ".join(cmd.split())
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=5)

    @staticmethod
    def action_update_cluster_log_level(engine, path, level=''):
        cmd = f"nv action update {path} {level}"
        cmd = " ".join(cmd.split())
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=5)

    @staticmethod
    def action_restore_cluster(engine, path):
        cmd = f"nv action restore {path}"
        cmd = " ".join(cmd.split())
        logging.info(f"Running '{cmd}' on dut using NVUE")
        return DutUtilsTool.run_cmd_with_disconnect(engine, cmd, timeout=5)
