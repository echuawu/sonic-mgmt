import logging

from ngts.cli_wrappers.common.vlan_clis_common import VlanCliCommon

logger = logging.getLogger()


class SonicVlanCli:

    def __new__(cls, **kwargs):
        branch = kwargs['branch']

        supported_cli_classes = {'default': SonicVlanCliDefault(),
                                 '202012': SonicVlanCli202012()}

        cli_class = supported_cli_classes.get(branch, supported_cli_classes['default'])
        cli_class_name = cli_class.__class__.__name__
        logger.info(f'Going to use VLAN CLI class: {cli_class_name}')

        return cli_class


class SonicVlanCliDefault(VlanCliCommon):

    @staticmethod
    def configure_vlan_and_add_ports(engine, vlan_info):
        """
        Method which adding VLAN and ports to VLAN on SONiC device
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        SonicVlanCliDefault.add_vlan(engine, vlan_info['vlan_id'])
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                SonicVlanCliDefault.add_port_to_vlan(engine, vlan_port, vlan_info['vlan_id'], mode)

    @staticmethod
    def delete_vlan_and_remove_ports(engine, vlan_info):
        """
        Method which remove ports from VLANs and VLANs on SONiC device
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                SonicVlanCliDefault.del_port_from_vlan(engine, vlan_port, vlan_info['vlan_id'])
        SonicVlanCliDefault.del_vlan(engine, vlan_info['vlan_id'])

    @staticmethod
    def add_vlan(engine, vlan):
        """
        Method which adding VLAN to SONiC dut
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan add {}".format(vlan))

    @staticmethod
    def del_vlan(engine, vlan):
        """
        Method which removing VLAN from SONiC dut
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan del {}".format(vlan))

    @staticmethod
    def add_port_to_vlan(engine, port, vlan, mode='trunk'):
        """
        Method which adding physical port to VLAN on SONiC dut
        :param engine: ssh engine object
        :param port: network port which should be VLAN member
        :param vlan: vlan ID
        :param mode: port mode - access or trunk
        :return: command output
        """
        if mode == 'trunk':
            return engine.run_cmd("sudo config vlan member add {} {}".format(vlan, port))
        elif mode == 'access':
            return engine.run_cmd("sudo config vlan member add --untagged {} {}".format(vlan, port))
        else:
            raise Exception('Incorrect port mode: "{}" provided, expected "trunk" or "access"')

    @staticmethod
    def del_port_from_vlan(engine, port, vlan):
        """
        Method which deleting physical port from VLAN on SONiC dut
        :param engine: ssh engine object
        :param port: network port which should be deleted from VLAN members
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan member del {} {}".format(vlan, port))

    @staticmethod
    def show_vlan_config(engine):
        """
        This method performs show vlan command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd("show vlan config")

    @staticmethod
    def shutdown_vlan(engine, vlan):
        """
        This method is to shutdown vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo ip link set dev Vlan{} down".format(vlan))

    @staticmethod
    def startup_vlan(engine, vlan):
        """
        This method is to startup vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo ip link set dev Vlan{} up".format(vlan))

    @staticmethod
    def disable_vlan_arp_proxy(engine, vlan):
        """
        This method is to disable arp proxy in vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan proxy_arp {} disabled".format(vlan), validate=True)

    @staticmethod
    def enable_vlan_arp_proxy(engine, vlan):
        """
        This method is to enable arp proxy in vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan proxy_arp {} enabled".format(vlan), validate=True)

    @staticmethod
    def show_vlan_brief(engine):
        """
        This method performs "show vlan brief"
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd("show vlan brief")

    @staticmethod
    def get_show_vlan_brief_parsed_output(engine, show_vlan_brief_output=None):
        """
        This method parses the "show vlan brief" output and returns a dictionary with the parsed data
        :param engine: ssh engine object
        :param show_vlan_brief_output: output from command "show vlan brief"
        :return: dictionary with parsed data
        """
        if not show_vlan_brief_output:
            show_vlan_brief_output = SonicVlanCliDefault.show_vlan_brief(engine)
        show_vlan_brief_parsed_dict = SonicVlanCliDefault.show_vlan_brief_parser(show_vlan_brief_output)
        return show_vlan_brief_parsed_dict

    @staticmethod
    def show_vlan_brief_parser(output, vlan_index=0, ip_addr_index=1, vlan_port_index=2, vlan_port_mode_index=3,
                               proxy_arp_index=4, dhcp_server_index=5, data_line_index=4):
        """
        This method doing parse for command "show vlan brief" output
        :param output: command "show vlan brief" output which should be parsed
        :param vlan_index: index for VLAN id in output list
        :param ip_addr_index: index for IP address in output list
        :param vlan_port_index: index for VLAN port in output list
        :param vlan_port_mode_index: index for VLAN port mode in output list
        :param proxy_arp_index: index for proxy ARP in output list
        :param dhcp_server_index: index for DHCP server in output list
        :param data_line_index: index from which data lines starts in output
        :return: dictionary with parsed data.

        Example:
        {'40': {'ips': ['4000::1/64', '40.0.0.1/24'],
                'ports': {'Ethernet236': 'tagged', 'PortChannel0002': 'tagged'},
                'dhcp_servers': [], 'proxy_arp': 'disabled'},
        '69': {'ips': ['69.0.0.1/24'..... ]}}
        """
        result_dict = {}

        # Read data without headers
        data_lines = output.splitlines()[data_line_index:]

        vlan = None
        vlan_ips = []
        vlan_ports = {}
        dhcp_servers = []
        proxy_arp = None

        for line in data_lines:
            # Skip lines like: +-----------+--------------+----- which does not
            # have data, analyze only lines with data
            splited_data_line = line.split('|')[1:]
            if splited_data_line:
                vlan_id = splited_data_line[vlan_index].strip()
                if vlan_id:
                    # If next vlan data started - clean previous data
                    if vlan != vlan_id:
                        vlan = None
                        vlan_ips = []
                        vlan_ports = {}
                        dhcp_servers = []
                        proxy_arp = None

                    vlan = vlan_id
                    proxy_arp = splited_data_line[proxy_arp_index].strip()

                vlan_ip = splited_data_line[ip_addr_index].strip()
                vlan_port = splited_data_line[vlan_port_index].strip()
                dhcp_server = splited_data_line[dhcp_server_index].strip()

                if vlan_ip:
                    vlan_ips.append(vlan_ip)
                if vlan_port:
                    vlan_ports[vlan_port] = splited_data_line[vlan_port_mode_index].strip()
                if dhcp_server:
                    dhcp_servers.append(dhcp_server)

                result_dict[vlan] = {'ips': vlan_ips, 'ports': vlan_ports, 'dhcp_servers': dhcp_servers,
                                     'proxy_arp': proxy_arp}

        return result_dict


class SonicVlanCli202012(SonicVlanCliDefault):

    @staticmethod
    def get_show_vlan_brief_parsed_output(engine, show_vlan_brief_output=None):
        """
        This method parses the "show vlan brief" output and returns a dictionary with the parsed data
        :param engine: ssh engine object
        :param show_vlan_brief_output: output from command "show vlan brief"
        :return: dictionary with parsed data
        """
        if not show_vlan_brief_output:
            show_vlan_brief_output = SonicVlanCli202012.show_vlan_brief(engine)
        show_vlan_brief_parsed_dict = SonicVlanCli202012.show_vlan_brief_parser(show_vlan_brief_output,
                                                                                proxy_arp_index=5,
                                                                                dhcp_server_index=4)
        return show_vlan_brief_parsed_dict
