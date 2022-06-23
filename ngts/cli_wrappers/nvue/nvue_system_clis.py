import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.constants.constants_nvos import ActionConsts

logger = logging.getLogger()


class NvueSystemCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "System"

    @staticmethod
    def action_image(engine, action_str, action_component_str, op_param=""):
        cmd = "nv action {action_type} system {action_component} {param}".format(action_type=action_str,
                                                                                 action_component=action_component_str,
                                                                                 param=op_param)
        logging.info("Running action cmd: '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_firmware_install(engine, action_component_str, op_param=""):
        cmd = "nv action install system {action_component} {param}".format(action_component=action_component_str,
                                                                           param=op_param)
        logging.info("Running action cmd: '{cmd}' onl dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
