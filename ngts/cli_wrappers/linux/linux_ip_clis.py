import json
import ipaddress
from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon


class LinuxIpCli(IpCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_del_ip_from_interface(self, action, interface, ip, mask):
        """
        This method adds/remove ip address to/from network interface
        :param action: action which should be executed: add or del
        :param interface: interface name to which IP should be assigned/removed
        :param ip: ip address which should be assigned/removed
        :param mask: mask which should be assigned/remove to/from IP
        :return: method which do required action
        """
        if action not in ['add', 'del']:
            raise NotImplementedError('Incorrect action {} provided, supported only add/del'.format(action))

        return self.engine.run_cmd("sudo ip addr {} {}/{} dev {}".format(action, ip, mask, interface))

    def add_ip_to_interface(self, interface, ip, mask):
        """
        This method adds ip address to network interface
        :param interface: interface name to which IP should be assigned
        :param ip: ip address which should be assigned
        :param mask: mask which should be assigned to IP
        :return: command output
        """
        return self.add_del_ip_from_interface('add', interface, ip, mask)

    def del_ip_from_interface(self, interface, ip, mask):
        """
        This method deletes an ip address from network interface
        :param interface: interface name from which IP should be removed
        :param ip: ip address which should be removed
        :param mask: network mask
        :return: command output
        """
        return self.add_del_ip_from_interface('del', interface, ip, mask)

    def get_ip_info(self, ip_ver='4'):
        """
        This method returns json output for command: "ip address"
        :param ip_ver: IP protocol version
        :return: json with ip command output data
        """
        ip_info = json.loads(self.engine.run_cmd('sudo ip -{} -j address'.format(ip_ver)))
        return ip_info

    @staticmethod
    def get_interface_ip_addresses(interface, ip_cmd_json_data):
        """
        This method returns list with IP addresses on specific interface
        :param interface: interface name
        :param ip_cmd_json_data: output from command 'ip -j addresses', the same as in method 'get_ip_info'
        :return: list with IPs
        """
        ips = []
        for iface in ip_cmd_json_data:
            if iface['ifname'] == interface:
                for addr in iface['addr_info']:
                    ips.append(addr['local'])
                break
        return ips

    def get_interface_link_local_ipv6_addresses(self, interface, ip_cmd_json_data=None):
        """
        This method returns link-local IPv6 address for specific interface
        :param interface: interface name
        :param ip_cmd_json_data: optional - output from command 'ip -j addresses', if not provided - will get it
        :return: link-local ipv6 address
        """
        if not ip_cmd_json_data:
            ip_cmd_json_data = self.get_ip_info(ip_ver='6')
        iface_ips = self.get_interface_ip_addresses(interface, ip_cmd_json_data)
        linklocal_ipv6 = [ip for ip in iface_ips if ipaddress.IPv6Address(ip).is_link_local][0]
        return linklocal_ipv6