import pytest
import logging
import os
import re
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from tests.common.helpers.assertions import pytest_assert
from tests.common.config_reload import config_reload
from tests.common.utilities import wait_until

IP_ADDRESS_LIST = ["10.255.255.1", "10.255.255.2", "10.255.255.3", "10.255.255.4"]
INTERNAL_PORTS = {"Mellanox-SN4700-O28": ["Ethernet224", "Ethernet232", "Ethernet240", "Ethernet248"]}

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.topology('t1'),
    pytest.mark.skip_check_dut_health
]


@pytest.fixture(scope="module", autouse=True)
def skip_non_smartswitch_testbed(duthost, tbinfo):
    if tbinfo['topo']['name'] != "t1-28-lag":
        pytest.skip("This test is only for smart switch")


@pytest.fixture(autouse=True)
def apply_ip_assignment_config(duthost):
    # Apply the ip assignment config if it was not applied in deployment
    config_applied_by_test = False
    config_facts = duthost.get_running_config_facts()
    if not config_facts.get('VLAN'):
        with allure.step('Apply virtual smart switch configuration'):
            duthost.copy(src='virtual_smart_switch/dpu_ip_assignment_config.json',
                         dest='/tmp/dpu_ip_assignment_config.json')
            duthost.shell('sudo sonic-cfggen -j /tmp/dpu_ip_assignment_config.json --write-to-db')
            duthost.shell('sudo config save -y')
            config_applied_by_test = True
            config_reload(duthost, safe_reload=True)

    yield

    if config_applied_by_test:
        with allure.step('Restore the config via loading minigraph'):
            config_reload(duthost, config_source='minigraph', safe_reload=True, check_intf_up_ports=True)


def test_dpu_ip_assignment(duthost):
    hwsku = duthost.facts["hwsku"]
    internal_port_list = INTERNAL_PORTS.get(hwsku, INTERNAL_PORTS["Mellanox-SN4700-O28"])
    with allure.step("Check the internal port status are up"):
        pytest_assert(duthost.links_status_up(internal_port_list), "Not all internal ports are up")
    with allure.step("Check the vlan interface is up and IP address is correct"):
        output = duthost.shell("show ip interface | grep Vlan4094")['stdout']
        pattern = r"10\.255\.255\.254.*up/up"
        pytest_assert(re.search(pattern, output),
                      "The vlan interface is not up or the IP address is not correct.")
    with allure.step("Check the vlan 4094 contains the internal ports"):
        output = duthost.shell("show vlan brief")['stdout']
        for port in internal_port_list:
            pytest_assert(re.search(port, output), f"The port {port} is not the member of vlan 4094")
    with allure.step("Check the DHCP server status"):
        output = duthost.shell("show dhcp_server ipv4 info")['stdout']
        pattern = r"Vlan4094.*PORT.*10\.255\.255\.254.*enabled"
        pytest_assert(re.search(pattern, output), "The DHCP server info is not correct.")
    with allure.step("Check the DHCP lease status"):
        def check_dhcp_lease():
            output = duthost.shell("show dhcp_server ipv4 lease")['stdout']
            for port in internal_port_list:
                if not re.search(port, output):
                    return False
            return True
        pytest_assert(wait_until(60, 5, 0, check_dhcp_lease), f"There is no lease for all internal ports, "
                                                              f"please check the test log.")
    for address in IP_ADDRESS_LIST:
        with allure.step(f"Ping the dpu IP address {address}"):
            duthost.shell(f"ping -c 5 {address}")
