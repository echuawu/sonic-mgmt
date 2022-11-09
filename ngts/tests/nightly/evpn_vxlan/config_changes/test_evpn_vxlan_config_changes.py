import logging
import pytest
import os

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vxlan_config_template import VxlanConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.helpers.vxlan_helper import send_and_validate_traffic, verify_counter_entry, validate_basic_evpn_type_2_3_route
from ngts.constants.constants import VxlanConstants
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure

"""

 EVPN VXLAN Test Cases

 Documentation: https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+EVPN+VXLAN+Documentation

"""

logger = logging.getLogger()
allure.logger = logger

VNI_TO_HEX_VNI_MAP = {VxlanConstants.VNI_12345: '0x303900', VxlanConstants.VNI_54321: '0xd43100'}
VLAN_VNI_TEST_MAP = [(VxlanConstants.VLAN_100, VxlanConstants.VNI_12345), (VxlanConstants.VLAN_200, VxlanConstants.VNI_12345), (VxlanConstants.VLAN_200, VxlanConstants.VNI_54321)]


@pytest.fixture(scope='module', autouse=True)
def basic_configuration(topology_obj, interfaces, cli_objects):
    """
    Pytest fixture used to configure basic vlan and ip configuration
    :param topology_obj: topology object fixture
    :param interfaces:  interfaces fixture
    """
    ip_config_dict = {
        'dut': [{'iface': 'Loopback0', 'ips': [('10.1.0.32', '32')]},
                {'iface': interfaces.dut_ha_1, 'ips': [('1.1.1.2', '24')]}
                ],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('1.1.1.1', '24')]}
               ]
    }

    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info("Enable vxlan counter")
    cli_objects.dut.vxlan.enable_vxlan_counter()
    logger.info('Basic vlan and ip connectivity configuration completed')

    yield

    logger.info("Disable vxlan counter")
    cli_objects.dut.vxlan.disable_vxlan_counter()
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    logger.info('Basic vlan and ip connectivity configuration cleanup completed')


class TestEvpnVxlanConfigChange:

    @pytest.fixture(autouse=True)
    def prepare_param(self, topology_obj, engines, players, interfaces):
        self.topology_obj = topology_obj
        self.engines = engines
        self.players = players
        self.interfaces = interfaces

        self.dut_loopback_ip = '10.1.0.32'
        self.dut_vlan_ip = '100.0.0.1'
        self.dut_ha_1_ip = '1.1.1.2'

        self.ha_dut_1_ip = '1.1.1.1'
        self.ha_br_ip = '100.0.0.2'

        self.hb_vlan_ip = '100.0.0.3'

        self.hb_vlan_100_iface = f"{interfaces.hb_dut_1}.100"

        self.dut_bgp_neighbor_1_ip_1_1_1_1 = self.ha_dut_1_ip

        self.dut_vtep_ip = self.dut_loopback_ip
        self.ha_vtep_ip = self.ha_dut_1_ip

    def config_vlan_vni_map(self, topology_obj, interfaces, vlan_id, vni):
        """
        This method is used to config vlan and vni map related configurations
        :param topology_obj: topology_obj fixture
        :param interfaces: interfaces fixture
        :param vlan_id: vlan id
        :param vni: vni
        """
        frr_config_folder = os.path.dirname(os.path.abspath(__file__))
        frr_config_dict = {
            'dut': {'configuration': {'config_name': 'dut_frr_config.conf', 'path_to_config_file': frr_config_folder},
                    'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']},
            'ha': {'configuration': {'config_name': 'ha_frr_config.conf', 'path_to_config_file': frr_config_folder},
                   'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']}
        }

        vlan_config_dict = {
            'dut': [{'vlan_id': '{}'.format(vlan_id), 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]}
                    ],
            'hb': [{'vlan_id': '{}'.format(vlan_id), 'vlan_members': [{interfaces.hb_dut_1: None}]}
                   ]
        }

        ip_config_dict = {
            'dut': [{'iface': 'Vlan{}'.format(vlan_id), 'ips': [('100.0.0.1', '24')]}
                    ],
            'hb': [{'iface': '{}.{}'.format(interfaces.hb_dut_1, vlan_id), 'ips': [('100.0.0.3', '24')]}
                   ]
        }

        vxlan_config_dict = {
            'dut': [{'evpn_nvo': '{}'.format(VxlanConstants.EVPN_NVO), 'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                     'tunnels': [{'vni': '{}'.format(vni), 'vlan': '{}'.format(vlan_id)}]}
                    ],
            'ha': [{'vtep_name': 'vtep_{}'.format(vni), 'vtep_src_ip': '1.1.1.1', 'vni': '{}'.format(vni),
                    'vtep_ips': [('100.0.0.2', '24')]}],
        }

        logger.info('Evpn vxlan configuration completed')
        VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
        IpConfigTemplate.configuration(topology_obj, ip_config_dict)
        VxlanConfigTemplate.configuration(topology_obj, vxlan_config_dict)
        # in case there is useless bgp configuration exist
        FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
        FrrConfigTemplate.configuration(topology_obj, frr_config_dict)

    def clean_vlan_vni_map(self, topology_obj, interfaces, vlan_id, vni):
        """
        This method is used to clean vlan and vni map related configurations
        :param topology_obj: topology_obj fixture
        :param interfaces: interfaces fixture
        :param vlan_id: vlan id
        :param vni: vni
        """
        frr_config_folder = os.path.dirname(os.path.abspath(__file__))
        frr_config_dict = {
            'dut': {'configuration': {'config_name': 'dut_frr_config.conf', 'path_to_config_file': frr_config_folder},
                    'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
            'ha': {'configuration': {'config_name': 'ha_frr_config.conf', 'path_to_config_file': frr_config_folder},
                   'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']}
        }

        vlan_config_dict = {
            'dut': [{'vlan_id': '{}'.format(vlan_id), 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]}
                    ],
            'hb': [{'vlan_id': '{}'.format(vlan_id), 'vlan_members': [{interfaces.hb_dut_1: None}]}
                   ]
        }

        ip_config_dict = {
            'dut': [{'iface': 'Vlan{}'.format(vlan_id), 'ips': [('100.0.0.1', '24')]}
                    ],
            'hb': [{'iface': '{}.{}'.format(interfaces.hb_dut_1, vlan_id), 'ips': [('100.0.0.3', '24')]}
                   ]
        }

        vxlan_config_dict = {
            'dut': [{'evpn_nvo': '{}'.format(VxlanConstants.EVPN_NVO), 'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                     'tunnels': [{'vni': '{}'.format(vni), 'vlan': '{}'.format(vlan_id)}]}
                    ],
            'ha': [{'vtep_name': 'vtep_{}'.format(vni), 'vtep_src_ip': '1.1.1.1', 'vni': '{}'.format(vni),
                    'vtep_ips': [('100.0.0.2', '24')]}],
        }

        logger.info('Cleanup evpn vxlan configuration')
        FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
        VxlanConfigTemplate.cleanup(topology_obj, vxlan_config_dict)
        IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
        VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    def clean_bgp_session(self, topology_obj):
        """
        This method is used to remove FRR BGP configuration at HA and DUT
        :param topology_obj: topology_obj fixture
        """
        bgp_clean_dict = {
            'dut': {'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
            'ha': {'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']}
        }
        FrrConfigTemplate.cleanup(topology_obj, bgp_clean_dict)

    def get_ha_br_mac(self, cli_objects, vni):
        """
        This method is used to get the mac address of bridge interface at HA
        :param cli_objects: cli_objects fixture
        :return: mac address of bridge interface at HA
        """
        ha_vni_iface = f"br_{vni}"
        ha_br_mac = cli_objects.ha.mac.get_mac_address_for_interface(ha_vni_iface)
        return ha_br_mac

    def validate_traffic_fail_to_pass(self, cli_objects, interfaces, vlan_id, vni):
        with allure.step(f"Send traffic from HB to HA via VLAN {vlan_id} to VNI {vni}"):
            hb_vlan_iface = f"{interfaces.hb_dut_1}.{vlan_id}"
            hb_vlan_mac = cli_objects.hb.mac.get_mac_address_for_interface(hb_vlan_iface)
            ha_vni_iface = f"br_{vni}"
            ha_br_mac = cli_objects.ha.mac.get_mac_address_for_interface(ha_vni_iface)

            pkt_hb_ha_vlan_vni_r = VxlanConstants.SIMPLE_PACKET.format(hb_vlan_mac, ha_br_mac,
                                                                       self.hb_vlan_ip,
                                                                       self.ha_br_ip)
            logger.info("Validate traffic from HB to HA")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=hb_vlan_iface, sender_pkt_format=pkt_hb_ha_vlan_vni_r,
                                      sender_count=VxlanConstants.PACKET_NUM_3, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VNI_TO_HEX_VNI_MAP[vni],
                                          VxlanConstants.HEX_100_0_0_3), receiver_count=VxlanConstants.PACKET_NUM_0)

    def validate_two_way_traffic_and_counters(self, cli_objects, interfaces, vlan_id, vni):
        with allure.step(f"Send traffic from HB to HA via VLAN {vlan_id} to VNI {vni}"):
            hb_vlan_iface = f"{interfaces.hb_dut_1}.{vlan_id}"
            hb_vlan_mac = cli_objects.hb.mac.get_mac_address_for_interface(hb_vlan_iface)
            ha_vni_iface = f"br_{vni}"
            ha_br_mac = cli_objects.ha.mac.get_mac_address_for_interface(ha_vni_iface)

            logger.info("Clear vxlan counter")
            cli_objects.dut.vxlan.clear_vxlan_counter()
            pkt_hb_ha_vlan_vni_r = VxlanConstants.SIMPLE_PACKET.format(hb_vlan_mac, ha_br_mac,
                                                                       self.hb_vlan_ip,
                                                                       self.ha_br_ip)
            logger.info(f"Validate traffic from HB to HA")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=hb_vlan_iface, sender_pkt_format=pkt_hb_ha_vlan_vni_r,
                                      sender_count=VxlanConstants.PACKET_NUM_100, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VNI_TO_HEX_VNI_MAP[vni],
                                          VxlanConstants.HEX_100_0_0_3))

        with allure.step('Validate vxlan tx counters'):
            verify_counter_entry(cli_objects, VxlanConstants.VTEP_NAME_DUT, 'tx', VxlanConstants.PACKET_NUM_100)

        with allure.step(f"Send traffic from HA to HB via VNI {vni} to VLAN {vlan_id}"):
            logger.info("Clear vxlan counter")
            cli_objects.dut.vxlan.clear_vxlan_counter()
            pkt_ha_hb_vni_vlan_r = VxlanConstants.SIMPLE_PACKET.format(ha_br_mac, hb_vlan_mac,
                                                                       self.ha_br_ip,
                                                                       self.hb_vlan_ip)
            logger.info(f"Validate traffic from HA to HB")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HA,
                                      sender_intf=ha_vni_iface, sender_pkt_format=pkt_ha_hb_vni_vlan_r,
                                      sender_count=VxlanConstants.PACKET_NUM_100, receiver=VxlanConstants.HOST_HB, receiver_intf=hb_vlan_iface,
                                      receiver_filter_format=VxlanConstants.SIMPLE_PACKET_FILTER.format(
                                          self.hb_vlan_ip))

        with allure.step('Validate vxlan rx counters'):
            verify_counter_entry(cli_objects, VxlanConstants.VTEP_NAME_DUT, 'rx', VxlanConstants.PACKET_NUM_100)

    def config_vlan_vni_map_and_verify_maclearn_traffic_counter(self, topology_obj, cli_objects, interfaces, vlan_id, vni):
        """
        This method is used to verify a full set of test
        1. Configure vlan and vni map, and related FRR BGP configuration at HA and DUT
        2. Validate BGP neighbor establishment
        3. Validate type 2 and type 3 routes
        4. Validate VXLAN remote mac learning
        5. Validate two side traffic
        6. Validate VXLAN counters
        7. Clean VXLAN configuration and FRR BGP configurations
        :param topology_obj: topology_obj fixture
        :param cli_objects: cli_objects fixture
        :param interfaces:  interface fixture
        :param vlan_id: vlan id
        :param vni: vni value
        """
        try:
            with allure.step(f"Add VLAN {vlan_id} on DUT and map with with tunnel {vni}, make VLAN {vlan_id} accessible on HB"):
                self.config_vlan_vni_map(topology_obj, interfaces, vlan_id, vni)
            with allure.step(f"Validate BGP neighbor {self.ha_dut_1_ip} established"):
                cli_objects.dut.frr.validate_bgp_neighbor_established(self.ha_dut_1_ip)
            with allure.step(f"Validate evpn type 2 and type 3 routes for vni {vni}"):
                ha_br_mac = self.get_ha_br_mac(cli_objects, vni)
                validate_basic_evpn_type_2_3_route(self.players, cli_objects, interfaces, vlan_id, self.dut_vlan_ip, self.dut_loopback_ip, self.ha_vtep_ip, self.hb_vlan_ip, VxlanConstants.RD_100)
            with allure.step(f"Validate MAC {ha_br_mac} is learned from EVPN VXLAN - vlan {vlan_id} - vtep {self.ha_vtep_ip} - vni {vni}"):
                cli_objects.dut.vxlan.check_vxlan_remotemac(vlan_mac_vtep_vni_check_list=[
                    (vlan_id, ha_br_mac, self.ha_vtep_ip, vni)
                ])
            with allure.step('Validate vxlan traffic and counters'):
                self.validate_two_way_traffic_and_counters(cli_objects, interfaces, vlan_id, vni)
        finally:
            with allure.step(f"Remove VLAN {vlan_id} and VNI {vni} configuration"):
                self.clean_vlan_vni_map(topology_obj, interfaces, vlan_id, vni)

    def test_config_changes(self, cli_objects, topology_obj, interfaces):
        """
        This test will check EVPN VXLAN config change functionality

        Test has next steps:
        1. Configure BGP/EVPN VXLAN on DUT and HA, VNI 12345
        2. Add VLAN 100 on DUT and map with with tunnel 12345, make VLAN 100 accessible on HB
        3. Check that traffic pass from VLAN 100 to tunnel and back, check MAC table on DUT
        4. Add VLAN 200 on DUT and HB, change VNI to VLAN mapping to: VLAN 200 - VNI 12345
        5. Check that traffic pass from VLAN 200 to tunnel and back, check MAC table on DUT
        6. Change VLAN to VNI mapping on DUT to: VLAN 200 - VNI 54321, do changes for VNI on HA vxlan interface
        7. Check that traffic pass from VLAN 200 to tunnel and back, check MAC table on DUT
        8. Remove VXLAN on host - check that VXLAN remote mac removed on DUT
        9. Remove VNI/VLAN mapping on DUT - check that traffic does not pass via VXLAN tunnel
        10. Remove VXLAN tunnel on DUT - check on HA that tunnel not advertised from DUT
        11. Remove BGP/EVPN related settings - check that BPG session not available on HA
        """
        # test vlan-vni map pairs of [(VLAN_100, VNI_12345), (VLAN_200, VNI_12345), (VLAN_200, VNI_54321)]
        for vlan_vni_pair in VLAN_VNI_TEST_MAP:
            vlan = vlan_vni_pair[0]
            vni = vlan_vni_pair[1]
            with allure.step(f"Test VXLAN functionality at VLAN {vlan} map with VNI {vni}"):
                self.config_vlan_vni_map_and_verify_maclearn_traffic_counter(topology_obj, cli_objects, interfaces, vlan, vni)
        try:
            with allure.step(f"Add VLAN {VxlanConstants.VLAN_200} on DUT and map with with tunnel {VxlanConstants.VNI_54321}, make VLAN {VxlanConstants.VLAN_200} accessible on HB"):
                self.config_vlan_vni_map(topology_obj, interfaces, VxlanConstants.VLAN_200, VxlanConstants.VNI_54321)
            with allure.step(f"Validate BGP neighbor {self.ha_dut_1_ip} established"):
                cli_objects.dut.frr.validate_bgp_neighbor_established(self.ha_dut_1_ip)
            with allure.step(f"Validate evpn type 2 and type 3 routes for vni {VxlanConstants.VNI_54321}"):
                validate_basic_evpn_type_2_3_route(self.players, cli_objects, interfaces, VxlanConstants.VLAN_200, self.dut_vlan_ip, self.dut_loopback_ip, self.ha_vtep_ip, self.hb_vlan_ip, VxlanConstants.RD_100)
            with allure.step(f"Remove VXLAN on HA"):
                ha_br_mac = self.get_ha_br_mac(cli_objects, VxlanConstants.VNI_54321)
                cli_objects.ha.interface.del_interface(VxlanConstants.HA_VXLAN_54321_IFACE)
            with allure.step(f"Validate MAC {ha_br_mac} is removed from EVPN VXLAN - vlan {VxlanConstants.VLAN_200} - vtep {self.ha_vtep_ip} - vni {VxlanConstants.VNI_54321}"):
                cli_objects.dut.vxlan.check_vxlan_remotemac(vlan_mac_vtep_vni_check_list=[
                    (VxlanConstants.VLAN_200, ha_br_mac, self.ha_vtep_ip, VxlanConstants.VNI_54321)
                ], learned=False)

            with allure.step('Remove VLAN VNI mapping on DUT'):
                cli_objects.dut.vxlan.del_vtep_mapping_to_vlan_vni(VxlanConstants.VTEP_NAME_DUT, VxlanConstants.VLAN_200, VxlanConstants.VNI_54321)
            with allure.step('Validate traffic would not pass via VXLAN tunnel'):
                self.validate_traffic_fail_to_pass(cli_objects, interfaces, VxlanConstants.VLAN_200, VxlanConstants.VNI_54321)

            with allure.step('Remove VXLAN tunnel on DUT'):
                cli_objects.dut.vxlan.del_evpn_nvo_vxlan_mapping(VxlanConstants.EVPN_NVO)
                cli_objects.dut.vxlan.del_vtep(VxlanConstants.VTEP_NAME_DUT)
            with allure.step('Validate on HA that no type 3 route from DUT send out'):
                ha_type_3_info = cli_objects.ha.frr.get_l2vpn_evpn_route_type_multicast()
                cli_objects.ha.frr.validate_type_3_route(ha_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, VxlanConstants.RD_100, learned=False)

            with allure.step('Remove FRR BGP'):
                self.clean_bgp_session(topology_obj)
            with allure.step('BGP session would not be established'):
                cli_objects.dut.frr.validate_bgp_neighbor_established(self.ha_dut_1_ip, establish=False)
        finally:
            with allure.step(f"Remove VLAN {VxlanConstants.VLAN_200} and VNI {VxlanConstants.VNI_54321} configuration"):
                self.clean_vlan_vni_map(topology_obj, interfaces, VxlanConstants.VLAN_200, VxlanConstants.VNI_54321)
