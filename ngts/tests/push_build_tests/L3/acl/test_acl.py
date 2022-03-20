import allure
import pytest
import logging
import ngts.helpers.acl_helper as acl_helper
from ngts.helpers.acl_helper import ACLConstants
from enum import Enum


logger = logging.getLogger()


class RuleType(Enum):
    match_forward = 1
    match_drop = 2
    unmatch = 3


@pytest.fixture(scope="module", params=ACLConstants.IP_VERSION_LIST)
def ip_version(request):
    return request.param


@pytest.fixture(scope="module", params=ACLConstants.STAGE_LIST)
def stage(request):
    return request.param


def test_acl_config(engines, acl_table_config_list):
    """
    Test the acl tables and rules can be added and removed correctly
    :param engines: engines fixture
    :param acl_table_config_list: acl_table_config_list fixture, which is a list of value returned from generate_acl_table
    """
    engine_dut = engines.dut
    with allure.step('Verify the acl tables are added'):
        acl_helper.verify_acl_tables_exist(engine_dut, acl_table_config_list, True)
    with allure.step('Verify the acl rules are added'):
        acl_helper.verify_acl_rules(engine_dut, acl_table_config_list, True)
    with allure.step('Remove acl rules'):
        acl_helper.clear_acl_rules(engine_dut)
    with allure.step('Verify the acl rules are removed'):
        acl_helper.verify_acl_rules(engine_dut, acl_table_config_list, False)
    with allure.step('Delete acl table'):
        acl_helper.remove_acl_table(engine_dut, acl_table_config_list)
    with allure.step('Verify the acl tables are removed'):
        acl_helper.verify_acl_tables_exist(engine_dut, acl_table_config_list, False)
    with allure.step('Add acl table'):
        acl_helper.add_acl_table(engine_dut, acl_table_config_list)
    with allure.step('Add acl rules'):
        acl_helper.add_acl_rules(engine_dut, acl_table_config_list)
    with allure.step('Verify the acl tables are added back'):
        acl_helper.verify_acl_tables_exist(engine_dut, acl_table_config_list, True)
    with allure.step('Verify the acl rules are added back'):
        acl_helper.verify_acl_rules(engine_dut, acl_table_config_list, True)


def test_acl_traffic_match(topology_obj, engines, interfaces, ip_version, stage):
    """
    Test the acl rules can work with sending traffic to match one of the rule.
    :param topology_obj: topology_obj fixture
    :param engines: engines
    :param interfaces: interfaces
    :param ip_version: ip_version fixture, ipv4 or ipv6
    :param stage: stage fixture, ingress or egress
    """

    with allure.step('Verify the traffic match acl rule with src ip can be forwarded'):
        rule_name = "RULE_1"
        traffic_param = get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, 'forward_src_ip_match',
                                               'forward_dst_ip_match', RuleType.match_forward)
        acl_helper.verify_acl_traffic(topology_obj, engines.dut, traffic_param, rule_name, True, True)
    with allure.step('Verify the traffic match acl rule with dst ip can be forwarded'):
        rule_name = "RULE_2"
        traffic_param = get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, 'unused_src_ip',
                                               'forward_dst_ip_match', RuleType.match_forward)
        acl_helper.verify_acl_traffic(topology_obj, engines.dut, traffic_param, rule_name, True, True)

    with allure.step('Verify the traffic match acl rule with src ip can be dropped'):
        rule_name = "RULE_3"
        traffic_param = get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, 'drop_src_ip_match',
                                               'drop_dst_ip_match', RuleType.match_drop)
        acl_helper.verify_acl_traffic(topology_obj, engines.dut, traffic_param, rule_name, True, False)

    with allure.step('Verify the traffic match acl rule with dst ip can be dropped'):
        rule_name = "RULE_4"
        traffic_param = get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, 'unused_src_ip',
                                               'drop_dst_ip_match', RuleType.match_drop)
        acl_helper.verify_acl_traffic(topology_obj, engines.dut, traffic_param, rule_name, True, False)


def test_acl_traffic_not_match(topology_obj, engines, interfaces, ip_version, stage):
    """
    Test the action  if no acl rule matched.
    :param topology_obj: topology_obj fixture
    :param engines: engines
    :param interfaces: interfaces
    :param ip_version: ip_version fixture, ipv4 , ipv6
    :param stage: stage fixture, ingress or egress
    """
    with allure.step('Verify the traffic unmatch any acl rule can be forwarded for both ingress and egress'):
        expect_received = True
        rule_name = ""
        expect_match = False
        traffic_param = get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, 'unused_src_ip',
                                               'unmatch_dst_ip', RuleType.unmatch)
        acl_helper.verify_acl_traffic(topology_obj, engines.dut, traffic_param, rule_name, expect_match, expect_received)


def get_acl_traffic_params(topology_obj, interfaces, ip_version, stage, src_ip_type, dst_ip_type, rule_type):
    """
    Get the traffic params which will be used to verify the specified acl rule.
    :param topology_obj: interfaces fixture
    :param interfaces: interfaces fixture
    :param ip_version: ip_version fixture, ipv4 , ipv6
    :param stage: stage fixture, ingress or egress
    :param src_ip_type: the param name which will be used to get the src ip
    :param dst_ip_type: the param name which will be used to get the dst ip
    :param rule_type: the rule type, it is enum, defined as RuleType
    :return: dictionary of traffic params
    """
    if stage == 'ingress':
        sender = 'ha'
        receiver = 'hb'
        src_port = interfaces.ha_dut_2
        dst_port = interfaces.hb_dut_1
        next_hop_port = interfaces.dut_ha_2
        if rule_type == RuleType.match_forward:
            vlan_id = 120
        elif rule_type == RuleType.match_drop:
            vlan_id = 122
        else:
            vlan_id = 124
    else:
        sender = 'hb'
        receiver = 'ha'
        src_port = interfaces.hb_dut_1
        next_hop_port = interfaces.dut_hb_1
        dst_port = interfaces.ha_dut_2
        if rule_type == RuleType.match_forward:
            vlan_id = 121
        elif rule_type == RuleType.match_drop:
            vlan_id = 123
        else:
            vlan_id = 125

    _, acl_table_name = acl_helper.generate_table_name(stage, ip_version)
    acl_rules_args = acl_helper.get_rules_template_file_args(acl_table_name)

    src_mac = get_mac_port_address(topology_obj, sender, src_port)
    dst_mac = get_mac_port_address(topology_obj, "dut", next_hop_port)
    src_ip = acl_helper.get_ip_addr_by_acl_rule_action_and_match_key(acl_rules_args, src_ip_type)
    dst_ip = acl_helper.get_ip_addr_by_acl_rule_action_and_match_key(acl_rules_args, dst_ip_type)
    src_port = f"{src_port}.{vlan_id}" if vlan_id else src_port
    traffic_param = {'table_name': acl_table_name,
                     'sender': sender,
                     'receiver': receiver,
                     'src_port': src_port,
                     'dst_port': dst_port,
                     'src_ip': src_ip,
                     'dst_ip': dst_ip,
                     'traffic_type': 'tcp',
                     'ip_version': ip_version,
                     'src_mac': src_mac,
                     'dst_mac': dst_mac}
    return traffic_param


def get_mac_port_address(topology_obj, host, port):
    """
    Get the port mac address for the specified port on the host(ha, hb or dut)
    :param topology_obj: topology_obj fixture object
    :param host: ha, hb, dut
    :param port: the port name
    :return: mac address
    """
    cli_object = topology_obj.players[host]['cli']
    engine = topology_obj.players[host]['engine']
    return cli_object.mac.get_mac_address_for_interface(engine, port)
