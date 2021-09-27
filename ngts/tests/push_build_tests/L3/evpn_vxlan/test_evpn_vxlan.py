import allure
import logging
import pytest

from ngts.cli_wrappers.common.frr_clis_common import FrrCliCommon
from ngts.cli_wrappers.sonic.sonic_vxlan_clis import SonicVxlanCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker

"""

 EVPN VXLAN Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+EVPN+VXLAN+Documentation

"""

logger = logging.getLogger()

simple_packet = 'Ether(src="{}",dst="{}")/IP(src="{}",dst="{}")/UDP()'
tcpdump_vxlan_src_ip_filter = 'port 4789 and ether[76:4]={}'  # filter VXLAN packet with encapsulated src IP
hex_100_0_0_3 = '0x64000003'  # hex value for 100.0.0.3
hex_101_0_0_3 = '0x65000003'  # hex value for 101.0.0.3

dut_vlan_100_iface = 'Vlan100'
ha_bond_0_iface = 'bond0'
hb_vlan_101_iface = 'bond0.101'

rd_100 = '100'
rd_101 = '101'

vlan_100 = 100
vlan_101 = 101

vni_500100 = 500100
vni_500101 = 500101

vni_500100_iface = 'br_{}'.format(vni_500100)
vni_500101_iface = 'br_{}'.format(vni_500101)


@pytest.fixture(scope='class')
def get_used_mac_addresses(engines):
    dut_mac = SonicMacCli.get_mac_address_for_interface(engines.dut, dut_vlan_100_iface)
    ha_br_500100_mac = LinuxMacCli.get_mac_address_for_interface(engines.ha, vni_500100_iface)
    ha_br_500101_mac = LinuxMacCli.get_mac_address_for_interface(engines.ha, vni_500101_iface)
    hb_br_500100_mac = LinuxMacCli.get_mac_address_for_interface(engines.hb, vni_500100_iface)
    hb_bond0_101_mac = LinuxMacCli.get_mac_address_for_interface(engines.hb, hb_vlan_101_iface)

    return dut_mac, ha_br_500100_mac, ha_br_500101_mac, hb_br_500100_mac, hb_bond0_101_mac


