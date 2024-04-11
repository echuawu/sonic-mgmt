import os
import re


class WcmpConsts:
    FRR_CONFIG_FOLDER = 'frr_config'
    HB_ADVERTISED_ROUTE = "10.0.0.0/24"
    BGP_BANDWIDTH_COMMUNITY_CONFIG = 'set extcommunity bandwidth num-multipaths'
    ROUTE_PATTERN = re.compile(r'nexthop via (\S+) dev (\S+) weight (\d+)')
    WCMP_STATUS_ENABLED = 'enabled'
    WCMP_STATUS_DISABLED = 'disabled'
    WCMP_STATUS_INVALID = ['1', 'invalid_test']
    WCMP_STATUS_REDIS_CLI_ENABLED = 'true'
    WCMP_STATUS_REDIS_CLI_DISABLED = 'false'
    WCMP_STATUS_REDIS_CLI_INVALID = 'test_invalid'
    INTERFACE_FLAP_COUNT = 5
    WCMP_STATUS_FLAP_COUNT = 5
    WEIGHT_VALUE_50 = 50
    WEIGHT_VALUE_DEFAULT = 1
    REBOOT_TYPE = ['reboot']
    FRR_CONFIG_PATH = os.path.dirname(os.path.abspath(__file__)) + '/' + FRR_CONFIG_FOLDER
    PKT_COUNT = 5
    PKT_FILTER = 'host 10.0.0.1'
    GET_ERR_SYSLOG_CMD = 'sudo grep "ERR bgp" /var/log/syslog | tail -10'

    V4_CONFIG = {
        'dut_ha_1': '4.4.4.1', 'ha_dut_1': '4.4.4.2',
        'dut_ha_2': '1.1.1.1', 'ha_dut_2': '1.1.1.2',
        'dut_hb_1': '2.2.2.1', 'hb_dut_1': '2.2.2.3',
        'dut_hb_2': '3.3.3.1', 'hb_dut_2': '3.3.3.3',
        'hb_dut_ipv4_network': '10.0.0.0/24',
        'ha_dut_ipv4_network': '20.0.0.0/24'
    }

    V6_CONFIG = {
        'dut_ha_1': '4000::1', 'ha_dut_1': '4000::2',
        'dut_ha_2': '1000::1', 'ha_dut_2': '1000::2',
        'dut_hb_1': '2000::1', 'hb_dut_1': '2000::3',
        'dut_hb_2': '3000::1', 'hb_dut_2': '3000::3',
        'ha_dut_ipv6_network': '6000::/64',
        'hb_dut_ipv6_network': '5000::/64'
    }

    DUMMY_INTF_HA = {
        'name': 'dummy_ha',
        'ipv4_addr': '20.0.0.1', 'ipv4_mask': '24', 'ipv4_network': '20.0.0.0/24',
        'ipv6_addr': '6000::1', 'ipv6_mask': '64', 'ipv6_network': '6000::/64',
    }

    DUMMY_INTF_HB = {
        'name': 'dummy_hb',
        'ipv4_addr': '10.0.0.1', 'ipv4_mask': '24', 'ipv4_network': '10.0.0.0/24',
        'ipv6_addr': '5000::1', 'ipv6_mask': '64', 'ipv6_network': '5000::/64',
    }

    FRR_CONFIG_CONFIG_DICT = {
        'dut': {
            'configuration': {'config_name': 'dut_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_PATH},
            'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']
        },
        'ha': {
            'configuration': {'config_name': 'ha_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_PATH},
            'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']
        },
        'hb': {
            'configuration': {'config_name': 'hb_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_PATH},
            'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']
        }
    }
