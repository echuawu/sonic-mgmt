import logging
import ipaddress

from ngts.helpers.config_db_utils import save_config_db_json, save_config_into_json

logger = logging.getLogger()


class SonicDhcpRelayCli:

    def __new__(cls, **kwargs):
        branch = kwargs['branch']
        engine = kwargs['engine']
        cli_obj = kwargs['cli_obj']

        supported_cli_classes = {'default': SonicDhcpRelayCliDefault(engine, cli_obj),
                                 'master': SonicDhcpRelayCliMaster(engine, cli_obj),
                                 '202012': SonicDhcpRelayCli202012(engine, cli_obj),
                                 '202111': SonicDhcpRelayCli202111(engine, cli_obj)}

        cli_class = supported_cli_classes.get(branch, supported_cli_classes['default'])
        cli_class_name = cli_class.__class__.__name__
        logger.info(f'Going to use DHCP relay CLI class: {cli_class_name}')

        return cli_class


class SonicDhcpRelayCliDefault:

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj

    def add_dhcp_relay(self, vlan, dhcp_server, **kwargs):
        """
        This method adding DHCP relay entry for VLAN interface
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return self.engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    def del_dhcp_relay(self, vlan, dhcp_server, **kwargs):
        """
        This method delete DHCP relay entry from VLAN interface
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return self.engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))

    def add_ipv4_dhcp_relay(self, vlan, dhcp_server):
        return self.engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    def del_ipv4_dhcp_relay(self, vlan, dhcp_server):
        return self.engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))

    def add_ipv6_dhcp_relay(self, vlan, dhcp_server):
        return self.engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    def del_ipv6_dhcp_relay(self, vlan, dhcp_server):
        return self.engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))

    def get_ipv4_dhcp_relay_cli_config_dict(self, cli_obj):
        return cli_obj.vlan.get_show_vlan_brief_parsed_output()

    def get_ipv6_dhcp_relay_cli_config_dict(self, cli_obj):
        return cli_obj.vlan.get_show_vlan_brief_parsed_output()

    @staticmethod
    def validate_dhcp_relay_cli_config_ipv4(vlan_brief_parsed_output, vlan, expected_dhcp_servers_list):
        """
        This method doing DHCP relay IPv4 CLI validation in "show vlan brief" output
        :param vlan_brief_parsed_output: dict, parsed output of cmd "show vlan brief"
        :param vlan: vlan in which we will do validation
        :param expected_dhcp_servers_list: list, expected DHCP relay servers
        :return: AssertionError in case of failure
        """
        for dhcp_server in expected_dhcp_servers_list:
            logger.info(f'Checking that DHCP relay: {dhcp_server} available in CLI config for VLAN: {vlan}')
            assert dhcp_server in vlan_brief_parsed_output[vlan]['dhcp_servers'], \
                f'Unable to find DHCP relay {dhcp_server} in "show vlan brief" output for VLAN {vlan}'

    @staticmethod
    def validate_dhcp_relay_cli_config_ipv6(vlan_brief_parsed_output, vlan, expected_dhcp_servers_list):
        """
        This method doing DHCP relay IPv6 CLI validation in "show vlan brief" output
        :param vlan_brief_parsed_output: dict, parsed output of cmd "show vlan brief"
        :param vlan: vlan in which we will do validation
        :param expected_dhcp_servers_list: list, expected DHCP relay servers
        :return: AssertionError in case of failure
        """
        for dhcp_server in expected_dhcp_servers_list:
            logger.info(f'Checking that DHCP relay: {dhcp_server} available in CLI config for VLAN: {vlan}')
            assert dhcp_server in vlan_brief_parsed_output[vlan]['dhcp_servers'], \
                f'Unable to find DHCP relay {dhcp_server} in "show vlan brief" output for VLAN {vlan}'


