import json

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
        assert expected_type_2_route in type_2_info['{}:{}'.format(peer_ip, peer_rd)], \
            err_msg.format(expected_type_2_route, type_2_info)

        if route_ip:
            expected_type_2_route += ':[{}]:[{}]'.format(ip_len, route_ip)
            assert expected_type_2_route in type_2_info['{}:{}'.format(peer_ip, peer_rd)], \
                err_msg.format(expected_type_2_route, type_2_info)

    @staticmethod
    def validate_type_3_route(type_3_info, route_ip, peer_ip, peer_rd):
        """
        Validate type-3 route in FRR output
        :param type_3_info: dictionary with cmd "show bgp l2vpn evpn route type multicast" output
        :param route_ip: IP address which we expect in type-2 route
        :param peer_ip: BGP peer IP address which we expect in type-2 route
        :param peer_rd: BGP peer RD
        """
        route_type = 3
        eth_tag = 0
        ip_len = 32
        expected_type_3_route = '[{}]:[{}]:[{}]:[{}]'.format(route_type, eth_tag, ip_len, route_ip)
        err_msg = 'Expected Type-3 route: {} \n not found in: \n{}'.format(expected_type_3_route, type_3_info)
        assert expected_type_3_route in type_3_info['{}:{}'.format(peer_ip, peer_rd)], err_msg

    @staticmethod
    def validate_type_5_route():
        pass
