import logging
import pytest
from .iface_loopback_action_helper import ACTION_DROP, NUM_OF_TOTAL_PACKETS
from .iface_loopback_action_helper import verify_traffic
from .iface_loopback_action_helper import config_loopback_action
from .iface_loopback_action_helper import clear_rif_counter
from .iface_loopback_action_helper import verify_interface_loopback_action
from .iface_loopback_action_helper import verify_rif_tx_err_count
from tests.common.helpers.assertions import pytest_assert
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure


pytestmark = [
    pytest.mark.topology('any'),
    pytest.mark.skip_check_dut_health
]
logger = logging.getLogger(__name__)
allure.logger = logger


@pytest.fixture(scope='module', autouse=True)
def check_global_configuration(duthost):
    config_facts = duthost.config_facts(host=duthost.hostname, source="running")['ansible_facts']
    wjh_global = config_facts.get('WJH', {})

    try:
        wjh_global = wjh_global['global']
        if wjh_global['mode'] != 'debug':
            pytest.skip("Debug mode is not enabled. Skipping test.")
    except Exception as e:
        pytest.fail("Could not fetch global configuration information.")


@pytest.fixture(scope='module', autouse=True)
def check_feature_enabled(duthost):
    features = duthost.feature_facts()['ansible_facts']['feature_facts']
    if 'what-just-happened' not in features or features['what-just-happened'] != 'enabled':
        pytest.skip("what-just-happened feature is not available. Skipping the test.")


def test_loopback_action_wjh(duthost, ptfadapter, ports_configuration):
    rif_interfaces = list(ports_configuration.keys())
    intf_count = len(rif_interfaces)
    action_list = [ACTION_DROP] * intf_count
    count_list = [NUM_OF_TOTAL_PACKETS] * intf_count
    with allure.step("Configure the loopback action to drop"):
        config_loopback_action(duthost, rif_interfaces, action_list)
    with allure.step("Verify the loopback acton is correct"):
        with allure.step("Check the looback action is configured correctly with cli command"):
            verify_interface_loopback_action(duthost, rif_interfaces, action_list)
        with allure.step("Check the loopback traffic"):
            with allure.step("Clear the rif counter"):
                clear_rif_counter(duthost)
            with allure.step("Check the traffic can be received or dropped as expected"):
                verify_traffic(duthost, ptfadapter, rif_interfaces, ports_configuration, action_list)
            with allure.step("Check the TX_ERR in rif counter statistic will increase or not as expected"):
                verify_rif_tx_err_count(duthost, rif_interfaces, count_list)
            with allure.step("Check WJH L3 drop group"):
                verify_wjh_l3_drop_group(duthost, rif_interfaces, ports_configuration)


def get_wjh_loopback_drop_items(duthost):
    """
    Get the wjh L3 loopback action drop items, Packets that will dropped due to loopback action will be counted by
    WJH in L3 drop group in severity warning.
    :param duthost: DUT hst object
    :return: Dictionary of L3 loopback action drop items
    Examples:
    {'Ethernet244': [{'#': '681',
                      'timestamp': '22/06/17 15:25:24.323',
                      'sport': 'Ethernet244',
                      'dport': 'N/A', 'VLAN': '58',
                      'smac': 'ee:46:86:41:a4:3d',
                      'dmac': '1c:34:da:1d:ea:00',
                      'ethtype': 'Dot1Q',
                      'src ip:port': '11.11.11.11',
                      'dst ip:port': '11.8.0.10',
                      'ip proto': 'ip',
                      'drop group': 'L3',
                      'severity': 'Warn',
                      'drop reason - Recommended action': 'Router interface loopback - Validate the interface configuration'
                      },
                     ...],
      'Ethernet248': [{'#': '691',
                       'timestamp': '22/06/17 15:25:27.234',
                       'sport': 'Ethernet248',
                       'dport': 'N/A',
                       'vlan': '59',
                       'smac': 'de:50:79:3b:04:3e',
                       'dmac': '1c:34:da:1d:ea:00',
                       'ethtype': 'Dot1Q',
                       'src ip:port': '11.11.11.11',
                       'dst ip:port': '11.9.0.10',
                       'ip proto': 'ip',
                       'drop group': 'L3',
                       'severity': 'Warn',
                       'drop reason - Recommended action': 'Router interface loopback - Validate the interface configuration'
                       },
                    ...],
                    ...
    }
    """
    wjh_loopback_drop_items = {}
    wjh_poll_forward_list = duthost.show_and_parse('show what-just-happened poll forwarding', header_len=2)

    for item in wjh_poll_forward_list:
        if 'sport' in item and item['sport']:
            port = item['sport']
            pre_port = port
            pre_item = item
        else:
            port = pre_port
            pre_item['drop reason - recommended action'] = " ".join([pre_item['drop reason - recommended action'],
                                                                     item['drop reason - recommended action']]).strip()
        if pre_item['drop group'] == 'L3' and pre_item['drop reason - recommended action'] == \
                'Router interface loopback - Validate the interface configuration':
            if port not in wjh_loopback_drop_items.keys():
                wjh_loopback_drop_items[port] = []
            wjh_loopback_drop_items[port].append(pre_item)
    return wjh_loopback_drop_items


def verify_wjh_l3_drop_group(duthost, expect_drop_rif_interface, ports_configuration):
    wjh_loopback_drop_items = get_wjh_loopback_drop_items(duthost)
    for rif_interface in expect_drop_rif_interface:
        port = ports_configuration[rif_interface]['port']
        pytest_assert(port in wjh_loopback_drop_items.keys(),
                      "Packets that dropped due to loopback action is not counted by WJH in L3 drop group "
                      "in severity warning for {}".format(rif_interface))