class SonicDhcpRelayCliMaster(SonicDhcpRelayCliDefault):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj

    def add_dhcp_relay(self, vlan, dhcp_server, **kwargs):
        """
        This method adding DHCP relay entry for VLAN interface
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        """
        ip_addr_version = ipaddress.ip_address(dhcp_server).version

        if ip_addr_version == 6:
            topology_obj = kwargs.get('topology_obj')
            self.add_ipv6_dhcp_relay(vlan, dhcp_server, topology_obj)
        else:
            self.add_ipv4_dhcp_relay(vlan, dhcp_server)

    def del_dhcp_relay(self, vlan, dhcp_server, **kwargs):
        """
        This method delete DHCP relay entry from VLAN interface
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        """
        ip_addr_version = ipaddress.ip_address(dhcp_server).version

        if ip_addr_version == 6:
            topology_obj = kwargs.get('topology_obj')
            self.del_ipv6_dhcp_relay(vlan, dhcp_server, topology_obj)
        else:
            self.del_ipv4_dhcp_relay(vlan, dhcp_server)

    def add_ipv6_dhcp_relay(self, vlan, dhcp_server, topology_obj):
        """
        This method adding DHCPv6 relay entry for VLAN interface using DHCPv6 json config
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        :param topology_obj: topology_obj
        """
        vlan_iface = 'Vlan{}'.format(vlan)

        config_db = self.cli_obj.general.get_config_db_from_running_config()

        if config_db.get('DHCP_RELAY'):
            available_dhcpv6_servers = config_db['DHCP_RELAY'].get(vlan_iface, {}).get('dhcpv6_servers', [])
            dhcpv6_servers_list = available_dhcpv6_servers + [dhcp_server]
            config = {'DHCP_RELAY': {vlan_iface: {'dhcpv6_servers': dhcpv6_servers_list}},
                      'VLAN': {vlan_iface: {'dhcpv6_servers': dhcpv6_servers_list}}
                      }
        else:
            config = {'DHCP_RELAY': {vlan_iface: {'dhcpv6_servers': [dhcp_server]}},
                      'VLAN': {vlan_iface: {'dhcpv6_servers': [dhcp_server]}}
                      }

        config_name = 'dhcpv6_relay.json'
        # Save config into JSON and upload to DUT
        path_to_config_on_dut = save_config_into_json(self.engine, config_dict=config, config_file_name=config_name)
        logger.info(f'Adding DHCP relay: {dhcp_server} for VLAN: {vlan}')
        self.engine.run_cmd(f'sudo config load -y {path_to_config_on_dut}')

    def del_ipv6_dhcp_relay(self, vlan, dhcp_server, topology_obj):
        """
        This method delete DHCPv6 relay entry from VLAN interface
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        :param topology_obj: topology_obj
        """
        vlan_iface = 'Vlan{}'.format(vlan)

        config_db = self.cli_obj.general.get_config_db_from_running_config()

        config_db = self.remove_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server)
        config_db = self.remove_vlan_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server)
        logger.info(f'Removing DHCP relay: {dhcp_server} from VLAN: {vlan}')

        # TODO: Once https://github.com/Azure/sonic-buildimage/issues/9679 fixed - remove "config reload -y" logic
        save_config_db_json(self.engine, config_db)
        branch = topology_obj.players['dut'].get('branch')
        self.cli_obj.general.reload_flow(topology_obj=topology_obj, reload_force=True)

    @staticmethod
    def remove_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server):
        """
        Remove DHCP_RELAY settings from config_db.json dictionary
        :param config_db: dict with config_db.json data
        :param vlan_iface: Vlan interface from which will be removed DHCPv6 relay settings
        :param dhcp_server: DHCPv6 server IP which will be removed
        :return: config_db dictionary with removed DHCPv6 relay settings
        """
        config_db['DHCP_RELAY'][vlan_iface]['dhcpv6_servers'].remove(dhcp_server)

        if not config_db['DHCP_RELAY'][vlan_iface]['dhcpv6_servers']:
            config_db['DHCP_RELAY'][vlan_iface].pop('dhcpv6_servers')

        if not config_db['DHCP_RELAY'][vlan_iface]:
            config_db['DHCP_RELAY'].pop(vlan_iface)

        if not config_db['DHCP_RELAY']:
            config_db.pop('DHCP_RELAY')

        return config_db

    @staticmethod
    def remove_vlan_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server):
        """
        Remove DHCPv6 relay settings from VLAN section in config_db.json
        :param config_db: dict with config_db.json data
        :param vlan_iface: Vlan interface from which will be removed DHCPv6 relay settings
        :param dhcp_server: DHCPv6 server IP which will be removed
        :return: config_db dictionary with removed DHCPv6 relay settings
        """
        config_db['VLAN'][vlan_iface]['dhcpv6_servers'].remove(dhcp_server)

        if not config_db['VLAN'][vlan_iface]['dhcpv6_servers']:
            config_db['VLAN'][vlan_iface].pop('dhcpv6_servers')

        return config_db

    def parse_show_dhcprelay_helper_ipv6_as_dict(self):
        """
        Parse output of command "show dhcprelay_helper ipv6" and return result as dict
        :param engine: ssh engine object
        :return: dict, example: {'Vlan690': ['6900::2', '6900::3'], 'Vlan691': ['6900::2']}
        """
        result = {}
        output = self.engine.run_cmd('show dhcprelay_helper ipv6')
        """
        Example of output:
        -------  -------
        Vlan690  6900::2
                 6900::3
        -------  -------

        -------  -------
        Vlan691  6900::2
        -------  -------
        """
        vlan = None
        for line in output.splitlines():
            if '----' not in line and line:
                # Example of splited_line : ['Vlan690', '6900::2'] or ['6900::3']
                splited_line = line.split()
                if len(splited_line) == 2:
                    vlan = splited_line[0]
                    relay_ip = splited_line[1]
                    result[vlan] = [relay_ip]
                else:
                    relay_ip = splited_line[0]
                    result[vlan].append(relay_ip)

        return result

    def get_ipv4_dhcp_relay_cli_config_dict(self, cli_obj):
        return cli_obj.vlan.get_show_vlan_brief_parsed_output()

    def get_ipv6_dhcp_relay_cli_config_dict(self, cli_obj):
        return cli_obj.dhcp_relay.parse_show_dhcprelay_helper_ipv6_as_dict()

    @staticmethod
    def validate_dhcp_relay_cli_config_ipv6(dhcprelay_helper_ipv6_output_dict, vlan, expected_dhcp_servers_list):
        """
        This method doing DHCP relay CLI IPv6 validation in "show dhcprelay_helper ipv6" output
        :param dhcprelay_helper_ipv6_output_dict: output of cmd "show dhcprelay_helper ipv6" parsed as dict
        :param vlan: vlan in which we will do validation
        :param expected_dhcp_servers_list: list, expected DHCP relay servers
        :return: AssertionError in case of failure
        """
        for dhcp_server in expected_dhcp_servers_list:
            vlan_iface = f'Vlan{vlan}'
            logger.info(f'Checking that DHCP relay: {dhcp_server} available in CLI config for VLAN: {vlan}')
            assert dhcp_server in dhcprelay_helper_ipv6_output_dict[vlan_iface], \
                f'Unable to find DHCP relay {dhcp_server} in "show dhcprelay_helper ipv6" output for VLAN {vlan}'


class SonicDhcpRelayCli202012(SonicDhcpRelayCliMaster):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj


class SonicDhcpRelayCli202111(SonicDhcpRelayCliMaster):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj
