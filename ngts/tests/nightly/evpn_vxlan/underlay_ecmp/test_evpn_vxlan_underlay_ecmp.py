import logging
import pytest
import os

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vxlan_config_template import VxlanConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.helpers.vxlan_helper import send_and_validate_traffic, verify_underlay_ecmp_counter_entry, validate_basic_evpn_type_2_3_route
from ngts.constants.constants import VxlanConstants
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure

"""

 EVPN VXLAN Test Cases

 Documentation: https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+EVPN+VXLAN+Documentation

"""

logger = logging.getLogger()
allure.logger = logger

DUT_VLAN_3_IFACE = 'Vlan3'
VETH_MAC_ADDR = VxlanConstants.SOURCE_MAC_ADDR_1


def config_veth_pair_at_ha(cli_objects, veth_name, veth_peer_name, bridge_name, veth_ip, name_space, mac):
    """
    This method is used to configure veth pair to simulate host of VXLAN at HA
    :param cli_objects: cli_objects fixture
    :param veth_name: veth name
    :param veth_peer_name: veth peer name
    :param bridge_name: the bridge to bind veth peer to
    :param veth_ip: ip address for veth
    :param name_space: name space to bind veth
    :param mac: mac address for veth
    """
    logger.info(
        f"Create veth {veth_name} in namespace {name_space} in HA, and bind veth peer {veth_peer_name} to bridge {bridge_name}")
    cli_objects.ha.vxlan.add_vxlan_veth(name_space, bridge_name, veth_name, veth_peer_name)
    logger.info(f"Set IP {veth_ip} to HA veth {veth_name} in namespace {name_space}")
    cli_objects.ha.vxlan.set_veth_ip_addr(name_space, veth_name, veth_ip)
    logger.info(f"Set MAC {mac} to HA veth {veth_name} in namespace {name_space}")
    cli_objects.ha.vxlan.set_veth_mac_addr(name_space, veth_name, mac)


@pytest.fixture(scope='module', autouse=True)
def basic_configuration(topology_obj, interfaces, cli_objects):
    """
    Pytest fixture used to configure basic evpn vxlan configuration
    :param topology_obj: topology object fixture
    :param interfaces:  interfaces fixture
    :param cli_objects: cli_objects fixture
    """
    vlan_config_dict = {
        'dut': [{'vlan_id': 3, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]}
                ],
        'hb': [{'vlan_id': 3, 'vlan_members': [{interfaces.hb_dut_1: None}]}
               ]
    }

    ip_config_dict = {
        'dut': [{'iface': 'Loopback0', 'ips': [('10.1.0.32', '32')]},
                {'iface': interfaces.dut_ha_1, 'ips': [('1.1.1.2', '24')]},
                {'iface': interfaces.dut_ha_2, 'ips': [('2.2.2.2', '24')]},
                {'iface': 'Vlan3', 'ips': [('3.3.3.1', '24')]}
                ],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('1.1.1.1', '24')]},
               {'iface': interfaces.ha_dut_2, 'ips': [('2.2.2.1', '24')]}
               ],
        'hb': [{'iface': '{}.3'.format(interfaces.hb_dut_1), 'ips': [('3.3.3.3', '24')]}
               ]
    }

    frr_config_folder = os.path.dirname(os.path.abspath(__file__))
    vxlan_config_dict = {
        'dut': [{'evpn_nvo': 'my-nvo', 'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                 'tunnels': [{'vni': VxlanConstants.VNI_3333, 'vlan': VxlanConstants.VLAN_3}]
                 }
                ],
        'ha': [{'vtep_name': 'vtep_3333', 'vtep_src_ip': '30.0.0.2', 'vni': VxlanConstants.VNI_3333,
                'vtep_ips': [('30.0.0.2', '24')]}]
    }

    frr_config_dict = {
        'dut': {'configuration': {'config_name': 'dut_frr_config.conf', 'path_to_config_file': frr_config_folder},
                'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']},
        'ha': {'configuration': {'config_name': 'ha_frr_config.conf', 'path_to_config_file': frr_config_folder},
               'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']}
    }

    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('Basic vlan and ip connectivity configuration completed')
    VxlanConfigTemplate.configuration(topology_obj, vxlan_config_dict)
    config_veth_pair_at_ha(cli_objects, VxlanConstants.VETH_NAME_1, VxlanConstants.VETH_PEER_NAME_1, VxlanConstants.VNI_3333_IFACE,
                           VxlanConstants.VETH_IP, VxlanConstants.NAME_SPACE_1, VETH_MAC_ADDR)
    # in case there is useless bgp configuration exist
    FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
    FrrConfigTemplate.configuration(topology_obj, frr_config_dict)
    logger.info('Evpn vxlan configuration completed')
    logger.info("Enable vxlan counter")
    cli_objects.dut.vxlan.enable_vxlan_counter()

    yield

    logger.info("Disable vxlan counter")
    cli_objects.dut.vxlan.disable_vxlan_counter()
    VxlanConfigTemplate.cleanup(topology_obj, vxlan_config_dict)
    cli_objects.ha.vxlan.del_vxlan_veth_ns(VxlanConstants.VETH_PEER_NAME_1, VxlanConstants.NAME_SPACE_1)
    FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
    logger.info('Evpn vxlan configuration cleanup completed')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    logger.info('Basic vlan and ip connectivity configuration cleanup completed')


@pytest.fixture(scope='class')
def mac_addresses(engines, cli_objects, interfaces):
    hb_vlan_3_iface = f"{interfaces.hb_dut_1}.3"
    dut_mac = cli_objects.dut.mac.get_mac_address_for_interface(DUT_VLAN_3_IFACE)
    ha_br_3333_mac = cli_objects.ha.mac.get_mac_address_for_interface(VxlanConstants.VNI_3333_IFACE)
    hb_vlan_3_mac = cli_objects.hb.mac.get_mac_address_for_interface(hb_vlan_3_iface)

    return dut_mac, ha_br_3333_mac, hb_vlan_3_mac


class TestEvpnVxlanUnderlayEcmp:

    @pytest.fixture(autouse=True)
    def prepare_param(self, topology_obj, engines, players, interfaces, mac_addresses):
        self.topology_obj = topology_obj
        self.engines = engines
        self.players = players
        self.interfaces = interfaces

        self.dut_loopback_ip = '10.1.0.32'
        self.dut_vlan_3_ip = '3.3.3.1'
        self.dut_ha_1_ip = '1.1.1.2'
        self.dut_ha_2_ip = '2.2.2.2'

        self.ha_dut_1_ip = '1.1.1.1'
        self.ha_dut_2_ip = '2.2.2.1'
        self.ha_br_3333_ip = '30.0.0.2'

        self.hb_vlan_3_ip = '3.3.3.3'

        self.hb_vlan_3_iface = f"{interfaces.hb_dut_1}.3"

        self.dut_bgp_neighbor_1_ip_1_1_1_1 = self.ha_dut_1_ip
        self.dut_bgp_neighbor_2_ip_2_2_2_1 = self.ha_dut_2_ip

        self.dut_vtep_ip = self.dut_loopback_ip
        self.ha_vtep_ip = self.ha_br_3333_ip

        self.dut_mac, self.ha_br_3333_mac, self.hb_vlan_3_mac = mac_addresses
        self.ecmp_interface_counter_check_list = [
            [interfaces.dut_ha_1, 'tx', VxlanConstants.PACKET_NUM_200],
            [interfaces.dut_ha_2, 'tx', VxlanConstants.PACKET_NUM_200],
            [interfaces.dut_hb_1, 'rx', VxlanConstants.PACKET_NUM_400],
        ]
        self.network_nexthop_list = [self.ha_br_3333_ip, (self.ha_dut_1_ip, self.ha_dut_2_ip)]

    def validate_ecmp_traffic_and_counters(self, cli_objects):
        with allure.step(f"Send ECMP traffic from HB to HA via VLAN {VxlanConstants.VLAN_3} to VNI {VxlanConstants.VNI_3333}"):
            logger.info("Clear interface and vxlan counter")
            cli_objects.dut.vxlan.clear_vxlan_counter()
            cli_objects.dut.interface.clear_counters()
            pkt_ecmp_hb_ha_vlan3_vni3333_r = VxlanConstants.ECMP_SIMPLE_PACKET.format(self.hb_vlan_3_mac, self.ha_br_3333_mac,
                                                                                      VxlanConstants.ECMP_TRAFFIC_SRC_IP_LIST,
                                                                                      VxlanConstants.VETH_IP)
            logger.info("Validate ECMP traffic")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=self.hb_vlan_3_iface, sender_pkt_format=pkt_ecmp_hb_ha_vlan3_vni3333_r,
                                      sender_count=VxlanConstants.PACKET_NUM_100, receiver=VxlanConstants.HOST_HA, receiver_intf=VxlanConstants.VNI_3333_IFACE,
                                      receiver_filter_format=VxlanConstants.SIMPLE_PACKET_FILTER.format(
                                          VxlanConstants.VETH_IP),
                                      receiver_count=VxlanConstants.PACKET_NUM_400)

        with allure.step('Validate vxlan tx counters'):
            verify_underlay_ecmp_counter_entry(cli_objects, self.ecmp_interface_counter_check_list)

    def test_underlay_ecmp(self, cli_objects, topology_obj, interfaces):
        """
        This test will check EVPN VXLAN underlay ecmp functionality

        Test has next steps:
        1. Send 400 packets from HB 3.3.3.3 to HA br3333 interface IP 3.3.3.2
        2. Check that traffic balanced 50/50 via 2 routes(1.1.1.2, 2.2.2.2) - each route transmit 200 packets
        """
        with allure.step('Validate evpn type 2 and type 3 routes'):
            validate_basic_evpn_type_2_3_route(self.players, cli_objects, interfaces, VxlanConstants.VLAN_3, self.dut_vlan_3_ip, self.dut_loopback_ip, self.ha_br_3333_ip, self.hb_vlan_3_ip,
                                               VxlanConstants.RD_3333)
        with allure.step('Validate BGP ECMP routes'):
            cli_objects.dut.frr.validate_bgp_ecmp_route(self.network_nexthop_list)
        with allure.step('Validate vxlan traffic and counters'):
            self.validate_ecmp_traffic_and_counters(cli_objects)
