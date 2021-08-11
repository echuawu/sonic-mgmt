import allure
import pytest
import logging

from retry.api import retry_call
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.config_templates.route_config_template import RouteConfigTemplate

logger = logging.getLogger()

"""

 VXLAN L2 Test Cases

 Documentation: https://wikinox.mellanox.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+L2+VXLAN+Documentation

"""


@pytest.fixture(autouse=True)
def static_route_configuration(topology_obj):
    # TODO: Move to main conftest.py once https://github.com/Azure/sonic-buildimage/issues/7028 fixed on 202012 image
    static_route_config_dict = {
        'dut': [{'dst': '10.1.1.32', 'dst_mask': 32, 'via': ['30.0.0.2']}]
    }

    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)

    yield

    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)


@pytest.mark.skip('Test does not work on master image SPC2/SCP3 - skipped until fix')
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('VXLAN Decap/Encap test case')
def test_vxlan_decap_encap(engines, players, cli_objects, upgrade_params):
    """
    Test checks that traffic pass via VXLAN tunnel from HA via DUT to HB and back
    Test has next steps:
    1. Check that tunnel configured using command "show vxlan tunnel"
    2. Check mapping VLAN to VNI using command "show vxlan vlanvnimap"
    3. Send PING via tunnel from HA interface vtep_76543 IP 23.45.0.1 to HB interface bond0.2345 IP 23.45.0.2

                                            dut
                                        -------------------------------
             ha                        | Loopback0 10.1.0.32/32      |                                  hb
      ---------------------------      |                             |               ----------------------------
      | bond0 30.0.0.2/24       |------| PortChannel0001 30.0.0.1/24 |               |                          |
      | dummy0 10.0.1.32/32     |      |                             |               |                          |
      | vtep_76543 23.45.0.1/24 |      |                             |               |                          |
      |                         |      |              PortChannel0002|---------------| bond0.2345 23.45.0.2/24  |
      ---------------------------      |                    Vlan2345 |               ----------------------------
                                       |                             |
                                       -------------------------------
    """
    if upgrade_params.is_upgrade_required:
        pytest.skip('PushGate with upgrade executed. Test not supported on branch 201911 which used as base version')

    hb_vlan2345_ip = '23.45.0.2'
    vlan = '2345'
    vni = '76543'
    vtep_iface = 'vtep_{}'.format(vni)

    # TODO: Workaround for bug https://redmine.mellanox.com/issues/2350931
    validation_create_arp = {'sender': 'ha', 'args': {'interface': 'bond0', 'count': 3, 'dst': '10.1.0.32'}}
    ping_checker_ha = PingChecker(players, validation_create_arp)
    retry_call(ping_checker_ha.run_validation, fargs=[], tries=3, delay=10, logger=logger)

    with allure.step('Checking that VXLAN tunnel configured'):
        expected_tunnel_info = {'vxlan tunnel name': 'vtep_76543',
                                'source ip': '10.1.0.32',
                                'destination ip': '',
                                'tunnel map name': 'map_76543_Vlan2345',
                                'tunnel map mapping(vni -> vlan)': '76543 -> Vlan2345'}

        cli_objects.dut.vxlan.check_vxlan_tunnels(engines.dut, expected_tunnels_info_list=[expected_tunnel_info])

    with allure.step('Checking VLAN {} mapping to VNI {}'.format(vlan, vni)):
        cli_objects.dut.vxlan.check_vxlan_vlanvnimap(engines.dut, vlan_vni_map_list=[(vlan, vni)])

    with allure.step('Sending 3 ping packets to {} from iface {}. '
                     'This steps will also trigger the arp learning process'.format(hb_vlan2345_ip, vtep_iface)):
        validation = {'sender': 'ha', 'args': {'iface': vtep_iface, 'count': 3, 'dst': hb_vlan2345_ip}}
        ping = PingChecker(players, validation)
        logger.info('Sending 3 ping packets to {} from iface {} via VXLAN tunnel'.format(hb_vlan2345_ip, vtep_iface))
        ping.run_validation()
