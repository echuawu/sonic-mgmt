import logging
import pytest

from ngts.constants.constants import VxlanConstants
from ngts.helpers.vxlan_helper import send_and_validate_traffic
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

"""

 EVPN VXLAN Test Cases

 Documentation: https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+EVPN+VXLAN+Documentation

"""

logger = logging.getLogger()
allure.logger = logger

DUT_VLAN_100_IFACE = 'Vlan100'
HA_BOND_0_IFACE = 'bond0'
HB_VLAN_101_IFACE = 'bond0.101'
STATIC_MAC_PORT = 'PortChannel0002'
SOURCE_MAC_PORT_1_TO_HB = 'PortChannel0002'
SOURCE_MAC_PORT_1_TO_HA = 'PortChannel0002'


@pytest.fixture(scope='class')
def mac_addresses(engines, cli_objects):
    dut_mac = cli_objects.dut.mac.get_mac_address_for_interface(DUT_VLAN_100_IFACE)
    ha_br_500100_mac = cli_objects.ha.mac.get_mac_address_for_interface(VxlanConstants.VNI_500100_IFACE)
    ha_br_500101_mac = cli_objects.ha.mac.get_mac_address_for_interface(VxlanConstants.VNI_500101_IFACE)
    hb_br_500100_mac = cli_objects.hb.mac.get_mac_address_for_interface(VxlanConstants.VNI_500100_IFACE)
    hb_bond0_101_mac = cli_objects.hb.mac.get_mac_address_for_interface(HB_VLAN_101_IFACE)

    return dut_mac, ha_br_500100_mac, ha_br_500101_mac, hb_br_500100_mac, hb_bond0_101_mac


