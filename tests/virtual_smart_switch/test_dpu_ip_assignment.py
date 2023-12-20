import pytest
import logging
import re
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from tests.common.helpers.assertions import pytest_assert

IP_ADDRESS_LIST = ["10.255.255.1", "10.255.255.2", "10.255.255.3", "10.255.255.4"]
INTERNAL_PORTS = {"Mellanox-SN4700-O28": ["Ethernet224", "Ethernet232", "Ethernet240", "Ethernet248"]}

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.topology('t1'),
    pytest.mark.skip_check_dut_health
]


@pytest.fixture(autouse=True)
def skip_non_smartswitch_testbed(duthost, duts_running_config_facts):
    cfg_facts = duts_running_config_facts[duthost.hostname]
    localhost_type = cfg_facts[0][1]["DEVICE_METADATA"]["localhost"].get('type', "")
    if localhost_type != "SmartSwitch":
        pytest.skip("This test is only for smart switch")


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
        output = duthost.shell("show dhcp-server ipv4 info")['stdout']
        pattern = r"Vlan4094.*PORT.*10\.255\.255\.254.*enabled"
        pytest_assert(re.search(pattern, output), "The DHCP server info is not correct.")
        output = duthost.shell("show dhcp-server ipv4 lease")['stdout']
        for port in internal_port_list:
            pytest_assert(re.search(port, output), f"There is no lease for port {port}.")
    for address in IP_ADDRESS_LIST:
        with allure.step(f"Ping the dpu IP address {address}"):
            duthost.shell(f"ping -c 5 {address}")