class TestEvpnVxlan:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, players, interfaces, get_used_mac_addresses):
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

        self.dut_mac, self.ha_br_500100_mac, self.ha_br_500101_mac, self.hb_br_500100_mac, self.hb_bond0_101_mac = \
            get_used_mac_addresses

    @pytest.mark.skip('Test not supported. Once EVPN VXLAN will be supported - need to remove skip')
    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('Test EVPN VXLAN Basic')
    def test_evpn_vxlan_basic(self, upgrade_params):
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
        3. Do CLI validations via FRR for: type-2, type-3, type-5 routes on DUT, HA, HB

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

        :return: raise assertion error in case when test failed
        """

        if upgrade_params.is_upgrade_required:
            pytest.skip(
                'PushGate with upgrade executed. Test not supported on branch 202012 which used as base version')

        with allure.step('Check CLI VLAN to VNI mapping'):
            SonicVxlanCli.check_vxlan_vlanvnimap(self.engines.dut, vlan_vni_map_list=[(vlan_100, vni_500100),
                                                                                      (vlan_101, vni_500101)])

        # Ping from hosts to DUT
        with allure.step('Send ping from HA to DUT via VNI 500100'):
            ping_ha_dut_vni_500100 = {'sender': 'ha', 'args': {'interface': vni_500100_iface, 'count': 3,
                                                               'dst': self.dut_vlan_100_ip}}
            PingChecker(self.players, ping_ha_dut_vni_500100).run_validation()

        with allure.step('Send ping from HA to DUT via VNI 500101'):
            ping_ha_dut_vni_500101 = {'sender': 'ha', 'args': {'interface': vni_500101_iface, 'count': 3,
                                                               'dst': self.dut_vlan_101_ip}}
            PingChecker(self.players, ping_ha_dut_vni_500101).run_validation()

        with allure.step('Send ping from HB to DUT via VNI 500100'):
            ping_hb_dut_vni_500100 = {'sender': 'hb', 'args': {'interface': vni_500100_iface, 'count': 3,
                                                               'dst': self.dut_vlan_100_ip}}
            PingChecker(self.players, ping_hb_dut_vni_500100).run_validation()

        with allure.step('Send ping from HB to DUT via VLAN 101'):
            ping_hb_dut_vlan_101 = {'sender': 'hb', 'args': {'interface': hb_vlan_101_iface, 'count': 3,
                                                             'dst': self.dut_vlan_101_ip}}
            PingChecker(self.players, ping_hb_dut_vlan_101).run_validation()

        # Pings between hosts
        with allure.step('Send ping from HB to HA via VLAN 101 to VNI 500101'):
            ping_hb_ha_vlan_101_to_vni_500101 = {'sender': 'hb', 'args': {'interface': hb_vlan_101_iface, 'count': 3,
                                                                          'dst': self.ha_vni_500101_iface_ip}}
            PingChecker(self.players, ping_hb_ha_vlan_101_to_vni_500101).run_validation()

        with allure.step('Send ping from HA to HB via VNI 500101 to VLAN 101'):
            ping_ha_hb_vni_500101_to_vlan_101 = {'sender': 'ha', 'args': {'interface': vni_500101_iface, 'count': 3,
                                                                          'dst': self.hb_vlan_101_iface_ip}}
            PingChecker(self.players, ping_ha_hb_vni_500101_to_vlan_101).run_validation()

        # Routing
        with allure.step('Send traffic from HB to HA via VLAN 101 to VNI 500100(routing)'):
            pkt_hb_ha_vlan101_vni500100_r = simple_packet.format(self.hb_bond0_101_mac, self.dut_mac,
                                                                 self.hb_vlan_101_iface_ip,
                                                                 self.ha_vni_500100_iface_ip)
            validation_hb_ha_vlan101_vni500100_r = {'sender': 'hb',
                                                    'send_args': {'interface': hb_vlan_101_iface,
                                                                  'packets': pkt_hb_ha_vlan101_vni500100_r,
                                                                  'count': 3},
                                                    'receivers':
                                                        [
                                                            {'receiver': 'ha',
                                                             'receive_args': {
                                                                 'interface': ha_bond_0_iface,
                                                                 'filter': tcpdump_vxlan_src_ip_filter.format(
                                                                     hex_101_0_0_3),
                                                             }
                                                             }
                                                    ]
                                                    }
            ScapyChecker(self.players, validation_hb_ha_vlan101_vni500100_r).run_validation()

        # Negative validations
        with allure.step('Send traffic from HB to HA via VNI 500100 to VNI 500100(negative)'):
            pkt_hb_ha_vni500100_vni500100 = simple_packet.format(self.hb_br_500100_mac, self.ha_br_500100_mac,
                                                                 self.hb_vni_500100_iface_ip,
                                                                 self.ha_vni_500100_iface_ip)
            validation_hb_ha_vni500100_vni500100 = {'sender': 'hb',
                                                    'send_args': {'interface': vni_500100_iface,
                                                                  'packets': pkt_hb_ha_vni500100_vni500100,
                                                                  'count': 3},
                                                    'receivers':
                                                        [
                                                            {'receiver': 'ha',
                                                             'receive_args': {
                                                                 'interface': ha_bond_0_iface,
                                                                 'filter': tcpdump_vxlan_src_ip_filter.format(
                                                                     hex_100_0_0_3),
                                                                 'count': 0}}
                                                    ]
                                                    }
            ScapyChecker(self.players, validation_hb_ha_vni500100_vni500100).run_validation()

        with allure.step('Send traffic from HB to HA via VLAN 101 to VNI 500100(negative)'):
            pkt_hb_ha_vlan101_vni500100 = simple_packet.format(self.hb_bond0_101_mac, self.ha_br_500100_mac,
                                                               self.hb_vlan_101_iface_ip,
                                                               self.ha_vni_500100_iface_ip)
            validation_hb_ha_vlan101_vni500100 = {'sender': 'hb',
                                                  'send_args': {'interface': hb_vlan_101_iface,
                                                                'packets': pkt_hb_ha_vlan101_vni500100,
                                                                'count': 3},
                                                  'receivers':
                                                      [
                                                          {'receiver': 'ha',
                                                           'receive_args': {
                                                               'interface': ha_bond_0_iface,
                                                               'filter': tcpdump_vxlan_src_ip_filter.format(
                                                                   hex_101_0_0_3),
                                                               'count': 0}}
                                                  ]
                                                  }
            ScapyChecker(self.players, validation_hb_ha_vlan101_vni500100).run_validation()

        with allure.step('Send traffic from HB to HA via VNI 500100 to VNI 500101(negative)'):
            pkt_hb_ha_vni500100_vni500101 = simple_packet.format(self.hb_br_500100_mac, self.ha_br_500101_mac,
                                                                 self.hb_vni_500100_iface_ip,
                                                                 self.ha_vni_500101_iface_ip)
            validation_hb_ha_vni500100_vni500101 = {'sender': 'hb',
                                                    'send_args': {'interface': vni_500100_iface,
                                                                  'packets': pkt_hb_ha_vni500100_vni500101,
                                                                  'count': 3},
                                                    'receivers':
                                                        [
                                                            {'receiver': 'ha',
                                                             'receive_args': {
                                                                 'interface': ha_bond_0_iface,
                                                                 'filter': tcpdump_vxlan_src_ip_filter.format(
                                                                     hex_100_0_0_3),
                                                                 'count': 0}}
                                                    ]
                                                    }
            ScapyChecker(self.players, validation_hb_ha_vni500100_vni500101).run_validation()

        # CLI validations
        with allure.step('Validate CLI type-2 routes on DUT'):
            dut_type_2_info = FrrCliCommon.get_l2vpn_evpn_route_type_macip(self.engines.dut)
            FrrCliCommon.validate_type_2_route(dut_type_2_info, self.hb_bond0_101_mac, self.dut_loopback_ip, rd_101,
                                               self.hb_vlan_101_iface_ip)

        with allure.step('Validate CLI type-3 routes on DUT'):
            dut_type_3_info = FrrCliCommon.get_l2vpn_evpn_route_type_multicast(self.engines.dut)
            FrrCliCommon.validate_type_3_route(dut_type_3_info, self.ha_bond_0_ip, self.ha_bond_0_ip, rd_100)
            FrrCliCommon.validate_type_3_route(dut_type_3_info, self.ha_bond_0_ip, self.ha_bond_0_ip, rd_101)

            FrrCliCommon.validate_type_3_route(dut_type_3_info, self.hb_vlan_40_ip, self.hb_vlan_40_ip, rd_100)

        with allure.step('Validate CLI type-5 routes on DUT'):
            # TODO: implement type-5 route validation
            dut_type_5_info = FrrCliCommon.get_l2vpn_evpn_route_type_prefix(self.engines.dut)

        with allure.step('Validate CLI type-2 routes on HA'):
            ha_type_2_info = FrrCliCommon.get_l2vpn_evpn_route_type_macip(self.engines.ha)
            FrrCliCommon.validate_type_2_route(ha_type_2_info, self.hb_bond0_101_mac, self.dut_loopback_ip, rd_101,
                                               self.hb_vlan_101_iface_ip)

        with allure.step('Validate CLI type-3 routes on HA'):
            ha_type_3_info = FrrCliCommon.get_l2vpn_evpn_route_type_multicast(self.engines.ha)
            FrrCliCommon.validate_type_3_route(ha_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, rd_100)
            FrrCliCommon.validate_type_3_route(ha_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, rd_101)

        with allure.step('Validate CLI type-5 routes on HA'):
            # TODO: implement type-5 route validation
            ha_type_5_info = FrrCliCommon.get_l2vpn_evpn_route_type_prefix(self.engines.ha)

        with allure.step('Validate CLI type-2 routes on HB'):
            hb_type_2_info = FrrCliCommon.get_l2vpn_evpn_route_type_macip(self.engines.hb)

        with allure.step('Validate CLI type-3 routes on HB'):
            hb_type_3_info = FrrCliCommon.get_l2vpn_evpn_route_type_multicast(self.engines.hb)
            FrrCliCommon.validate_type_3_route(hb_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, rd_100)
            FrrCliCommon.validate_type_3_route(hb_type_3_info, self.dut_loopback_ip, self.dut_loopback_ip, rd_101)

        with allure.step('Validate CLI type-5 routes on HB'):
            # TODO: implement type-5 route validation
            hb_type_5_info = FrrCliCommon.get_l2vpn_evpn_route_type_prefix(self.engines.hb)
