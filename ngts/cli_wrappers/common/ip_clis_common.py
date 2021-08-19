import re
import logging

from ngts.cli_wrappers.interfaces.interface_ip_clis import IpCliInterface

logger = logging.getLogger()


class IpCliCommon(IpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass

    @staticmethod
    def add_ip_neigh(engine, neighbor, neigh_mac_addr, dev, action="replace"):
        """
        This method adds an neighbor entry to the ARP table
        :param engine: ssh engine object
        :param neighbor: neighbor IP address
        :param neigh_mac_addr: neighbor MAC address
        :param dev: interface to which neighbour is attached
        :param action: it includes replace or add, the two both can add ip neigh, replace can replace old neigh
        :return: command output
        """
        return engine.run_cmd("sudo ip neigh {} {} lladdr {} dev {}".format(action, neighbor, neigh_mac_addr, dev))

    @staticmethod
    def del_ip_neigh(engine, neighbor, neigh_mac_addr, dev):
        """
        This method adds an neighbor entry to the ARP table
        :param engine: ssh engine object
        :param neighbor: neighbor IP address
        :param neigh_mac_addr: neighbor MAC address
        :param dev: interface to which neighbour is attached
        :return: command output
        """
        return engine.run_cmd("sudo ip neigh del {} lladdr {} dev {}".format(neighbor, neigh_mac_addr, dev))

    @staticmethod
    def del_static_neigh(engine):
        """
        This method del the static(PERMANENT) arp from the arp table
        :param engine: ssh engine object
        """
        static_arp_regrex = r"(?P<neigh>.*) dev (?P<dev>.*) lladdr (?P<mac>[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{" \
                            r"2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}) .*PERMANENT"
        ip_neigh_table = engine.run_cmd("sudo ip neigh")
        for arp_entry in ip_neigh_table.split("\n"):
            static_arp_entry = re.match(static_arp_regrex, arp_entry.strip())
            if static_arp_entry:
                static_arp_entry = static_arp_entry.groupdict()
                logger.info("Del static arp:{}".format(static_arp_entry))
                IpCliCommon.del_ip_neigh(engine, static_arp_entry["neigh"], static_arp_entry["mac"],
                                         static_arp_entry["dev"])
