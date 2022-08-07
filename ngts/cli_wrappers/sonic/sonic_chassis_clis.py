import re
from ngts.cli_wrappers.common.chassis_clis_common import ChassisCliCommon


class SonicChassisCli(ChassisCliCommon):
    """
    This class is for chassis cli commands for sonic only
    """

    def __init__(self, engine):
        self.engine = engine

    def get_platform(self):
        """
        This method excute command "show platform summary" and return the dut platform type
        :return: the dut platform type
        """
        output = self.show_platform_summary()
        pattern = r"Platform:\s*(.*)"
        try:
            platform = re.search(pattern, output, re.IGNORECASE).group(1)
            return platform
        except Exception:
            raise AssertionError("Could not match platform type for switch {}".format(self.engine.ip))

    def show_platform_summary(self):
        """
        This method excute command "show platform summary" on dut
        :return: the cmd output
        """
        return self.engine.run_cmd("show platform summary")

    def show_platform_syseeprom(self):
        """
        This method excute command "show platform syseeprom" on dut
        :return: the cmd output
        """
        return self.engine.run_cmd("show platform syseeprom")

    def show_mst_status(self):
        return self.engine.run_cmd("sudo mst status")

    def get_pci_conf(self):
        mst_status = self.show_mst_status()
        return re.search("(.*pciconf0)", mst_status).group(1)

    def parse_platform_summary(self):
        """
        Parse the output of "show platform summary"
        :return: dict, example: {'HwSKU': 'ACS-MSN4410', 'ASIC Count': '1', 'ASIC': 'mellanox'...}

        """
        platform_summary_dict = {}
        platform_summary = self.show_platform_summary()
        for line in platform_summary.splitlines():
            split_line = line.split(": ")
            platform_summary_dict.update({split_line[0]: split_line[1]})
        return platform_summary_dict
