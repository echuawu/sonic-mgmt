import re
from ngts.cli_wrappers.common.chassis_clis_common import ChassisCliCommon


class SonicChassisCli(ChassisCliCommon):
    """
    This class is for chassis cli commands for sonic only
    """
    def __init__(self):
        pass

    @staticmethod
    def get_platform(engine):
        """
        This method excute command "show platform summary" and return the dut platform type
        :param engine: ssh engine object
        :return: the dut platform type
        """
        output = SonicChassisCli.show_platform_summary(engine)
        pattern = "Platform:\s*(.*)"
        try:
            platform = re.search(pattern, output, re.IGNORECASE).group(1)
            return platform
        except Exception:
            raise AssertionError("Could not match platform type for switch {}".format(engine.ip))

    @staticmethod
    def show_platform_summary(engine):
        """
        This method excute command "show platform summary" on dut
        :param engine: ssh engine object
        :return: the cmd output
        """
        return engine.run_cmd("show platform summary")

    @staticmethod
    def show_mst_status(engine):
        return engine.run_cmd("sudo mst status")

    @staticmethod
    def get_pci_conf(engine):
        mst_status = SonicChassisCli.show_mst_status(engine)
        return re.search("(.*pciconf0)", mst_status).group(1)
