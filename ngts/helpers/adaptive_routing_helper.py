import logging
import os
import re

from retry import retry
from functools import partial
from ngts.tests.conftest import get_dut_loopbacks
from ngts.tests.nightly.adaptive_routing.constants import ArConsts
from ngts.constants.constants import AppExtensionInstallationConstants
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker

logger = logging.getLogger()


class ArHelper:

    def enable_doai_service(self, cli_objects, request=None):
        """
        This method is to enable doAI service
        :param cli_objects: cli_objects fixture
        :param request: pytest builtin
        """
        if request:
            logger.info('Add disabling DoAI feature into finalizer')
            cleanup = partial(self.disable_doai_service, cli_objects)
            request.addfinalizer(cleanup)
        logger.info('Enable doAI feature')
        cli_objects.dut.general.set_feature_state(AppExtensionInstallationConstants.DOAI, 'enabled')

    def disable_doai_service(self, cli_objects):
        """
        This method is to disable doAI service
        :param cli_objects: cli_objects fixture
        """
        logger.info('Disable doAI feature')
        cli_objects.dut.general.set_feature_state(AppExtensionInstallationConstants.DOAI, 'disabled')

    def enable_ar_function(self, cli_objects, request=None):
        """
        This method is to enable AR function
        :param cli_objects: cli_objects fixture
        :param request: pytest builtin
        """
        if request:
            logger.info('Add disabling AR function into finalizer')
            cleanup = partial(self.disable_ar, cli_objects)
            request.addfinalizer(cleanup)
        logger.info('Enable AR function')
        cli_objects.dut.ar.enable_ar_function()

    def disable_ar(self, cli_objects):
        """
        This method is to disable AR function
        :param cli_objects: cli_objects fixture
        """
        logger.info('Disable AR function')
        cli_objects.dut.ar.disable_ar_function()

    def enable_ar_port(self, cli_objects, port_list, port_util_percent=None, request=None, restart_swss=False):
        """
        This method is to enable AR function at DUT port
        :param cli_objects: cli_objects fixture
        :param port_list: list of DUT ports where AR must be enabled
        :param port_util_percent: port util percent to be configured at port (0-100)
        :param request: pytest builtin
        :param restart_swss: if True swss service and all dockers will be restarted
        """
        if request:
            logger.info('Add disabling AR function into finalizer')
            cleanup = partial(self.disable_ar_port, cli_objects, port_list)
            request.addfinalizer(cleanup)
        logger.info(f'Enable AR on {port_list}')
        for port in port_list:
            cli_objects.dut.ar.enable_ar_port(port, port_util_percent, restart_swss=restart_swss)

    def config_save_reload(self, cli_objects, topology_obj, reload_force=False):
        """
        This method is to save configuration and reload
        :param cli_objects: cli_objects fixture
        :param topology_obj: topology_obj fixture
        :param reload_force: adds -f option to command
        """
        cli_objects.dut.general.save_configuration()
        cli_objects.dut.general.reload_flow(topology_obj=topology_obj, reload_force=reload_force)

    def disable_ar_port(self, cli_objects, port_list):
        """
        This method is to disable AR function at DUT port
        :param cli_objects: cli_objects fixture
        :param port_list: list of DUT ports where AR must be disabled
        """
        logger.info('Disable AR function')
        for port in port_list:
            cli_objects.dut.ar.disable_ar_port(port)

    def add_dummy_vlan_intf(self, cli_objects, request=None):
        """
        This method is to add dummy vlan interface
        :param cli_objects: cli_objects fixture
        :param request: pytest builtin
        """
        if request:
            logger.info('Add removing vlan interface into finalizer')
            cleanup = partial(self.del_dummy_vlan_intf, cli_objects)
            request.addfinalizer(cleanup)
        logger.info(f'Add vlan interface with vlan {ArConsts.DUMMY_VLAN} ip {ArConsts.DUMMY_VLAN_IP}')
        cli_objects.dut.vlan.add_vlan(ArConsts.DUMMY_VLAN)
        cli_objects.dut.ip.add_ip_to_interface(ArConsts.DUMMY_VLAN_INTF, ArConsts.DUMMY_VLAN_IP)

    def del_dummy_vlan_intf(self, cli_objects):
        """
        This method is to remove dummy vlan interface
        :param cli_objects: cli_objects fixture
        """
        logger.info(f'Delete vlan interface with vlan {ArConsts.DUMMY_VLAN} ip {ArConsts.DUMMY_VLAN_IP}')
        cli_objects.dut.ip.del_ip_from_interface(ArConsts.DUMMY_VLAN_INTF, ArConsts.DUMMY_VLAN_IP)
        cli_objects.dut.vlan.del_vlan(ArConsts.DUMMY_VLAN)

    def add_lacp_intf(self, cli_objects, topology_obj, request=None):
        """
        This method is to add LACP interface
        :param cli_objects: cli_objects fixture
        :param topology_obj: topology_obj fixture
        :param request: pytest builtin
        """
        lb = get_dut_loopbacks(topology_obj)
        if request:
            logger.info('Add removing lag interface into finalizer')
            cleanup = partial(self.del_lacp_intf, cli_objects, lb[0][0])
            request.addfinalizer(cleanup)
        logger.info(f'Add lag interface {ArConsts.DUMMY_LAG_INTF} with member port {lb[0][0]}')
        cli_objects.dut.lag.create_lag_interface(ArConsts.DUMMY_LAG_INTF)
        cli_objects.dut.lag.add_port_to_port_channel(lb[0][0], ArConsts.DUMMY_LAG_INTF)

    def del_lacp_intf(self, cli_objects, port):
        """
        This method is to delete LACP interface
        :param cli_objects: cli_objects fixture
        :param port: port to be deleted from LAG
        """
        logger.info(f'Remove port {port} from lag {ArConsts.DUMMY_LAG_INTF}')
        cli_objects.dut.lag.delete_port_from_port_channel(port, ArConsts.DUMMY_LAG_INTF)
        cli_objects.dut.lag.delete_lag_interface(ArConsts.DUMMY_LAG_INTF)

    def config_ecmp_ports_speed_to_10G(self, cli_objects, interfaces, request=None):
        """
        This method is to config ports speed to 10G in ecmp group
        :param cli_objects: cli_objects fixture
        :param interfaces: interfaces fixture
        :param request: pytest builtin
        """
        logger.info(f'Get original port speed of {interfaces.dut_hb_1, interfaces.dut_hb_2}')
        original_intf_speeds = cli_objects.dut.interface.get_interfaces_speed(
            [interfaces.dut_hb_1, interfaces.dut_hb_2])
        if request:
            logger.info('Add disabling AR port into finalizer')
            cleanup = partial(self.restore_ecmp_ports_speed, cli_objects, original_intf_speeds)
            request.addfinalizer(cleanup)

        logger.info('Config port speed to 10G')
        speed = '10000'
        cli_objects.dut.interface.set_interface_speed(interfaces.dut_hb_1, speed)
        cli_objects.dut.interface.set_interface_speed(interfaces.dut_hb_2, speed)

    def restore_ecmp_ports_speed(self, cli_objects, original_intf_speeds):
        """
        This method is to config ports speed to original in ecmp group
        :param cli_objects: cli_objects fixture
        :param original_intf_speeds: original interface speed
        """
        logger.info('Restore port speed')
        cli_objects.dut.interface.set_interfaces_speed(original_intf_speeds)

    def add_dummy_interface_hb(self, cli_objects, request=None):
        """
        This method is to add dummy interface to hb
        :param cli_objects: cli_objects fixture
        :param request: pytest builtin
        """
        if request:
            logger.info('Add removing dummy interface into finalizer')
            cleanup = partial(self.del_dummy_interface_hb, cli_objects, ArConsts.DUMMY_INTF['name'])
            request.addfinalizer(cleanup)
        logger.info(f'Configure dummy interface: {ArConsts.DUMMY_INTF["name"]}')
        cli_objects.hb.interface.add_interface(ArConsts.DUMMY_INTF['name'], 'dummy')
        cli_objects.hb.ip.add_ip_to_interface(ArConsts.DUMMY_INTF['name'], ArConsts.DUMMY_INTF['ipv4_addr'],
                                              ArConsts.DUMMY_INTF['ipv4_mask'])
        cli_objects.hb.ip.add_ip_to_interface(ArConsts.DUMMY_INTF['name'], ArConsts.DUMMY_INTF['ipv6_addr'],
                                              ArConsts.DUMMY_INTF['ipv6_mask'])
        cli_objects.hb.interface.enable_interface(ArConsts.DUMMY_INTF['name'])

    def del_dummy_interface_hb(self, cli_objects, name):
        """
        This method is to delete dummy interface to hb
        :param cli_objects: cli_objects fixture
        :param name: interface name
        """
        cli_objects.hb.interface.del_interface(name)

    @retry(Exception, tries=10, delay=10)
    def verify_bgp_neighbor(self, cli_objects):
        """
        This method is to verify bgp neighbors
        :param cli_objects: cli_objects fixture
        """
        for neighbor in [
            ArConsts.V4_CONFIG['ha_dut_1'],
            ArConsts.V4_CONFIG['hb_dut_1'],
            ArConsts.V4_CONFIG['hb_dut_2'],
            ArConsts.V6_CONFIG['ha_dut_1'],
            ArConsts.V6_CONFIG['hb_dut_1'],
            ArConsts.V6_CONFIG['hb_dut_2'],
        ]:
            logger.info(f'Validate BGP neighbor {neighbor} established')
            cli_objects.dut.frr.validate_bgp_neighbor_established(neighbor)

    def assert_for_ecmp_routes(self, route, route_next_hops, intf):
        """
        This method is to get next hops for routes
        :param route: route for which ecmp group wll be check
        :param route_next_hops: route_next_hops for route
        :param intf: interface to check
        """
        assert intf in route_next_hops, f'ECMP Next hop for route {route} is incorrect or not available'

    def verify_ecmp_route(self, cli_objects, interfaces):
        """
        Check the ECMP route and its nexthop interface correctness
        :param cli_objects: cli_objects fixture
        :param interfaces: interfaces where ecmp routes will be verified
        Route example:
        B>* 10.0.0.0/24 [200/0] via 2.2.2.3, Ethernet64, weight 1, 01:24:40
          *                     via 3.3.3.3, Ethernet124, weight 1, 01:24:40

        B>* 5000::/64 [200/0] via fe80::e42:a1ff:feb4:ca48, Ethernet64, weight 1, 01:24:51
          *                   via fe80::e42:a1ff:feb4:ca49, Ethernet124, weight 1, 01:24:51
        """
        parsed_ipv4_route_output = cli_objects.dut.route.show_ip_route(is_json=True)
        parsed_ipv6_route_output = cli_objects.dut.route.show_ip_route(ipv6=True, is_json=True)
        ipv4_route_next_hops = cli_objects.dut.route.get_next_hops(parsed_ipv4_route_output[ArConsts.V4_CONFIG['ipv4_network']])
        ipv6_route_next_hops = cli_objects.dut.route.get_next_hops(parsed_ipv6_route_output[ArConsts.V6_CONFIG['ipv6_network']])

        route_nexthops_intf_list = [
            [ArConsts.DUMMY_INTF['ipv4_network'], ipv4_route_next_hops['intf'], interfaces.dut_hb_1],
            [ArConsts.DUMMY_INTF['ipv4_network'], ipv4_route_next_hops['intf'], interfaces.dut_hb_2],
            [ArConsts.DUMMY_INTF['ipv6_network'], ipv6_route_next_hops['intf'], interfaces.dut_hb_1],
            [ArConsts.DUMMY_INTF['ipv6_network'], ipv6_route_next_hops['intf'], interfaces.dut_hb_2],
        ]
        for route_nexthops_intf in route_nexthops_intf_list:
            route = route_nexthops_intf[0]
            nexthop_intfs = route_nexthops_intf[1]
            intf = route_nexthops_intf[2]
            self.assert_for_ecmp_routes(route, nexthop_intfs, intf)

    @retry(Exception, tries=10, delay=2)
    def get_tx_port_in_ecmp(self, cli_objects, port_list, packet_threshold):
        """
        This method is to get next hops for routes
        :param cli_objects: cli_objects fixture
        :param port_list: list of port to be candidates to receive traffic
        :param packet_threshold: packet_threshold
        :return: port to which RoCE traffic must be send
        """
        interface_counters_dict = self.get_interfaces_counters(cli_objects, port_list, "TX_OK")
        for port in port_list:
            if interface_counters_dict[port] >= packet_threshold:
                logger.info(f'Checking {port}, the TX counter is \
                {interface_counters_dict[port]}, need to be at least {packet_threshold}')
                return port

    def search_by_name(self, name, cmd_output, find_all=False):
        """
        This method is to search value by name in command output
        :param name: parameter name
        :param cmd_output: command output to search in
        :param find_all: find all matches by name if True
        :return: find value
        """
        pattern = f"({name}:?)\\s*(.+)"
        if find_all:
            return re.findall(pattern, cmd_output)
        return re.search(pattern, cmd_output).group(2)

    def get_ports_profile_configuration(self, cmd_output):
        """
        This method is to find all values for Ethernet ports
        :param cmd_output: command output to search in
        :return: tuple of port name, found value
        """
        return re.findall("(Ethernet\\d+)\\s+(\\d+)", cmd_output)

    def get_ar_configuration(self, cli_objects, profile_names):
        """
        This method is to get AR configured at DUR
        :param cli_objects: cli_objects fixture
        :param profile_names: list of profiles available for AR
        :return: dictionary which describes output of "show ar config"
        Return example:
        {
        'Global':
            {'DoAI state': 'enabled', 'AR state': 'enabled', 'AR active profile': 'profile0'},
        'Profiles':
            {'profile0':
                {'mode': 'free', 'busy_threshold': '0', 'free_threshold': '4',
                'congestion_th_low (Cells)': '200', 'congestion_th_medium (Cells)': '1000',
                'congestion_th_high (Cells)': '10000', 'from_shaper_enable': 'true', 'from_shaper (* 100 ns)': '10',
                'to_shaper_enable': 'N/A', 'to_shaper (* 100 ns)': 'N/A', 'ecmp_size': '64', 'elephant_enable': 'false'}
            },
        'Ports':
            {'Ethernet128': '70', 'Ethernet252': '70'}
        }
        """
        # Get show ar config output
        show_ar_config_output = cli_objects.dut.ar.show_ar_config()
        # Get Global values
        ar_result_dict = {}
        global_dict = {
            ArConsts.DOAI_STATE: self.search_by_name(ArConsts.DOAI_STATE, show_ar_config_output),
            ArConsts.AR_STATE: self.search_by_name(ArConsts.AR_STATE, show_ar_config_output),
            ArConsts.AR_ACTIVE_PROFILE: self.search_by_name(ArConsts.AR_ACTIVE_PROFILE, show_ar_config_output)
        }
        ar_result_dict[ArConsts.AR_GLOBAL] = global_dict
        # Get profiles values
        profiles_dicts = {}
        for index, profile in enumerate(profile_names):
            profiles_dicts.setdefault(profile, {})
            for parameter in ArConsts.AR_PROFILE_KEYS_LIST:
                key, value = self.search_by_name(parameter, show_ar_config_output, find_all=True)[index]
                profiles_dicts[profile].update({key: value})
        ar_result_dict[ArConsts.AR_PROFILE_GLOBAL] = profiles_dicts
        # Get Ports dict values
        port_util_value = self.get_ports_profile_configuration(show_ar_config_output)
        ar_result_dict[ArConsts.AR_PORTS_GLOBAL] = dict(port_util_value)
        return ar_result_dict

    def send_and_validate_traffic(self, player, sender, sender_intf, sender_pkt_format, sender_count, sendpfast=False,
                                  mbps=None, loop=None, timeout=None):
        """
        This method is used to send then validate traffic
        :param player: player
        :param sender: sender, such as 'ha', 'hb'
        :param sender_intf: sender interface
        :param sender_pkt_format: packet to send
        :param sender_count: number of packets to send
        sendpfast: use sendpfast method to send traffic
        mbps: mega bit per second traffic to be send
        loop: number of times packet to be send
        timeout: timeout to be set for sending traffic
        """
        traffic_validation = {'sender': sender,
                              'send_args': {'interface': sender_intf,
                                            'packets': sender_pkt_format,
                                            'count': sender_count
                                            }
                              }
        send_fast = {
            'send_method': 'sendpfast',
            'mbps': mbps,
            'loop': loop,
            'timeout': timeout
        }

        if sendpfast:
            traffic_validation['send_args'].update(send_fast)
        logger.info(f"Traffic parameters: {traffic_validation}")
        ScapyChecker(player, traffic_validation).run_validation()

    def get_received_port(self, interfaces, original_tx_port):
        """
        This method is used to get port to receive traffic
        :param interfaces: interfaces fixture
        :param original_tx_port: port from which traffic will be send
        :return: receiving ecmp port
        """
        ecmp_port_list = [interfaces.dut_hb_1, interfaces.dut_hb_2]
        assert original_tx_port in ecmp_port_list, \
            f'original tx port: {original_tx_port} should in ecmp port list: {ecmp_port_list}'
        ecmp_port_list.remove(original_tx_port)
        return ecmp_port_list.pop()

    @retry(Exception, tries=3, delay=20)
    def get_interfaces_counters(self, cli_objects, ports, stat):
        """
        This method is used to get interfaces counters
        :param cli_objects: cli_objects fixture
        :param ports: list of ports for which statistics must be taken
        :param stat: port stat TX_OK, RX_OK etc
        :return: port statistic dictionary
        """
        port_stat_dict = {}
        counters_data = cli_objects['dut'].interface.parse_interfaces_counters()
        for port in ports:
            port_stat_dict[port] = port_stat_dict.get(port, 0) + int(counters_data[port][stat].replace(",", ""))
        return port_stat_dict

    def validate_roce_v2_pkts_traffic(self, players, interfaces, ha_dut_1_mac, dut_ha_1_mac, sender_count,
                                      sendpfast=False, mbps=None, loop=None, timeout=None):
        pkt_tc3_roce_v2_with_ar_flag = ArConsts.TC3_ROCEV2_AR_FLAG_PACKET.format(ha_dut_1_mac, dut_ha_1_mac,
                                                                                 ArConsts.V4_CONFIG['dut_ha_1'],
                                                                                 ArConsts.DUMMY_INTF['ipv4_addr'])
        logger.info("Send and validate traffic")
        self.send_and_validate_traffic(player=players, sender=ArConsts.HOST_A,
                                       sender_intf=interfaces.ha_dut_1,
                                       sender_pkt_format=pkt_tc3_roce_v2_with_ar_flag,
                                       sender_count=sender_count,
                                       sendpfast=sendpfast,
                                       mbps=mbps,
                                       loop=loop,
                                       timeout=timeout
                                       )

    def verify_enable_ar_before_doai_service_start(self, cli_objects):
        """
        This method is used to check if AR enabled before doAI service started
        :param cli_objects: cli_objects fixture
        """
        try:
            self.disable_ar(cli_objects)
            self.disable_doai_service(cli_objects)
            warn_output = cli_objects.dut.ar.enable_ar_function()
            assert ArConsts.WARNING_MESSAGE in warn_output, f'Adaptive Routing should print warning when enabling' \
                                                            f'ar function before ' \
                                                            f'{AppExtensionInstallationConstants.DOAI} service'
        except Exception as err:
            raise err
        finally:
            self.enable_doai_service(cli_objects)
            self.enable_ar_function(cli_objects)

    def verify_config_non_exist_profile(self, cli_objects):
        """
        This method is used to verify non existing profile can not be added to AR config
        :param cli_objects: cli_objects fixture
        """
        error_output = cli_objects.dut.ar.config_ar_profile(ArConsts.NON_EXIST_PROFILE)
        assert ArConsts.NON_EXIST_PROFILE_ERROR_MESSAGE in error_output, \
            f'AR configured with a non exist profile: {ArConsts.NON_EXIST_PROFILE}'

    def verify_config_ar_at_non_exist_port(self, cli_objects):
        """
        This method is used to verify invalid port can not be added to AR config
        :param cli_objects: cli_objects fixture
        """
        error_output = cli_objects.dut.ar.enable_ar_port(ArConsts.NON_EXIST_PORT)
        assert ArConsts.NON_EXIST_PORT_ERROR_MESSAGE in error_output, \
            f'AR configured with a non exist port: {ArConsts.NON_EXIST_PORT}'

    def verify_config_ar_on_vlan_intf(self, cli_objects):
        """
        This method is used to verify invalid vlan interface can not be added to AR config
        :param cli_objects: cli_objects fixture
        """
        error_output = cli_objects.dut.ar.enable_ar_port(ArConsts.DUMMY_VLAN_INTF)
        assert ArConsts.AR_ON_VLAN_INTF_ERROR_MESSAGE in error_output, \
            f'AR configured with on vlan interface: {ArConsts.DUMMY_VLAN_INTF}'

    def verify_config_ar_on_lag_intf_and_lag_member(self, cli_objects, topology_obj):
        """
        This method is used to verify invalid LAG interface/ LAG member can not be added to AR config
        :param cli_objects: cli_objects fixture
        :param topology_obj: topology_obj fixture
        """
        lb = get_dut_loopbacks(topology_obj)
        error_output = cli_objects.dut.ar.enable_ar_port(ArConsts.DUMMY_LAG_INTF)
        assert ArConsts.AR_ON_LAG_INTF_ERROR_MESSAGE in error_output, \
            f'AR configured with on lag interface: {ArConsts.DUMMY_LAG_INTF}'
        error_output = cli_objects.dut.ar.enable_ar_port(lb[0][0])
        assert ArConsts.AR_ON_LAG_MEMBER_ERROR_MESSAGE in error_output, f'AR configured with on lag member: {lb[0][0]}'

    def verify_config_ar_on_mgmt_port(self, cli_objects):
        """
        This method is used to verify management port can not be added to AR config
        :param cli_objects: cli_objects fixture
        """
        error_output = cli_objects.dut.ar.enable_ar_port(ArConsts.MGMT_PORT)
        assert ArConsts.AR_ON_MGMT_PORT_ERROR_MESSAGE in error_output, \
            f'AR configured with on mgmt interface: {ArConsts.MGMT_PORT}'

    def verify_config_ar_invalid_link_utilization(self, cli_objects, interfaces):
        """
        This method is used to verify invalid value if link utilization can not be set to AR interface
        :param cli_objects: cli_objects fixture
        :param interfaces: interfaces fixture
        """
        error_output = cli_objects.dut.ar.enable_ar_port(interfaces.dut_hb_1, ArConsts.INVALID_LINK_UTIL_PERCENT_VALUE)
        assert ArConsts.INVALID_LINK_UTIL_PERCENT_MESSAGE in error_output, \
            f'AR configured with invalid link utilization: {ArConsts.INVALID_LINK_UTIL_PERCENT_VALUE}'

    def copy_packet_aging_file_to_dut(self, engines):
        """
        This method is used to copy aging file to DUT
        :param engines: engines fixture
        """
        logger.info('Get sonic-mgmt path')
        base_dir = os.path.dirname(os.path.realpath(__file__))
        sonic_mgmt_base_dir = ArConsts.DIR_DELIMITER.join(base_dir.split(ArConsts.DIR_DELIMITER)[:-3])
        logger.info('Get path of packet aging file')
        packet_aging_script_abs_path = os.path.join(sonic_mgmt_base_dir, ArConsts.PACKET_AGING_SCRIPT_PATH)
        logger.info('Copy packet aging file to dut')
        engines.dut.copy_file(source_file=packet_aging_script_abs_path,
                              file_system='/tmp',
                              dest_file=packet_aging_script_abs_path.split(ArConsts.DIR_DELIMITER)[-1],
                              overwrite_file=True)

    def disable_packet_aging(self, engines, request=None):
        """
        This method is used to disable packet aging in syncd
        :param engines: engines fixture
        :param request: pytest builtin
        """
        if request:
            logger.info('Add enabling packet aging into finalizer')
            cleanup = partial(self.enable_packet_aging, engines)
            request.addfinalizer(cleanup)
        self.copy_packet_aging_file_to_dut(engines)
        logger.info('Copy packet aging file to syncd docker')
        engines.dut.run_cmd('docker cp /tmp/packets_aging.py syncd:/')
        logger.info('Disable packet aging')
        engines.dut.run_cmd('docker exec syncd python /packets_aging.py disable')

    def enable_packet_aging(self, engines):
        """
        This method is used to disable packet aging in syncd
        :param engines: engines fixture
        """
        logger.info('Enable packet aging')
        engines.dut.run_cmd('docker exec syncd python /packets_aging.py enable')
        engines.dut.run_cmd('docker exec syncd rm -rf /packets_aging.py')

    def copy_and_load_profile_config(self, engines, cli_objects, config_folder):
        """
        This method is used to copy  profile config file from sonic-mgmt to DUT and perform load
        :param engines: engines fixture
        :param cli_objects: cli_objects fixture
        :param config_folder: folder where config stored
        """
        engines.dut.copy_file(source_file=os.path.join(config_folder, ArConsts.AR_CUSTOM_PROFILE_FILE_NAME),
                              dest_file=ArConsts.AR_CUSTOM_PROFILE_FILE_NAME,
                              file_system='/tmp/',
                              overwrite_file=True,
                              verify_file=False)

        cli_objects.dut.general.load_configuration('/tmp/' + ArConsts.AR_CUSTOM_PROFILE_FILE_NAME)

    def enable_ar_profile(self, cli_objects, profile_name, restart_swss=False, request=None):
        """
        This method is used to enable ar profile
        :param cli_objects: engines fixture
        :param profile_name: profile to be enabled
        :param restart_swss: restart_swss flag
        :param request: python builtin
        """
        if request:
            logger.info('Add enabling packet aging into finalizer')
            cleanup = partial(cli_objects.dut.ar.config_ar_profile, ArConsts.GOLDEN_PROFILE0, restart_swss)
            request.addfinalizer(cleanup)
        cli_objects.dut.ar.config_ar_profile(profile_name, restart_swss=restart_swss)

    def get_all_ports(self, topology_obj):
        """
        This method is used to get all ports of DUT
        :param topology_obj: topology_obj fixture
        :return: list op DUT ports
        """
        return topology_obj.players_all_ports["dut"]
