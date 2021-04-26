from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from ngts.constants.constants import IpIfaceAddrConst


class SonicIpCli(IpCliCommon):

    @staticmethod
    def add_del_ip_from_interface(engine, action, interface, ip, mask):
        """
        This method adds/remove ip address to/from network interface
        :param engine: ssh engine object
        :param action: action which should be executed: add or remove
        :param interface: interface name to which IP should be assigned/removed
        :param ip: ip address which should be assigned/removed
        :param mask: mask which should be assigned/remove to/from IP
        :return: method which do required action
        """
        if action not in ['add', 'remove']:
            raise NotImplementedError(
                'Incorrect action {} provided, supported only add/del'.format(action))

        engine.run_cmd(
            'sudo config interface ip {} {} {}/{}'.format(action, interface, ip, mask))

    @staticmethod
    def add_ip_to_interface(engine, interface, ip, mask=24):
        """
        This method adds IP to SONiC interface
        :param engine: ssh engine object
        :param interface: interface name to which IP should be assigned
        :param ip: ip address which should be assigned
        :param mask: mask which should be assigned to IP
        :return: command output
        """
        SonicIpCli.add_del_ip_from_interface(
            engine, 'add', interface, ip, mask)

    @staticmethod
    def del_ip_from_interface(engine, interface, ip, mask=24):
        """
        This method removes IP from SONiC interface
        :param engine: ssh engine object
        :param interface: interface name from which IP should be removed
        :param ip: ip address which should be removed
        :param mask: network mask
        :return: command output
        """
        SonicIpCli.add_del_ip_from_interface(
            engine, 'remove', interface, ip, mask)

    @staticmethod
    def show_ip_interfaces(engine):
        """
        This method shows ip configuration on interfaces
        :return: the output of the command "show ip interfaces"
        """
        return engine.run_cmd('sudo show ip interfaces')

    @staticmethod
    def get_interface_ips(engine, interface):
        """
        This method get ip address and mask on specified interface
        :return: list of ip and mask of the interface, empty list will retrun if no ip address configured for the interface
                 example for [{'ip': '10.0.0.2', 'mask': 24},{'ip': '20.0.0.2', 'mask': 24}]
        """

        ip_list = []
        cmd_list = ['sudo show ip interfaces', 'sudo show ipv6 interfaces']
        for cmd in cmd_list:
            output = engine.run_cmd(cmd)
            interfaces = generic_sonic_output_parser(output, headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                                     data_ofset_from_end=None, column_ofset=2, output_key="Interface")
            if interface in interfaces.keys():
                interface_dict_list = SonicIpCli.get_interface_dict_list(
                    interfaces, interface)
                for interface_dict in interface_dict_list:
                    key = SonicIpCli.get_ip_type_key(interface_dict)
                    ip_mask = interface_dict[key].split('/')
                    ip_list.append({'ip': ip_mask[0], 'mask': ip_mask[1]})

        return ip_list

    @staticmethod
    def get_interface_dict_list(interfaces, interface):
        """
        This method is to make sure the interface dict for the specified interface is contained into a list
        :param interfaces: the dict of the interfaces
        :param interface: the interface name, such as Ethernet0
        :return: list of interface dict, such as [{Interface: Ethernet0, ....}]
        """

        interface_dict_list = interfaces[interface]
        if not isinstance(interface_dict_list, list):
            interface_dict_list = [interface_dict_list]

        return interface_dict_list

    @staticmethod
    def get_ip_type_key(interface_dict):
        """
        get the ip type key, when IPV6_ADDR_MASK_KEY is in the header, use it, else, use IPV4_ADDR_MASK_KEY
        :param interface_dict: interface dict
        :return: the header name.
        """
        return IpIfaceAddrConst.IPV6_ADDR_MASK_KEY if IpIfaceAddrConst.IPV6_ADDR_MASK_KEY in interface_dict else IpIfaceAddrConst.IPV4_ADDR_MASK_KEY
