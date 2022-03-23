import logging
import re

from ngts.cli_wrappers.common.lldp_clis_common import LldpCliCommon

logger = logging.getLogger()


class LinuxLldpCli(LldpCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def show_lldp_info_for_specific_interface(self, interface_name):
        """
        This method gets LLDP information for a specific interface
        :param interface_name: interface name
        :return: command output
        """
        return self.engine.run_cmd("lldptool -i {} -t -n".format(interface_name))

    @staticmethod
    def parse_lldp_info_for_specific_interface(port_lldp_output):
        """
        return a dictionary with parsed lldp information for a specific interface on host.
        :param port_lldp_output: LLDP information for a specific interface
        :return: a dictionary with parsed lldp information
        """
        regex_patterns = {"neighbor_port": "Port\\s*Description\\s*TLV\\s*(.*)\\s",
                          "neighbor_hostname": "System\\s*Name\\s*TLV\\s*(.*)\\s",
                          "neighbor_mgmt_ip": "Management\\s*Address\\s*TLV\\s*IPv4:\\s*(.*)\\s"}
        res = {}
        logger.debug("LLDP info is:\n{}".format(port_lldp_output))
        for value_name, reg_pattern in regex_patterns.items():
            logger.debug("Checking for regex pattern {} in LLDP info".format(reg_pattern))
            try:
                reg_value = re.search(reg_pattern, port_lldp_output, re.IGNORECASE).group(1)
            except Exception as e:
                raise AssertionError("Couldn't find regex pattern: {} in LLDP output: {}"
                                     .format(reg_pattern, port_lldp_output))
            res[value_name] = reg_value
        return res

    def disable_lldp_on_interface(self, interface):
        """
        This method disable LLDP on host interface
        :param interface: interface name
        :return: command output
        """
        return self.engine.run_cmd("lldptool set-lldp -i {} adminStatus=disabled".format(interface))

    def enable_lldp_on_interface(self, interface):
        """
        This method enable LLDP on host interface
        :param interface: interface name
        :return: command output
        """
        return self.engine.run_cmd("lldptool set-lldp -i {} adminStatus=rxtx".format(interface))

    def enable_lldp_on_host(self):
        """
        This method enable LLDP on host
        :return: command output
        """
        return self.engine.run_cmd("lldpad -d")

    def is_lldp_enabled_on_host(self):
        """
        This method enable LLDP on host
        :return: command output
        """
        regex_pattern = "lldpad -d"
        output = self.engine.run_cmd("ps -aux | grep lldpad")
        return bool(re.search(regex_pattern, output, re.IGNORECASE))
