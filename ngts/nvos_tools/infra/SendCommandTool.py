from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli


class SendCommandTool:

    @staticmethod
    def apply_config(engine):
        """
        Apply configuration
        """
        NvueGeneralCli.apply_config(engine)
