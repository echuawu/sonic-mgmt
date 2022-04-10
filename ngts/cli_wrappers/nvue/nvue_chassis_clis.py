from ngts.cli_wrappers.common.chassis_clis_common import ChassisCliCommon


class NvueChassisCli(ChassisCliCommon):
    """
    This class is for chassis cli commands for NVOS only
    """

    def __init__(self):
        pass

    @staticmethod
    def show_platform_summary(engine):
        """
        This method excute command "show platform summary" on dut
        :param engine: ssh engine object
        :return: the cmd output
        """
        return engine.run_cmd("show platform summary")

    def get_hostname(self):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
