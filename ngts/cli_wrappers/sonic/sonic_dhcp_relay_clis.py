import logging
import ipaddress
import time

from retry.api import retry_call

from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.helpers.config_db_utils import save_config_db_json, save_config_into_json

logger = logging.getLogger()


class SonicDhcpRelayCli:

    def __new__(cls, **kwargs):
        topology = kwargs['topology']
        branch = topology.players['dut'].get('branch')

        supported_branches = {'default': SonicDhcpRelayCliDefault(),
                              'master': SonicDhcpRelayCliMaster(),
                              '202012': SonicDhcpRelayCli202012(),
                              '202111': SonicDhcpRelayCli202111()}

        if supported_branches.get(branch):
            logger.info(f'Going to use custom DHCP relay CLI class for SONiC branch: {branch}')
        else:
            logger.warning(f'Can not get DHCP relay CLI class for SONiC branch: {branch}, '
                           f'default DHCP relay CLI class will be used.')
        return supported_branches.get(branch, supported_branches['default'])


class SonicDhcpRelayCliDefault:

    @staticmethod
    def add_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method adding DHCP relay entry for VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    @staticmethod
    def del_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method delete DHCP relay entry from VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))

    @staticmethod
    def add_ipv4_dhcp_relay(engine, vlan, dhcp_server):
        return engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    @staticmethod
    def del_ipv4_dhcp_relay(engine, vlan, dhcp_server):
        return engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))

    @staticmethod
    def add_ipv6_dhcp_relay(engine, vlan, dhcp_server):
        return engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    @staticmethod
    def del_ipv6_dhcp_relay(engine, vlan, dhcp_server):
        return engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))


class SonicDhcpRelayCliMaster(SonicDhcpRelayCliDefault):

    @staticmethod
    def add_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method adding DHCP relay entry for VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        """
        ip_addr_version = ipaddress.ip_address(dhcp_server).version

        if ip_addr_version == 6:
            SonicDhcpRelayCliMaster.add_ipv6_dhcp_relay(engine, vlan, dhcp_server)
        else:
            SonicDhcpRelayCliMaster.add_ipv4_dhcp_relay(engine, vlan, dhcp_server)

    @staticmethod
    def del_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method delete DHCP relay entry from VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        """
        ip_addr_version = ipaddress.ip_address(dhcp_server).version

        if ip_addr_version == 6:
            SonicDhcpRelayCliMaster.del_ipv6_dhcp_relay(engine, vlan, dhcp_server)
        else:
            SonicDhcpRelayCliMaster.del_ipv4_dhcp_relay(engine, vlan, dhcp_server)

    @staticmethod
    def add_ipv6_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method adding DHCPv6 relay entry for VLAN interface using DHCPv6 json config
        :param engine: ssh engine object
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        """
        vlan_iface = 'Vlan{}'.format(vlan)

        config_db = SonicGeneralCli.get_config_db_from_running_config(engine)

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
        path_to_config_on_dut = save_config_into_json(engine, config_dict=config, config_file_name=config_name)
        logger.info(f'Adding DHCP relay: {dhcp_server} for VLAN: {vlan}')
        engine.run_cmd(f'sudo config load -y {path_to_config_on_dut}')

        # TODO: Once https://github.com/Azure/sonic-buildimage/issues/9679 fixed - remove "config reload -y" logic
        SonicGeneralCli.save_configuration(engine)
        SonicGeneralCli.reload_configuration(engine)
        SonicGeneralCli.verify_dockers_are_up(engine)

        first_interface = 'Ethernet0'
        delay_after_first_iface_up = 5
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[engine, [first_interface]], tries=12,
                   delay=5, logger=logger)
        time.sleep(delay_after_first_iface_up)

    @staticmethod
    def del_ipv6_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method delete DHCPv6 relay entry from VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        """
        vlan_iface = 'Vlan{}'.format(vlan)

        config_db = SonicGeneralCli.get_config_db_from_running_config(engine)

        config_db = SonicDhcpRelayCliMaster.remove_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server)
        config_db = SonicDhcpRelayCliMaster.remove_vlan_dhcp_relay_in_config_db(config_db, vlan_iface, dhcp_server)
        logger.info(f'Removing DHCP relay: {dhcp_server} from VLAN: {vlan}')

        # TODO: Once https://github.com/Azure/sonic-buildimage/issues/9679 fixed - remove "config reload -y" logic
        save_config_db_json(engine, config_db)
        SonicGeneralCli.reload_configuration(engine)
        SonicGeneralCli.verify_dockers_are_up(engine)

        first_interface = 'Ethernet0'
        delay_after_first_iface_up = 5
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[engine, [first_interface]], tries=12,
                   delay=5, logger=logger)
        time.sleep(delay_after_first_iface_up)

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


class SonicDhcpRelayCli202012(SonicDhcpRelayCliMaster):
    pass


class SonicDhcpRelayCli202111(SonicDhcpRelayCliMaster):
    pass
