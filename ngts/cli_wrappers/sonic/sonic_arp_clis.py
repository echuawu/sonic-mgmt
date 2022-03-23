import logging

from ngts.cli_util.cli_parsers import generic_sonic_output_parser

logger = logging.getLogger()


class SonicArpCli:
    """
    This class hosts SONiC ARP cli methods
    """

    def __init__(self, engine):
        self.engine = engine

    def clear_arp(self):
        """
        This method is to clear dynamic arp table
        :return: command output
        """
        return self.engine.run_cmd('sudo sonic-clear arp', validate=True)

    def show_arp_table(self):
        """
        This method is to show the arp table info by show arp
        e.g.:
            Address      MacAddress         Iface       Vlan
            -----------  -----------------  ----------  ------
            10.210.24.1  00:00:5e:00:01:01  eth0        -
            29.0.0.2     08:bc:27:af:cc:45  Ethernet36  -
            Total number of entries 2
        :return: command output like below
        {"10.210.24.1": {"Address": "10.210.24.1", "MacAddress":"00:00:5e:00:01:01", "Iface":"etho", "vlan": ""},
        "29.0.0.2 ": {"Address": "29.0.0.2", "MacAddress":"08:bc:27:af:cc:45", "Iface":"Ethernet36", "vlan": ""}}
        """
        arp_table = self.engine.run_cmd('sudo show arp', validate=True)
        arp_table_dict = generic_sonic_output_parser(arp_table,
                                                     headers_ofset=0,
                                                     len_ofset=1,
                                                     data_ofset_from_start=2,
                                                     data_ofset_from_end=-1,
                                                     column_ofset=2,
                                                     output_key='Address')
        return arp_table_dict
