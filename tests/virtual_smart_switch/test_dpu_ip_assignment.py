import pytest
import logging
import re
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from tests.common.helpers.assertions import pytest_assert
from tests.common.config_reload import config_reload
from tests.common.utilities import wait_until
from tests.common.platform.interface_utils import get_dpu_npu_ports_from_hwsku

IP_ADDRESS_LIST = {"Mellanox-SN4700-O28": ["10.255.255.1", "10.255.255.2", "10.255.255.3", "10.255.255.4"],
                   "ACS-SN4280": ["169.254.200.1", "169.254.200.2", "169.254.200.3", "169.254.200.4"]}

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
    # This is only for the virtual smart switch, the real one does not need this
    if "4700" in duthost.facts["hwsku"]:
        # Apply the ip assignment config if it was not applied in deployment
        config_applied_by_test = False
        config_facts = duthost.get_running_config_facts()
        if not config_facts.get('VLAN'):
            with allure.step('Apply virtual smart switch configuration'):
                duthost.shell('sudo config qos clear')
                duthost.copy(src='virtual_smart_switch/dpu_ip_assignment_config.json',
                             dest='/tmp/dpu_ip_assignment_config.json')
                duthost.shell('sudo sonic-cfggen -j /tmp/dpu_ip_assignment_config.json --write-to-db')
                duthost.shell('sudo config save -y')
                config_applied_by_test = True
                config_reload(duthost, safe_reload=True)

    yield

    if "4700" in duthost.facts["hwsku"]:
        if config_applied_by_test:
            with allure.step('Restore the config via loading minigraph'):
                config_reload(duthost, config_source='minigraph', safe_reload=True, check_intf_up_ports=True)


def test_dpu_ip_assignment(duthost):
    hwsku = duthost.facts["hwsku"]
    internal_port_list = get_dpu_npu_ports_from_hwsku(duthost)
    with allure.step("Check the internal port status are up"):
        pytest_assert(duthost.links_status_up(internal_port_list), "Not all internal ports are up")
    with allure.step("Check the DHCP lease status"):
        def check_dhcp_lease():
            duthost.shell("show dhcp_server ipv4 info")
            output = duthost.shell("show dhcp_server ipv4 lease")['stdout']
            for port in internal_port_list:
                if not re.search(port, output):
                    return False
            return True
        if "4700" in hwsku:
            lease_check_timeout = 600
            lease_check_interval = 30
        else:
            lease_check_timeout = 20
            lease_check_interval = 5
        pytest_assert(wait_until(lease_check_timeout, lease_check_interval, 0, check_dhcp_lease),
                      "There is no lease for all internal ports, "
                      "please check the test log.")
    for address in IP_ADDRESS_LIST.get(hwsku, IP_ADDRESS_LIST["ACS-SN4280"]):
        with allure.step(f"Ping the dpu IP address {address}"):
            duthost.shell(f"ping -c 5 {address}")
