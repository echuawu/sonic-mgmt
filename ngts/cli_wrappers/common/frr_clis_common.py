import json

from retry import retry
from ngts.cli_wrappers.interfaces.interface_frr_clis import FrrCliInterface


class FrrCliCommon(FrrCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self, engine):
        self.engine = engine

    def run_config_frr_cmd(self, frr_command):
        """
        Run FRR command
        :param frr_command: string or list with FRR commands
        :return: cli output
        """
        cmd = self.get_frr_configuration_command(frr_command)
        return self.engine.run_cmd(cmd)

    def run_show_frr_cmd(self, frr_command, is_json=True):
        """
        Run FRR show command
        :param frr_command: string with FRR command
        :param is_json: is need JSON output - then True, if not - False
        :return: cli output
        """
        if is_json:
            frr_command += ' json'

        cmd_output = self.run_config_frr_cmd(frr_command)
        if is_json:
            cmd_output = json.loads(cmd_output)

        return cmd_output

    @staticmethod
    def get_frr_configuration_command(frr_command):
        """
        Get FRR configuration command
        :param frr_command: string or list with FRR commands
        :return: string with FRR configuration command which can be executed in BASH
        """
        cmd = 'sudo vtysh'
        if isinstance(frr_command, list):
            for frr_cmd in frr_command:
                cmd += ' -c "{}"'.format(frr_cmd)
        else:
            cmd += ' -c "{}"'.format(frr_command)
        return cmd

    def get_l2vpn_evpn_route(self, is_json=True):
        """
        Run FRR command "show bgp l2vpn evpn route"
        :param is_json: is need JSON output - then True, if not - False
        :return: cli output string or dict
        """
        cmd = 'show bgp l2vpn evpn route'
        return self.run_show_frr_cmd(cmd, is_json)

    def get_l2vpn_evpn_route_type_multicast(self, is_json=True):
        """
        Run FRR command "show bgp l2vpn evpn route type multicast"
        :param is_json: is need JSON output - then True, if not - False
        :return: cli output string or dict
        """
        cmd = 'show bgp l2vpn evpn route type multicast'
        return self.run_show_frr_cmd(cmd, is_json)

    def get_l2vpn_evpn_route_type_macip(self, is_json=True):
        """
        Run FRR command "show bgp l2vpn evpn route type macip"
        :param is_json: is need JSON output - then True, if not - False
        :return: cli output string or dict
        """
        cmd = 'show bgp l2vpn evpn route type macip'
        return self.run_show_frr_cmd(cmd, is_json)

    def get_l2vpn_evpn_route_type_prefix(self, is_json=True):
        """
        Run FRR command "show bgp l2vpn evpn route type prefix"
        :param is_json: is need JSON output - then True, if not - False
        :return: cli output string or dict
        """
        cmd = 'show bgp l2vpn evpn route type prefix'
        return self.run_show_frr_cmd(cmd, is_json)

    def get_bgp_neighbor_status(cls, neighbor):
        """
        Run FRR command "show bgp neighbor x.x.x.x|interface"
        :param neighbor: neighbor ip address or unnumbered interface
        :return: cli output string
        """
        cmd = f"show bgp neighbor {neighbor}"
        return cls.run_config_frr_cmd(cmd)

    def bgp_neighbor(self, neighbor_ip, status):
        """
        Shutdown BGP neighbor x.x.x.x
        :param neighbor_ip: neighbor ip address
        :param status: enable or disable bgp neighbor
        """
        config_mode_cmd = 'configure terminal'
        bgp_config_mode_cmd = 'router bgp'
        if status == 'disable':
            bgp_neighbor_config = f"neighbor {neighbor_ip} shutdown"
        elif status == 'enable':
            bgp_neighbor_config = f"no neighbor {neighbor_ip} shutdown"
        else:
            bgp_neighbor_config = ''
        cmd_list = [config_mode_cmd, bgp_config_mode_cmd, bgp_neighbor_config]
        self.run_config_frr_cmd(cmd_list)

    def show_bgp_ipv4_route(self, network=None):
        """
        This method is used to get the output of command 'show bgp ipv4 x.x.x.x'
        :param network: ip network, such as 1.1.1.0
        :return: command output
        """
        cmd = f"show bgp ipv4 {network}"
        return self.run_config_frr_cmd(cmd)

    def validate_bgp_ecmp_route(self, network_nexthop_list):
        """
        This method is used to validate the bgp ecmp route and its nexthops
        :param network_nexthop_list: network and nexthop list, for example ['30.0.0.2', ('1.1.1.1','2.2.2.1')]
        """
        network = network_nexthop_list[0]
        nexthops = network_nexthop_list[1]
        bgp_ipv4_ecmp_routes = self.show_bgp_ipv4_route(network)
        err_msg = 'Expected ECMP route {} nexthop {} \n not found in: \n{}'

        for nexthop in nexthops:
            expected_route = f"{nexthop} from {nexthop} ({network})"
            assert expected_route in bgp_ipv4_ecmp_routes, err_msg.format(network, nexthop, bgp_ipv4_ecmp_routes)

    def save_frr_configuration(self):
        """
        Save FRR configuration
        :return: cli output
        """
        cmd = 'write memory'
        return self.run_config_frr_cmd(cmd)

    @staticmethod
    def validate_type_2_route(type_2_info, route_mac, peer_ip, peer_rd, route_ip=None):
        """
        Validate type-2 route in FRR output
        :param type_2_info: dictionary with cmd "show bgp l2vpn evpn route type macip" output
        :param route_mac: MAC address which we expect in type-2 route
        :param peer_ip: BGP peer IP address which we expect in type-2 route
        :param peer_rd: BGP peer RD
        :param route_ip: IP address which we expect in type-2 route
        """
        route_type = 2
        eth_tag = 0
        mac_len = 48
        ip_len = 32
        expected_type_2_route = '[{}]:[{}]:[{}]:[{}]'.format(route_type, eth_tag, mac_len, route_mac)
        err_msg = 'Expected Type-2 route: {} \n not found in: \n{}'
        if route_ip:
            expected_type_2_route += ':[{}]:[{}]'.format(ip_len, route_ip)
            assert expected_type_2_route in type_2_info['{}:{}'.format(peer_ip, peer_rd)], \
                err_msg.format(expected_type_2_route, type_2_info)
        else:
            assert expected_type_2_route in type_2_info['{}:{}'.format(peer_ip, peer_rd)], \
                err_msg.format(expected_type_2_route, type_2_info)

    @staticmethod
    def validate_type_3_route(type_3_info, route_ip, peer_ip, peer_rd, learned=True):
        """
        Validate type-3 route in FRR output
        :param type_3_info: dictionary with cmd "show bgp l2vpn evpn route type multicast" output
        :param route_ip: IP address which we expect in type-3 route
        :param peer_ip: BGP peer IP address which we expect in type-3 route
        :param peer_rd: BGP peer RD
        :param learned: A flag to show the route is supposed to be learned or not
        """
        route_type = 3
        eth_tag = 0
        ip_len = 32
        expected_type_3_route = '[{}]:[{}]:[{}]:[{}]'.format(route_type, eth_tag, ip_len, route_ip)
        err_msg = 'Expected Type-3 route: {} \n not found in: \n{}'.format(expected_type_3_route, type_3_info)
        if learned:
            assert expected_type_3_route in type_3_info['{}:{}'.format(peer_ip, peer_rd)], err_msg
        else:
            assert expected_type_3_route not in type_3_info, err_msg

    @staticmethod
    def validate_type_5_route():
        pass

    @retry(Exception, tries=20, delay=2)
    def validate_bgp_neighbor_established(cls, neighbor, establish=True):
        """
        Validate BGP neighbor establish status
        :param neighbor: neighbor ip or unnumbered interface
        :param establish: A flag to show it is supposed to be established or not
        """
        neighbor_info = cls.get_bgp_neighbor_status(neighbor)
        expected_establish_status = 'BGP state = Established'
        err_msg_establish = 'Expected BGP neighbor established not found in: \n{}'.format(neighbor_info)
        err_msg_not_establish = 'No expected BGP neighbor established found in: \n{}'.format(neighbor_info)
        if establish:
            assert expected_establish_status in neighbor_info, err_msg_establish
        else:
            assert expected_establish_status not in neighbor_info, err_msg_not_establish

    def config_bgp_unnumbered_mode(self, bgp_id, neighbor_ip, interface):
        """
        Configure BGP unnumbered mode based on an ordinary BGP session
        :param bgp_id: bgp session number
        :param neighbor_ip: neighbor ip address
        :param interface: interface that would be used to configure unnumbered mode
        """
        config_mode_cmd = 'configure terminal'
        bgp_config_mode_cmd = 'router bgp'
        del_bgp_neighbor_cmd = f"no neighbor {neighbor_ip} remote-as {bgp_id}"
        config_bgp_unnumbered_cmd = f"neighbor {interface} interface  remote-as {bgp_id}"
        enter_l2vpn_evpn_address_family_cmd = "address-family l2vpn evpn"
        config_bgp_unnumbered_neighbor_activate_cmd = f"neighbor {interface} activate"
        cmd_list = [
            config_mode_cmd,
            bgp_config_mode_cmd,
            del_bgp_neighbor_cmd,
            config_bgp_unnumbered_cmd,
            enter_l2vpn_evpn_address_family_cmd,
            config_bgp_unnumbered_neighbor_activate_cmd
        ]
        self.run_config_frr_cmd(cmd_list)

    def clean_bgp_unnumbered_mode(self, bgp_id, neighbor_ip, interface):
        """
        Clean BGP unnumbered mode and then recover default BGP neighbor configuration
        :param bgp_id: bgp session number
        :param neighbor_ip: neighbor ip address
        :param interface: interface that would be used to configure unnumbered mode
        """
        config_mode_cmd = 'configure terminal'
        bgp_config_mode_cmd = 'router bgp'
        del_bgp_unnumbered_cmd = f"no neighbor {interface} interface  remote-as {bgp_id}"
        config_bgp_neighbor_cmd = f"neighbor {neighbor_ip} remote-as {bgp_id}"
        enter_l2vpn_evpn_address_family_cmd = "address-family l2vpn evpn"
        config_bgp_neighbor_activate_cmd = f"neighbor {neighbor_ip} activate"
        cmd_list = [
            config_mode_cmd,
            bgp_config_mode_cmd,
            del_bgp_unnumbered_cmd,
            config_bgp_neighbor_cmd,
            enter_l2vpn_evpn_address_family_cmd,
            config_bgp_neighbor_activate_cmd
        ]
        self.run_config_frr_cmd(cmd_list)