class TestEvpnVxlan:

    @pytest.fixture(autouse=True)
    def prepare_param(self, topology_obj, engines, players, interfaces, mac_addresses):
        self.topology_obj = topology_obj
        self.engines = engines
        self.players = players
        self.interfaces = interfaces

        self.dut_loopback_ip = '10.1.0.32'
        self.dut_vlan_100_ip = '100.0.0.1'
        self.dut_vlan_101_ip = '101.0.0.1'

        self.ha_bond_0_ip = '30.0.0.2'
        self.ha_vni_500100_iface_ip = '100.0.0.2'
        self.ha_vni_500101_iface_ip = '101.0.0.2'

        self.hb_vlan_40_ip = '40.0.0.3'
        self.hb_vni_500100_iface_ip = '100.0.0.3'
        self.hb_vlan_101_iface_ip = '101.0.0.3'

        self.dut_vtep_ip = self.ha_bond_0_ip
        self.ha_vtep_ip = self.ha_bond_0_ip
        self.hb_vtep_ip = self.hb_vlan_40_ip

        self.dut_mac, self.ha_br_500100_mac, self.ha_br_500101_mac, self.hb_br_500100_mac, self.hb_bond0_101_mac = mac_addresses

    def validate_basic_evpn_type_2_3_route(self, cli_objects):
        """
        This method is used to verify basic evpn type 2 and type 3 route states
        :param cli_objects: cli_objects fixture
        """
        # VXLAN route validation
        with allure.step('Validate CLI type-2 routes on DUT'):
            dut_type_2_info = cli_objects.dut.frr.get_l2vpn_evpn_route_type_macip()
            cli_objects.dut.frr.validate_type_2_route(dut_type_2_info, self.hb_bond0_101_mac, self.dut_loopback_ip,
                                                      VxlanConstants.RD_101, self.hb_vlan_101_iface_ip)

        with allure.step('Validate CLI type-3 routes on DUT'):
            dut_type_3_info = cli_objects.dut.frr.get_l2vpn_evpn_route_type_multicast()
            cli_objects.dut.frr.validate_type_3_route(dut_type_3_info, self.ha_bond_0_ip, self.ha_bond_0_ip, VxlanConstants.RD_100)
            cli_objects.dut.frr.validate_type_3_route(dut_type_3_info, self.ha_bond_0_ip, self.ha_bond_0_ip, VxlanConstants.RD_101)

            cli_objects.dut.frr.validate_type_3_route(dut_type_3_info, self.hb_vlan_40_ip, self.hb_vlan_40_ip, VxlanConstants.RD_100)

        with allure.step('Validate CLI type-2 routes on HA'):
            ha_type_2_info = cli_objects.ha.frr.get_l2vpn_evpn_route_type_macip()
            cli_objects.ha.frr.validate_type_2_route(ha_type_2_info, self.hb_bond0_101_mac, self.dut_loopback_ip,
                                                     VxlanConstants.RD_101, self.hb_vlan_101_iface_ip)

        with allure.step('Validate CLI type-3 routes on HA'):
            ha_type_3_info = cli_objects.ha.frr.get_l2vpn_evpn_route_type_multicast()
            cli_objects.ha.frr.validate_type_3_route(ha_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, VxlanConstants.RD_100)
            cli_objects.ha.frr.validate_type_3_route(ha_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, VxlanConstants.RD_101)

        with allure.step('Validate CLI type-3 routes on HB'):
            hb_type_3_info = cli_objects.hb.frr.get_l2vpn_evpn_route_type_multicast()
            cli_objects.hb.frr.validate_type_3_route(hb_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, VxlanConstants.RD_100)
            cli_objects.hb.frr.validate_type_3_route(hb_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, VxlanConstants.RD_101)

    def validate_l3_connectivity(self):
        """
        This method is used to validate layer 3 connectivity
        """
        # Ping from hosts to DUT over VXLAN and VLAN
        with allure.step('Send ping from HA to DUT via VNI 500100'):
            ping_ha_dut_vni_500100 = {'sender': 'ha', 'args': {'interface': VxlanConstants.VNI_500100_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                               'dst': self.dut_vlan_100_ip}}
            PingChecker(self.players, ping_ha_dut_vni_500100).run_validation()

        with allure.step('Send ping from HA to DUT via VNI 500101'):
            ping_ha_dut_vni_500101 = {'sender': 'ha', 'args': {'interface': VxlanConstants.VNI_500101_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                               'dst': self.dut_vlan_101_ip}}
            PingChecker(self.players, ping_ha_dut_vni_500101).run_validation()

        with allure.step('Send ping from HB to DUT via VNI 500100'):
            ping_hb_dut_vni_500100 = {'sender': 'hb', 'args': {'interface': VxlanConstants.VNI_500100_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                               'dst': self.dut_vlan_100_ip}}
            PingChecker(self.players, ping_hb_dut_vni_500100).run_validation()

        with allure.step('Send ping from HB to DUT via VLAN 101'):
            ping_hb_dut_vlan_101 = {'sender': 'hb', 'args': {'interface': HB_VLAN_101_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                             'dst': self.dut_vlan_101_ip}}
            PingChecker(self.players, ping_hb_dut_vlan_101).run_validation()
        # Pings between hosts
        with allure.step('Send ping from HB to HA via VLAN 101 to VNI 500101'):
            ping_hb_ha_vlan_101_to_vni_500101 = {'sender': 'hb', 'args': {'interface': HB_VLAN_101_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                                          'dst': self.ha_vni_500101_iface_ip}}
            PingChecker(self.players, ping_hb_ha_vlan_101_to_vni_500101).run_validation()

        with allure.step('Send ping from HA to HB via VNI 500101 to VLAN 101'):
            ping_ha_hb_vni_500101_to_vlan_101 = {'sender': 'ha', 'args': {'interface': VxlanConstants.VNI_500101_IFACE, 'count': VxlanConstants.PACKET_NUM_3,
                                                                          'dst': self.hb_vlan_101_iface_ip}}
            PingChecker(self.players, ping_ha_hb_vni_500101_to_vlan_101).run_validation()

    def validate_vxlan_traffic(self, interfaces):
        """
        This method is used to validate vxlan traffic
        :param interfaces: interfaces fixture
        """
        # Routing
        with allure.step('Send traffic from HB to HA via VLAN 101 to VNI 500100(routing)'):
            pkt_hb_ha_vlan101_vni500100_r = VxlanConstants.SIMPLE_PACKET.format(self.hb_bond0_101_mac, self.dut_mac,
                                                                                self.hb_vlan_101_iface_ip,
                                                                                self.ha_vni_500100_iface_ip)
            logger.info("Send and validate traffic")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=HB_VLAN_101_IFACE, sender_pkt_format=pkt_hb_ha_vlan101_vni500100_r,
                                      sender_count=VxlanConstants.PACKET_NUM_3, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VxlanConstants.HEX_500100,
                                          VxlanConstants.HEX_101_0_0_3))
        # Negative validations
        with allure.step('Send traffic from HB to HA via VNI 500100 to VNI 500100(negative)'):
            pkt_hb_ha_vni500100_vni500100 = VxlanConstants.SIMPLE_PACKET.format(self.hb_br_500100_mac, self.ha_br_500100_mac,
                                                                                self.hb_vni_500100_iface_ip,
                                                                                self.ha_vni_500100_iface_ip)
            logger.info("Send and validate traffic")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=VxlanConstants.VNI_500100_IFACE, sender_pkt_format=pkt_hb_ha_vni500100_vni500100,
                                      sender_count=VxlanConstants.PACKET_NUM_3, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VxlanConstants.HEX_500100,
                                          VxlanConstants.HEX_100_0_0_3), receiver_count=VxlanConstants.PACKET_NUM_0)

        with allure.step('Send traffic from HB to HA via VLAN 101 to VNI 500100(negative)'):
            pkt_hb_ha_vlan101_vni500100 = VxlanConstants.SIMPLE_PACKET.format(self.hb_bond0_101_mac, self.ha_br_500100_mac,
                                                                              self.hb_vlan_101_iface_ip,
                                                                              self.ha_vni_500100_iface_ip)
            logger.info("Send and validate traffic")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=HB_VLAN_101_IFACE, sender_pkt_format=pkt_hb_ha_vlan101_vni500100,
                                      sender_count=VxlanConstants.PACKET_NUM_3, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VxlanConstants.HEX_500100,
                                          VxlanConstants.HEX_101_0_0_3), receiver_count=VxlanConstants.PACKET_NUM_0)

        with allure.step('Send traffic from HB to HA via VNI 500100 to VNI 500101(negative)'):
            pkt_hb_ha_vni500100_vni500101 = VxlanConstants.SIMPLE_PACKET.format(self.hb_br_500100_mac, self.ha_br_500101_mac,
                                                                                self.hb_vni_500100_iface_ip,
                                                                                self.ha_vni_500101_iface_ip)
            logger.info("Send and validate traffic")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=VxlanConstants.VNI_500100_IFACE, sender_pkt_format=pkt_hb_ha_vni500100_vni500101,
                                      sender_count=VxlanConstants.PACKET_NUM_3, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VxlanConstants.HEX_500101,
                                          VxlanConstants.HEX_100_0_0_3), receiver_count=VxlanConstants.PACKET_NUM_0)

    @pytest.mark.build
    @pytest.mark.push_gate
    def test_evpn_vxlan_basic(self, cli_objects, interfaces):
        """
        This test will check basic EVPN VXLAN functionality.

        Test has next steps:
        1. Check VLAN to VNI mapping
        2. Do traffic validations
            - Send ping from HA to DUT via VNI 500100
            - Send ping from HA to DUT via VNI 500101
            - Send ping from HB to DUT via VNI 500100
            - Send ping from HB to DUT via VLAN 101
            - Send ping from HA to HB via VNI 500101 to VLAN 101
            - Send ping from HB to HA via VLAN 101 to VNI 500101
            - Send traffic from HB to HA via VNI 500100 to VNI 500100(negative)
            - Send traffic from HB to HA via VLAN 101 to VNI 500100(negative)
            - Send traffic from HB to HA via VLAN 101 to VNI 500100(routing)
            - Send traffic from HB to HA via VNI 500100 to VNI 500101(negative)
        3. Do CLI validations via FRR for: type-2, type-3 routes on DUT, HA, HB

                                                dut
                                           -------------------------------
                 ha                        | Loopback0 10.1.0.32/32      |                                  hb
          --------------------------- BGP  |                             |               ----------------------------
          | bond0 30.0.0.2/24       |------| PortChannel0001 30.0.0.1/24 |               | vni500100 100.0.0.3/24   |
          |                         |      | Vlan100 100.0.0.1/24        |               |                          |
          | vni500100 100.0.0.2/24  |      | Vlan101 101.0.0.1/24        |    BGP        |                          |
          | vni500101 101.0.0.2/24  |      |              PortChannel0002|---------------| bond0.40                 |
          ---------------------------      | VNI500100=Vlan100  Vlan40   |               | bond0.101 101.0.0.3/24   |
                                           | VNI500101=Vlan101  Vlan101  |               ----------------------------
                                           -------------------------------
                vtep 30.0.0.2                    vtep 10.1.0.32                                 vtep 40.0.0.3
              (vxlan encap/decap)              (vxlan encap/decap)                            (vxlan encap/decap)

        """
        with allure.step('Check CLI VLAN to VNI mapping'):
            cli_objects.dut.vxlan.check_vxlan_vlanvnimap(vlan_vni_map_list=[(VxlanConstants.VLAN_100, VxlanConstants.VNI_500100),
                                                                            (VxlanConstants.VLAN_101, VxlanConstants.VNI_500101)])
        with allure.step('Validate L3 connectivity'):
            self.validate_l3_connectivity()

        with allure.step('Validate VXLAN traffic'):
            self.validate_vxlan_traffic(interfaces)

        with allure.step('Validate evpn type 2 and type 3 routes'):
            self.validate_basic_evpn_type_2_3_route(cli_objects)
