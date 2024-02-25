import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.acl.acl import Acl
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType, AclConsts
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from scapy import config
from scapy import route
from scapy.ansmachine import send
from scapy.layers.inet import IP, TCP, ICMP
from scapy.all import *

logger = logging.getLogger()

RULE_CONFIG_FUNCTION = {
    AclConsts.ACTION: lambda rule_id_obj, param: rule_id_obj.action.set(param),
    AclConsts.ACTION_LOG_PREFIX: lambda rule_id_obj, param: rule_id_obj.action.log.set_log_prefix(param),
    AclConsts.REMARK: lambda rule_id_obj, param: rule_id_obj.set_remark(param),

    AclConsts.SOURCE_PORT: lambda rule_id_obj, param: rule_id_obj.match.ip.source_port.set(param),
    AclConsts.DEST_PORT: lambda rule_id_obj, param: rule_id_obj.match.ip.dest_port.set(param),
    AclConsts.FRAGMENT: lambda rule_id_obj, param: rule_id_obj.match.ip.set_fragment(),
    AclConsts.ECN_FLAGS: lambda rule_id_obj, param: rule_id_obj.match.ip.ecn.flags.set(param),
    AclConsts.ECN_IP_ECT: lambda rule_id_obj, param: rule_id_obj.match.ip.ecn.set_ecn_ip_ect(param),
    AclConsts.TCP_FLAGS: lambda rule_id_obj, param: rule_id_obj.match.ip.tcp.flags.set(param),
    AclConsts.TCP_MASK: lambda rule_id_obj, param: rule_id_obj.match.ip.tcp.mask.set(param),
    AclConsts.TCP_STATE: lambda rule_id_obj, param: rule_id_obj.match.ip.state.set(param),
    AclConsts.TCPMSS: lambda rule_id_obj, param: rule_id_obj.match.ip.tcp.set_tcpmss(param),
    AclConsts.ALL_TCPMSS_EXCEPT: lambda rule_id_obj, param: rule_id_obj.match.ip.tcp.set_all_tcpmss_except(param),
    AclConsts.SOURCE_IP: lambda rule_id_obj, param: rule_id_obj.match.ip.set_source_ip(param),
    AclConsts.DEST_IP: lambda rule_id_obj, param: rule_id_obj.match.ip.set_dest_ip(param),
    AclConsts.ICMP_TYPE: lambda rule_id_obj, param: rule_id_obj.match.ip.set_icmp_type(param),
    AclConsts.ICMPV6_TYPE: lambda rule_id_obj, param: rule_id_obj.match.ip.set_icmpv6_type(param),
    AclConsts.IP_PROTOCOL: lambda rule_id_obj, param: rule_id_obj.match.ip.set_protocol(param),
    AclConsts.RECENT_LIST_NAME: lambda rule_id_obj, param: rule_id_obj.match.ip.recent_list.set_name(param),
    AclConsts.RECENT_LIST_UPDATE: lambda rule_id_obj, param: rule_id_obj.match.ip.recent_list.set_update_interval(param),
    AclConsts.RECENT_LIST_HIT: lambda rule_id_obj, param: rule_id_obj.match.ip.recent_list.set_hit_count(param),
    AclConsts.RECENT_LIST_ACTION: lambda rule_id_obj, param: rule_id_obj.recent_list.set_action(param),
    AclConsts.HASHLIMIT_NAME: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_name(param),
    AclConsts.HASHLIMIT_RATE: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_rate_limit(param),
    AclConsts.HASHLIMIT_BURST: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_burst(param),
    AclConsts.HASHLIMIT_MODE: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_mode(param),
    AclConsts.HASHLIMIT_EXPIRE: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_expire(param),
    AclConsts.HASHLIMIT_DEST_MASK: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_destination_mask(param),
    AclConsts.HASHLIMIT_SRC_MASK: lambda rule_id_obj, param: rule_id_obj.match.ip.hashlimit.set_source_mask(param),

    AclConsts.SOURCE_MAC: None,
    AclConsts.SOURCE_MAC_MASK: None,
    AclConsts.DEST_MAC: None,
    AclConsts.DEST_MAC_MASK: None,
    AclConsts.MAC_PROTOCOL: None
}


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_rules_order(engines, test_api):
    """
    Validate acl rules order by priority of rules order.
    the first rule that match the packet should applied even if the next rule also match but the action is different.
    steps:
    1. config an ACL with 2 rules
    2. send packet
    3. validate that the action we do on the packet is as the first rule.
    """
    TestToolkit.tested_api = test_api
    with allure.step("Define ACL with 2 rules"):

        with allure.step("Define ACL"):
            acl = Acl()
            acl_id = "TEST_ACL1"
            acl.set(acl_id).verify_result()
            acl_id_obj = acl.acl_id[acl_id]
            acl_id_obj.set(AclConsts.TYPE, 'ipv4').verify_result()
            expected_acl_dict = {acl_id: {AclConsts.RULE: {}, AclConsts.TYPE: 'ipv4'}}

        with allure.step("Config 2 rules"):
            rule_dict = {AclConsts.ACTION: AclConsts.DENY, AclConsts.SOURCE_IP: 'ANY', AclConsts.IP_PROTOCOL: 'icmp',
                         AclConsts.ICMP_TYPE: 'echo-request'}
            rule_id_1 = '1'
            config_rule(engines.dut, acl_id_obj, rule_id_1, rule_dict)
            rule_id_2 = '2'
            rule_dict[AclConsts.ACTION] = AclConsts.PERMIT
            config_rule(engines.dut, acl_id_obj, rule_id_2, rule_dict)

            expected_acl_dict[acl_id][AclConsts.RULE].update({rule_id_1: {AclConsts.ACTION: {AclConsts.DENY: {}}, AclConsts.MATCH:
                                                                          {AclConsts.IP: {AclConsts.SOURCE_IP: 'ANY', AclConsts.PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}}}})
            expected_acl_dict[acl_id][AclConsts.RULE].update({rule_id_2: {AclConsts.ACTION: {AclConsts.PERMIT: {}}, AclConsts.MATCH:
                                                                          {AclConsts.IP: {AclConsts.SOURCE_IP: 'ANY', AclConsts.PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}}}})

        with allure.step("Validate configuration with show commands"):
            acl_id_output = acl_id_obj.parse_show()
            assert expected_acl_dict[acl_id] == acl_id_output, \
                f'Got unexpected acl output after acl and rules configuration\n' \
                f'expected: {expected_acl_dict[acl_id]}\n' \
                f'but got: {acl_id_output}'

    with allure.step("Define ACL to mgmt interface"):
        mgmt_port = MgmtPort()
        mgmt_port.interface.acl.set(acl_id).verify_result()
        mgmt_port.interface.acl.acl_id[acl_id].inbound.set(AclConsts.CONTROL_PLANE, apply=True)

        with allure.step("Validate configuration with show commands"):
            interface_acl_output = mgmt_port.interface.acl.acl_id[acl_id].parse_show()
            assert expected_acl_dict[acl_id][AclConsts.RULE].keys() == interface_acl_output[AclConsts.STATISTICS].keys(), \
                f'Got unexpected mgmt interface acl output after mgmt configuration\n' \
                f'expected: {expected_acl_dict[acl_id][AclConsts.RULE].keys()}\n' \
                f'but got: {interface_acl_output[AclConsts.STATISTICS].keys()}'

    with allure.step("Validate rule order"):
        rule_packets_before = get_rule_packets(mgmt_port, acl_id)
        ping_packet = IP(dst=engines.dut.ip) / ICMP()
        send(ping_packet)
        rule_packets_after = get_rule_packets(mgmt_port, acl_id)
        assert rule_packets_after[rule_id_1] > rule_packets_before[rule_id_1], \
            f'we expect to see increase in rule id {rule_id_1} counter - cause the first rule should be applied'
        assert rule_packets_after[rule_id_2] == rule_packets_before[rule_id_2], \
            f'we expect to see that the counter of rule id {rule_id_2} will not change - cause the first rule should be applied and not the second'

    with allure.step("Remove the first rule"):
        acl_id_obj.rule.rule_id[rule_id_1].unset(apply=True)
        expected_acl_dict[acl_id][AclConsts.RULE].pop(rule_id_1)
        acl_id_output = acl_id_obj.parse_show()
        assert expected_acl_dict[acl_id] == acl_id_output, f'Got unexpected acl output after removing 1 rule\n' \
            f'expected: {expected_acl_dict[acl_id]}\nbut got: {acl_id_output}'
        interface_acl_output = mgmt_port.interface.acl.acl_id[acl_id].parse_show()
        assert expected_acl_dict[acl_id][AclConsts.RULE].keys() == interface_acl_output[AclConsts.STATISTICS].keys(), \
            f'Got unexpected mgmt interface acl output after removing 1 rule\n' \
            f'expected: {expected_acl_dict[acl_id][AclConsts.RULE].keys()}\n' \
            f'but got: {interface_acl_output[AclConsts.STATISTICS].keys()}'
        rule_packets_before = get_rule_packets(mgmt_port, acl_id)
        send(ping_packet)
        rule_packets_after = get_rule_packets(mgmt_port, acl_id)
        assert rule_packets_after[rule_id_2] > rule_packets_before[rule_id_2], \
            f'we expect to see that the counter of rule id {rule_id_2} will not change - cause the first rule should be applied and not the second'


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_order(engines, test_api):
    """
    Validate ACLs rules order by priority of ACL order.
    the first rule in the first acl that match the packet should applied.
    steps:
    1. config 2 ACLs with a rule
    2. send packet
    3. validate that the action we do on the packet is as the first ACL rule.
    """
    TestToolkit.tested_api = test_api

    with allure.step("Define ACLs with rule"):
        acl_type = 'ipv4'
        mgmt_port = MgmtPort()
        sonic_mgmt_ip = engines.sonic_mgmt.ip
        rule_id = '1'
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.DENY, AclConsts.SOURCE_IP: sonic_mgmt_ip,
                                   AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}

        acl_id_1 = "TEST_ACL_1"
        acl_id_1_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_1, acl_type, rule_id,
                                                                  rule_configuration_dict, mgmt_port, AclConsts.INBOUND, AclConsts.CONTROL_PLANE)

        acl_id_2 = "TEST_ACL_2"
        sonic_mgmt_prefix_or_netmask = sonic_mgmt_ip + random.choice(['/255.255.255.0', '/32'])
        rule_conf_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.SOURCE_IP: sonic_mgmt_prefix_or_netmask,
                          AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}
        acl_id_2_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_2, acl_type, rule_id, rule_conf_dict,
                                                                  mgmt_port, AclConsts.INBOUND, AclConsts.CONTROL_PLANE)

    with allure.step("Validate configuration with show commands"):
        interface_acl_1_output = mgmt_port.interface.acl.acl_id[acl_id_1].parse_show()
        interface_acl_2_output = mgmt_port.interface.acl.acl_id[acl_id_2].parse_show()
        assert interface_acl_1_output[AclConsts.STATISTICS].keys() == interface_acl_2_output[AclConsts.STATISTICS].keys(), \
            f'Got unexpected mgmt interface acl output after mgmt configuration'

    with allure.step("Validate ACL rule order"):
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_1)
        rule_packets_2_before = get_rule_packets(mgmt_port, acl_id_2)
        ping_packet = IP(dst=engines.dut.ip, src=sonic_mgmt_ip) / ICMP()
        send(ping_packet)
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_1)
        rule_packets_2_after = get_rule_packets(mgmt_port, acl_id_2)
        assert rule_packets_1_after[rule_id] > rule_packets_1_before[rule_id], \
            f'we expect to see increase in acl {acl_id_1} rule id {rule_id} counter - cause the first acl should be applied'
        assert rule_packets_2_after[rule_id] == rule_packets_2_before[rule_id], \
            f'we expect to see that the counter of acl {acl_id_2} rule id {rule_id} will not change - cause the first acl should be applied and not the second'

    with allure.step("Remove the first rule"):
        mgmt_port.interface.acl.unset(acl_id_1).verify_result()
        acl_id_1_obj.unset(apply=True)
        acl_output = Acl().parse_show()
        assert acl_id_1 not in acl_output.keys(), 'Got unexpected acl output after acl removal'
        interface_acl_output = mgmt_port.interface.acl.parse_show()
        assert acl_id_1 not in interface_acl_output.keys(), 'Got unexpected mgmt interface acl output after acl removal'
        rule_packets_before = get_rule_packets(mgmt_port, acl_id_2)
        send(ping_packet)
        rule_packets_after = get_rule_packets(mgmt_port, acl_id_2)
        assert rule_packets_after[rule_id] > rule_packets_before[rule_id], \
            f'we expect to see increase in acl {acl_id_2} rule id {rule_id} counter - cause the first acl has removed'


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_ipv6(engines, test_api):
    """
    Validate ACLs rules over ipv6.
    steps:
    1. config ACL with a rule
    2. send packet
    3. validate counters increase
    """
    TestToolkit.tested_api = test_api

    with allure.step("Define ACLs with rule"):
        acl_type = 'ipv6'
        mgmt_port = MgmtPort()
        ipv6_addr = "2001:db8:abcd:0012:0000:0000:0000:00ef"
        ipv6_prefix_or_netmask = ipv6_addr + '/64'
        rule_id = '1'
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.DENY, AclConsts.SOURCE_IP: ipv6_addr}

        acl_id_1 = "TEST_ACL_IPV6"
        acl_id_1_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_1, acl_type, rule_id,
                                                                  rule_configuration_dict, mgmt_port, AclConsts.INBOUND, AclConsts.CONTROL_PLANE)

        switch_ipv6_addr = mgmt_port.interface.get_ipv6_address()

    with allure.step("Validate ACL counters"):
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_1)
        ping_packet = IPv6(dst=switch_ipv6_addr, src=ipv6_addr) / ICMPv6EchoRequest()
        send(ping_packet)
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_1)
        assert rule_packets_1_after[rule_id] > rule_packets_1_before[rule_id], \
            f'we expect to see increase in acl {acl_id_1} rule id {rule_id} counter'

    with allure.step("Change the rule- use ipv6 prefix"):
        config_rule(engines.dut, acl_id_1_obj, rule_id,
                    {AclConsts.ACTION: AclConsts.DENY, AclConsts.SOURCE_IP: ipv6_prefix_or_netmask})
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_1)
        ping_packet = IPv6(dst=switch_ipv6_addr, src=ipv6_addr) / ICMPv6EchoRequest()
        send(ping_packet)
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_1)
        assert rule_packets_1_after[rule_id] > rule_packets_1_before[rule_id], \
            f'we expect to see increase in acl {acl_id_1} rule id {rule_id} counter'


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_loopback(engines, test_api):
    """
    Validate ACLs rules over the loopback
    steps:
    1. config ACL with a rule
    2. send packet
    3. validate counters increase
    """
    TestToolkit.tested_api = test_api

    with allure.step("Define ACLs with rule"):
        acl_type = 'ipv4'
        mgmt_port = MgmtPort('lo')
        sonic_mgmt_ip = engines.sonic_mgmt.ip
        rule_id = '1'
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT}

        acl_id_1 = "TEST_ACL_LOOPBACK"
        acl_id_1_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_1, acl_type, rule_id,
                                                                  rule_configuration_dict, mgmt_port, AclConsts.INBOUND, AclConsts.CONTROL_PLANE)

    with allure.step("Validate ACL counters"):
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_1)
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_1)
        assert rule_packets_1_after[rule_id] > rule_packets_1_before[rule_id], \
            f'we expect to see increase in acl {acl_id_1} rule id {rule_id} counter - cause the first acl should be applied'


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_acl_commands(engines, test_api):
    """
    Validate acl show commands.
    steps:
    1. config an ACL with rules
    2. validate show commands
    """
    TestToolkit.tested_api = test_api
    with allure.step("Define ACL with rules"):

        with allure.step("Define ACL"):
            acl = Acl()
            acl_id = "TEST_ACL1"
            acl.set(acl_id).verify_result()
            acl_id_obj = acl.acl_id[acl_id]
            acl_id_obj.set(AclConsts.TYPE, 'ipv4').verify_result()
            expected_acl_dict = {acl_id: {AclConsts.RULE: {}, AclConsts.TYPE: 'ipv4'}}

        with allure.step("Config 3 rules"):
            rule_id_1 = '1'
            config_rule(engines.dut, acl_id_obj, rule_id_1, {AclConsts.ACTION: AclConsts.DENY, AclConsts.REMARK: "description", AclConsts.SOURCE_IP: 'ANY',
                                                             AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'})
            expected_acl_dict[acl_id][AclConsts.RULE].update(
                {rule_id_1: {AclConsts.ACTION: {AclConsts.DENY: {}}, AclConsts.REMARK: "description", AclConsts.MATCH:
                             {AclConsts.IP: {AclConsts.SOURCE_IP: 'ANY', AclConsts.PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}}}})

            rule_id_2 = '2'
            config_rule(engines.dut, acl_id_obj, rule_id_2, {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: 'tcp',
                                                             AclConsts.DEST_PORT: 'snmp', AclConsts.ECN_FLAGS: 'tcp-ece', AclConsts.ECN_IP_ECT: 2})
            expected_acl_dict[acl_id][AclConsts.RULE].update(
                {rule_id_2: {AclConsts.ACTION: {AclConsts.PERMIT: {}}, AclConsts.MATCH:
                             {AclConsts.IP: {AclConsts.PROTOCOL: 'tcp', AclConsts.DEST_PORT: {'snmp': {}},
                                             'ecn': {AclConsts.FLAGS: {'tcp-ece': {}}, AclConsts.IP_ECT: 2}}}}})

            rule_id_3 = '3'
            config_rule(engines.dut, acl_id_obj, rule_id_3,
                        {AclConsts.ACTION: AclConsts.LOG, AclConsts.IP_PROTOCOL: 'tcp', AclConsts.TCP_FLAGS: 'syn', AclConsts.TCP_MASK: 'syn'})
            expected_acl_dict[acl_id][AclConsts.RULE].update(
                {rule_id_3: {AclConsts.ACTION: {AclConsts.LOG: {}}, AclConsts.MATCH:
                             {AclConsts.IP: {AclConsts.PROTOCOL: 'tcp', 'tcp':
                                             {AclConsts.FLAGS: {'syn': {}}, AclConsts.MASK: {'syn': {}}}}}}})

        with allure.step("Validate configuration with show commands"):
            rule_id_1_obj = acl_id_obj.rule.rule_id[rule_id_1]
            acl_output = acl.parse_show()  # nv show acl
            acl_id_output = acl_id_obj.parse_show()  # nv show acl <acl-id>
            rule_output = acl_id_obj.rule.parse_show()  # nv show acl <acl-id> rule
            rule_id_1_output = rule_id_1_obj.parse_show()  # nv show acl <acl-id> rule <rule-id>
            action_show = rule_id_1_obj.action.parse_show()
            match_show = rule_id_1_obj.match.parse_show()
            match_ip_show = rule_id_1_obj.match.ip.parse_show()
            dest_port_show = acl_id_obj.rule.rule_id[rule_id_2].match.ip.dest_port.parse_show()
            tcp_show = acl_id_obj.rule.rule_id[rule_id_3].match.ip.tcp.parse_show()
            tcp_flags_show = acl_id_obj.rule.rule_id[rule_id_3].match.ip.tcp.flags.parse_show()
            tcp_mask_show = acl_id_obj.rule.rule_id[rule_id_3].match.ip.tcp.mask.parse_show()
            ecn_show = acl_id_obj.rule.rule_id[rule_id_2].match.ip.ecn.parse_show()
            ecn_flags_show = acl_id_obj.rule.rule_id[rule_id_2].match.ip.ecn.flags.parse_show()
            assert expected_acl_dict[acl_id] == acl_output[acl_id]
            assert expected_acl_dict[acl_id] == acl_id_output
            assert expected_acl_dict[acl_id][AclConsts.RULE] == rule_output
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_1] == rule_id_1_output
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_1][AclConsts.ACTION] == action_show  # bug 3659032
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_1][AclConsts.MATCH] == match_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_1][AclConsts.MATCH][AclConsts.IP] == match_ip_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_2][AclConsts.MATCH][AclConsts.IP][AclConsts.DEST_PORT] == dest_port_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_3][AclConsts.MATCH][AclConsts.IP]['tcp'] == tcp_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_3][AclConsts.MATCH][AclConsts.IP]['tcp'][AclConsts.FLAGS] == tcp_flags_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_3][AclConsts.MATCH][AclConsts.IP]['tcp'][AclConsts.MASK] == tcp_mask_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_2][AclConsts.MATCH][AclConsts.IP]['ecn'] == ecn_show
            assert expected_acl_dict[acl_id][AclConsts.RULE][rule_id_2][AclConsts.MATCH][AclConsts.IP]['ecn'][AclConsts.FLAGS] == ecn_flags_show

    with allure.step("Define ACL to mgmt interface"):
        mgmt_port = MgmtPort()
        mgmt_port.interface.acl.set(acl_id).verify_result()
        mgmt_port.interface.acl.acl_id[acl_id].inbound.set(AclConsts.CONTROL_PLANE, apply=True)

        with allure.step("Validate configuration with show commands"):
            interface_acls_output = mgmt_port.interface.acl.parse_show()
            interface_acl_output = mgmt_port.interface.acl.acl_id[acl_id].parse_show()
            statistics_output = mgmt_port.interface.acl.acl_id[acl_id].statistics.parse_show()
            rule_statistics_output = mgmt_port.interface.acl.acl_id[acl_id].statistics.parse_show(rule_id_1)
            inbound_output = mgmt_port.interface.acl.acl_id[acl_id].inbound.parse_show(AclConsts.CONTROL_PLANE)
            assert acl_output[acl_id][AclConsts.RULE].keys() == interface_acls_output[acl_id][AclConsts.STATISTICS].keys()
            assert rule_output.keys() == interface_acl_output[AclConsts.STATISTICS].keys()
            assert rule_output.keys() == statistics_output.keys()
            assert statistics_output[rule_id_1].keys() == rule_statistics_output.keys()
            assert rule_output.keys() == inbound_output[AclConsts.STATISTICS].keys()


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_inbound_outbound_counters(engines, test_api):
    """
    Validate inbound outbound counters.
    rule match ip dest-ip - should increase outbound counters only
    rule match ip source-ip - should increase inbound counters only
    steps:
    1. config inbound and outbound ACLs with match dest-ip rule
    2. validate outbound counters increased only
    3. config inbound and outbound ACLs with match source-ip rule
    4. validate inbound counters increased only
    5. unset source-ip rule from inbound acl
    6. validate outbound counters are still 0
    """
    TestToolkit.tested_api = test_api
    with allure.step("Config inbound and outbound ACLs with match dest-ip rule"):
        acl_type = 'ipv4'
        mgmt_port = MgmtPort()
        control_plane = random.choice([AclConsts.CONTROL_PLANE, ""])
        sonic_mgmt_ip = engines.sonic_mgmt.ip

        rule_id_match_dest_ip = '1'
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.DEST_IP: sonic_mgmt_ip,
                                   AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}

        acl_id_inbound_match_dest_ip = "TEST_A_ACL_INBOUND_MATCH_DEST_IP"
        acl_obj_inbound_match_dest_ip = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_inbound_match_dest_ip,
                                                                                   acl_type, rule_id_match_dest_ip,
                                                                                   rule_configuration_dict, mgmt_port,
                                                                                   AclConsts.INBOUND, control_plane)

        acl_id_outbound_match_dest_ip = "TEST_B_ACL_OUTBOUND_MATCH_DEST_IP"
        acl_obj_outbound_match_dest_ip = config_acl_with_rule_attached_to_interface(engines.dut, acl_id_outbound_match_dest_ip,
                                                                                    acl_type, rule_id_match_dest_ip,
                                                                                    rule_configuration_dict, mgmt_port,
                                                                                    AclConsts.OUTBOUND, control_plane)

    with allure.step("Validate outbound counters increased only"):
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_inbound_match_dest_ip, rule_id_match_dest_ip, rule_direction=AclConsts.INBOUND)
        rule_packets_2_before = get_rule_packets(mgmt_port, acl_id_outbound_match_dest_ip, rule_id_match_dest_ip, rule_direction=AclConsts.OUTBOUND)
        engines.dut.run_cmd('ping {} -c {}'.format(sonic_mgmt_ip, 2))
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_inbound_match_dest_ip, rule_id_match_dest_ip, rule_direction=AclConsts.INBOUND)
        rule_packets_2_after = get_rule_packets(mgmt_port, acl_id_outbound_match_dest_ip, rule_id_match_dest_ip, rule_direction=AclConsts.OUTBOUND)
        assert rule_packets_1_after[rule_id_match_dest_ip] == rule_packets_1_before[rule_id_match_dest_ip], \
            f'The inbound counters of acl {acl_id_inbound_match_dest_ip} rule id {rule_id_match_dest_ip} should be the same cause the rule is matching' \
            f' packets with specific dest ip but it attached to the inbound control plan and not to the outbound.'
        assert rule_packets_2_after[rule_id_match_dest_ip] > rule_packets_2_before[rule_id_match_dest_ip], \
            f'we expect to see increase in acl {acl_id_outbound_match_dest_ip} rule id {rule_id_match_dest_ip} counter after the ping'

    with allure.step("Config inbound and outbound ACLs with match source-ip rule"):
        rule_id_match_src_ip = '2'
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.SOURCE_IP: sonic_mgmt_ip,
                                   AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request'}
        config_rule(engines.dut, acl_obj_inbound_match_dest_ip, rule_id_match_src_ip, rule_configuration_dict)
        config_rule(engines.dut, acl_obj_outbound_match_dest_ip, rule_id_match_src_ip, rule_configuration_dict)

    with allure.step("Validate inbound counters increased only"):
        rule_packets_1_before = get_rule_packets(mgmt_port, acl_id_inbound_match_dest_ip, rule_id_match_src_ip,
                                                 rule_direction=AclConsts.INBOUND)
        rule_packets_2_before = get_rule_packets(mgmt_port, acl_id_outbound_match_dest_ip, rule_id_match_src_ip,
                                                 rule_direction=AclConsts.OUTBOUND)
        ping_packet = IP(dst=engines.dut.ip, src=sonic_mgmt_ip) / ICMP()
        send(ping_packet)
        rule_packets_1_after = get_rule_packets(mgmt_port, acl_id_inbound_match_dest_ip, rule_id_match_src_ip,
                                                rule_direction=AclConsts.INBOUND)
        rule_packets_2_after = get_rule_packets(mgmt_port, acl_id_outbound_match_dest_ip, rule_id_match_src_ip,
                                                rule_direction=AclConsts.OUTBOUND)
        assert rule_packets_1_after[rule_id_match_src_ip] > rule_packets_1_before[rule_id_match_src_ip], \
            f'we expect to see increase in acl {acl_id_inbound_match_dest_ip} rule id {rule_id_match_src_ip} counter after the ping'
        assert rule_packets_2_after[rule_id_match_src_ip] == rule_packets_2_before[rule_id_match_src_ip], \
            f'The outbound counters of acl {acl_id_outbound_match_dest_ip} rule id {rule_id_match_src_ip} should be the same cause the rule is matching' \
            f' packets with specific dest ip but it attached to the inbound control plan and not to the outbound.'
        assert rule_packets_2_after[rule_id_match_src_ip] == '0'

    with allure.step("Unset source-ip rule from inbound acl"):
        acl_obj_inbound_match_dest_ip.rule.rule_id[rule_id_match_src_ip].unset(apply=True)

    with allure.step("Validate outbound counters are still 0"):
        send(ping_packet)
        rule_packets_2_after = get_rule_packets(mgmt_port, acl_id_outbound_match_dest_ip, rule_id_match_src_ip,
                                                rule_direction=AclConsts.OUTBOUND)
        assert rule_packets_2_after[rule_id_match_src_ip] == '0', \
            f'we expect to see increase in acl {acl_id_outbound_match_dest_ip} rule id {rule_id_match_src_ip} counter after the ping'


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_dest_ip(engines, test_api):
    """
    Validate ACL match dest-ip rules.
    steps:
    1. config ACL with a match dest-ip rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort()
    with allure.step("ACL type ipv4 test"):
        ipv4_addr = engines.sonic_mgmt.ip
        dest_ip_list = ['ANY', ipv4_addr, ipv4_addr + '/32', ipv4_addr + '/255.255.255.0']
        dest_ip_test(engines, mgmt_port, 'ipv4', "TEST_ACL_IPV4", dest_ip_list, ipv4_addr)

    with allure.step("ACL type ipv6 test"):
        ipv6_addr = "2001:db8:abcd:0012:0000:0000:0000:00ef"
        dest_ip_list = [ipv6_addr, ipv6_addr + '/64']
        dest_ip_test(engines, mgmt_port, 'ipv6', "TEST_ACL_IPV6", dest_ip_list, ipv6_addr)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_source_port(engines, test_api):
    """
    Validate ACL match source port rules.
    steps:
    1. config ACL with a match source port rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort()
    src_port_list = ['ANY', 'ssh', 1244]
    match_ip_port_test(engines, mgmt_port, 'ipv4', 'TEST_ACL_SOURCE_PORT', src_port_list, engines.dut.ip, AclConsts.SOURCE_PORT)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_dest_port(engines, test_api):
    """
    Validate ACL match dest port rules.
    steps:
    1. config ACL with a match dest port rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort()
    dest_port_list = ['ANY', 'ssh', 1244]
    match_ip_port_test(engines, mgmt_port, 'ipv4', 'TEST_ACL_DEST_PORT', dest_port_list, engines.sonic_mgmt.ip, AclConsts.DEST_PORT)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_protocol(engines, test_api):
    """
    Validate ACL match protocol rules.
    steps:
    1. config ACL with a match protocol rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_PROTOCOL"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    protocol_packet_dict = {'tcp': f"IP(dst=\"{dest_addr}\") / TCP()",
                            'udp': f"IP(dst=\"{dest_addr}\") / UDP()",
                            'icmp': f"IP(dst=\"{dest_addr}\") / ICMP()"}
    rule_id = str(len(protocol_packet_dict))
    acl_obj = None

    for protocol, packet in protocol_packet_dict.items():
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: protocol}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)
        rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_fragment(engines, test_api):
    """
    Validate ACL match fragment rules.
    steps:
    1. config ACL with a match fragment rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_FRAGMENT"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    packet = f"IP(dst=\"{dest_addr}\") /  ICMP() / (\"X\" * (8000))"
    rule_id = '3'
    rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: 'icmp', AclConsts.FRAGMENT: AclConsts.FRAGMENT}
    config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id, rule_configuration_dict, mgmt_port,
                                               AclConsts.INBOUND, control_plane='')
    validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr, packet=packet)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_tcp_flag_mask(engines, test_api):
    """
    Validate ACL match tcp flag and mask rules.
    steps:
    1. config ACL with tcp flag and mask rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_TCP_FLAG_MASK"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    flag_packet_dict = {'ack': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"A\")",
                        'fin': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"F\")",
                        'psh': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"P\")",
                        'rst': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"R\")",
                        'syn': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"S\")",
                        'urg': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"U\")",
                        'all': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"SAFRUP\")",
                        'none': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"\")"}

    rule_id = str(len(flag_packet_dict) * 2)
    acl_obj = None

    for flag, packet in flag_packet_dict.items():
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: 'tcp',
                                   AclConsts.TCP_FLAGS: flag, AclConsts.TCP_MASK: flag}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)
        rule_id = str(int(rule_id) - 1)
        if flag not in ['all', 'none']:
            rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: 'tcp',
                                       AclConsts.TCP_FLAGS: flag, AclConsts.TCP_MASK: 'all'}
            acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                                 rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                                 AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
            validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id,
                                            dest_addr, packet=packet)
            rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_ip_state(engines, test_api):
    """
    Validate ACL match ip state rules.
    steps:
    1. config ACL with a match ip state rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_IP_STATE"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    state_packet_dict = {'new': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"S\")",
                         'invalid': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"R\")",
                         'established': f"IP(dst=\"{dest_addr}\") / ICMP()"}
    # 'related': f"IP(dst=\"{dest_addr}\") / ICMP(type=3)"}
    rule_id = str(len(state_packet_dict))
    acl_obj = None

    for state, packet in state_packet_dict.items():
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.TCP_STATE: state, AclConsts.IP_PROTOCOL: 'tcp'}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)
        rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_icmp_type(engines, test_api):
    """
    Validate ACL match icmp_type rules.
    steps:
    1. config ACL with a match icmp_type rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_ICMP_TYPE"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    rand_num_type = random.randint(0, 255)
    state_packet_dict = {'echo-reply': f"IP(dst=\"{dest_addr}\") / ICMP(type=\"echo-reply\")",
                         'echo-request': f"IP(dst=\"{dest_addr}\") / ICMP(type=\"echo-request\")",
                         'time-exceeded': f"IP(dst=\"{dest_addr}\") / ICMP(type=\"time-exceeded\")",
                         'destination-unreachable': f"IP(dst=\"{dest_addr}\") / ICMP(type=3)",
                         'port-unreachable': f"IP(dst=\"{dest_addr}\") / ICMP(type=3, code=3)",
                         rand_num_type: f"IP(dst=\"{dest_addr}\") / ICMP(type={rand_num_type})"}
    rule_id = str(len(state_packet_dict))
    acl_obj = None

    for icmp_type, packet in state_packet_dict.items():
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.ICMP_TYPE: icmp_type, AclConsts.IP_PROTOCOL: 'icmp'}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)
        rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_icmpv6_type(engines, test_api):
    """
    Validate ACL match icmpv6_type rules.
    steps:
    1. config ACL with a match icmpv6_type rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_ICMPV6_TYPE"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    icmpv6_type_packet_dict = {'router-solicitation': f"IP(dst=\"{dest_addr}\") / ICMPv6ND_RS()",
                               'router-advertisement': f"IP(dst=\"{dest_addr}\") / ICMPv6ND_RA()"}
    # 'neighbor-solicitation': f"IP(dst=\"{dest_addr}\") / ICMPv6ND_NS()",
    # 'neighbor-advertisement': f"IP(dst=\"{dest_addr}\") / ICMPv6ND_NA()"}
    rule_id = str(len(icmpv6_type_packet_dict))
    acl_obj = None

    for icmpv6_type, packet in icmpv6_type_packet_dict.items():
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.ICMPV6_TYPE: icmpv6_type, AclConsts.IP_PROTOCOL: 'icmpv6'}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv6', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)
        rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_tcpmss(engines, test_api):
    """
    Validate ACL match ip tcpmss rules.
    steps:
    1. config ACL with a match ip tcpmss rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_TCPMSS"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    rand_tcpmss = str(random.randint(1500, 2500))
    packet = f"IP(dst=\"{dest_addr}\") / TCP(options=[('MSS', {rand_tcpmss})])"
    rule_id = str(random.randint(2, 10))

    with allure.step("tcpmss rules"):
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.TCPMSS: rand_tcpmss, AclConsts.IP_PROTOCOL: 'tcp'}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)

    with allure.step("all-tcpmss-except rules"):
        rule_id = str(int(rule_id) - 1)
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.ALL_TCPMSS_EXCEPT: rand_tcpmss, AclConsts.IP_PROTOCOL: 'tcp'}
        config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id, rule_configuration_dict,
                                                   mgmt_port, AclConsts.INBOUND, AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                        packet=packet)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_match_ecn(engines, test_api):
    """
    Validate ACL match ecn rules.
    steps:
    1. config ACL with a match ecn rule
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_ECN"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    ecn_flags_dict = {'tcp-cwr': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"C\")",
                      'tcp-ece': f"IP(dst=\"{dest_addr}\") / TCP(flags=\"E\")"}
    ecn_ip_ect_dict = {0: f"IP(dst=\"{dest_addr}\", tos=0) / TCP(dport=80)",
                       1: f"IP(dst=\"{dest_addr}\", tos=1) / TCP(dport=80)",
                       2: f"IP(dst=\"{dest_addr}\", tos=2) / TCP(dport=80)"}
    # 3: f"IP(dst=\"{dest_addr}\", tos=3) / TCP(dport=80)"}
    rule_id = str(len(ecn_flags_dict) + len(ecn_ip_ect_dict))
    acl_obj = None

    with allure.step("ecn flags rules"):
        for ecn_flag, packet in ecn_flags_dict.items():
            rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.ECN_FLAGS: ecn_flag, AclConsts.IP_PROTOCOL: 'tcp'}
            acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                                 rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                                 AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
            validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                            packet=packet)
            rule_id = str(int(rule_id) - 1)

    with allure.step("ecn ip-ect rules"):
        for ip_ect, packet in ecn_ip_ect_dict.items():
            rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.ECN_IP_ECT: ip_ect, AclConsts.IP_PROTOCOL: 'tcp'}
            acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id,
                                                                 rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                                 AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
            validate_counters_after_traffic(engines.sonic_mgmt, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr,
                                            packet=packet)
            rule_id = str(int(rule_id) - 1)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_hashlimit(engines, test_api):
    """
    Validate ACL match hashlimit rules.
    steps:
    1. config ACL with 2 rule hashlimit rules
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_HASH_LIMIT"
    mgmt_port = MgmtPort()
    dest_addr = engines.sonic_mgmt.ip
    rule_id = '1'
    rand_burst = random.randint(1, 10)

    with allure.step("configurations"):
        rule_1_configuration_dict = {AclConsts.ACTION: AclConsts.DENY, AclConsts.DEST_IP: dest_addr,
                                     AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request',
                                     AclConsts.HASHLIMIT_NAME: 'one_per_min', AclConsts.HASHLIMIT_RATE: '1/min',
                                     AclConsts.HASHLIMIT_BURST: rand_burst, AclConsts.HASHLIMIT_MODE: 'src-ip',
                                     AclConsts.HASHLIMIT_EXPIRE: 50000}
        config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', rule_id, rule_1_configuration_dict,
                                                   mgmt_port, AclConsts.OUTBOUND)
        with allure.step(f"Validate counters increased"):
            rule_packets_before = get_rule_packets(mgmt_port, acl_id, rule_id, rule_direction=AclConsts.OUTBOUND)
            packets_amount = 3 * rand_burst
            engines.dut.run_cmd('ping {} -c {} -i 0.2'.format(dest_addr, packets_amount))
            rule_packets_after = get_rule_packets(mgmt_port, acl_id, rule_id, rule_direction=AclConsts.OUTBOUND)
            assert int(rule_packets_after[rule_id]) - int(rule_packets_before[rule_id]) >= (packets_amount - rand_burst - 1), \
                "expect to see difference in the counters after the ping"


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_acl_recent_list(engines, test_api):
    """
    Validate ACL match recent-list rules.
    steps:
    1. config ACL with 2 recent-list rules
    2. send packet
    3. validate counter increased
    """
    TestToolkit.tested_api = test_api
    acl_id = "TEST_ACL_RECENT_LIST"
    mgmt_port = MgmtPort()
    dest_addr = engines.dut.ip
    src_ip = engines.sonic_mgmt.ip
    set_rule_id = '1'
    update_rule_id = '2'
    recent_list_name = 'ip_list'
    update_interval = random.randint(5, 10)
    hit_count = random.randint(3, 10)

    with allure.step("configurations"):
        rule_1_configuration_dict = {AclConsts.SOURCE_IP: src_ip, AclConsts.RECENT_LIST_NAME: recent_list_name,
                                     AclConsts.RECENT_LIST_ACTION: 'set', AclConsts.IP_PROTOCOL: 'icmp',
                                     AclConsts.ICMP_TYPE: 'echo-request'}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, 'ipv4', set_rule_id, rule_1_configuration_dict,
                                                             mgmt_port, AclConsts.INBOUND)
        rule_2_configuration_dict = {AclConsts.ACTION: AclConsts.DENY, AclConsts.SOURCE_IP: src_ip,
                                     AclConsts.IP_PROTOCOL: 'icmp', AclConsts.ICMP_TYPE: 'echo-request',
                                     AclConsts.RECENT_LIST_NAME: recent_list_name, AclConsts.RECENT_LIST_ACTION: 'update',
                                     AclConsts.RECENT_LIST_UPDATE: update_interval, AclConsts.RECENT_LIST_HIT: hit_count}
        config_rule(engines.dut, acl_obj, update_rule_id, rule_2_configuration_dict)

    with allure.step("Validate the second rule will not match cause it will be less packets than the hit-count"):
        amount_of_packet = hit_count - 2
        engines.sonic_mgmt.run_cmd_set(['ping {} -c {} -i 0.1'.format(dest_addr, amount_of_packet), "\x03"])
        rule_packets_after = get_rule_packets(mgmt_port, acl_id)
        assert amount_of_packet == int(rule_packets_after[set_rule_id])
        assert 0 == int(rule_packets_after[update_rule_id])

        with allure.step(f"wait {update_interval} sec as the update interval value"):
            time.sleep(update_interval)

    with allure.step("Validate the second rule will match cause it will be the same amount of packets as the hit-count"):
        amount_of_packet1 = 2 * hit_count + 2
        engines.sonic_mgmt.run_cmd_set(['ping {} -c {} -i 0.1'.format(dest_addr, amount_of_packet1), "\x03"])
        rule_packets_after = get_rule_packets(mgmt_port, acl_id)
        assert amount_of_packet + amount_of_packet1 == int(rule_packets_after[set_rule_id]), "expect to see all the sent packets in the counters of the set rule after ping"
        assert hit_count <= int(rule_packets_after[update_rule_id]), f"expect to see just {hit_count} packets in the counters of the update rule after ping"

    with allure.step("unset the second rule and validate packets received since it should delete the ip from the list"):
        acl_obj.rule.rule_id[update_rule_id].unset(apply=True)
        amount_of_packet = hit_count
        output = engines.sonic_mgmt.run_cmd_set(['ping {} -c {} -i 0.1'.format(dest_addr, amount_of_packet), "\x03"])
        rule_packets_after3 = get_rule_packets(mgmt_port, acl_id)
        assert 4 * hit_count == int(rule_packets_after3[set_rule_id]), "expect to see all the sent packets in the counters of the set rule after ping"
        assert '0% packet loss' in output, "expect ping to pass after removing the update rule"


def get_rule_packets(mgmt_port, acl_id, rule_id=None, rule_direction=AclConsts.INBOUND):
    output = mgmt_port.interface.acl.acl_id[acl_id].parse_show()
    res = {}
    if rule_id:
        res[rule_id] = output[AclConsts.STATISTICS][rule_id][rule_direction]["packet"]
    else:
        for rule_id, rule_obj in output[AclConsts.STATISTICS].items():
            res[rule_id] = rule_obj[rule_direction]["packet"]
    return res


def config_rule(engine, acl_id_obj, rule_id, rule_config_dict):
    with allure.step(f"Config rule {rule_id}"):
        acl_id_obj.rule.set(rule_id).verify_result()
        rule_id_obj = acl_id_obj.rule.rule_id[rule_id]

        for key, value in rule_config_dict.items():
            RULE_CONFIG_FUNCTION[key](rule_id_obj, value).verify_result()

        result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engine)
        return result_obj


def config_acl_with_rule_attached_to_interface(engine, acl_id, acl_type, rule_id, rule_configuration_dict, mgmt_port,
                                               rule_direction, control_plane=AclConsts.CONTROL_PLANE, acl_obj=None):
    with allure.step(f"config acl {acl_id} with rule {rule_id} attached to interface {mgmt_port.name}"):
        if acl_obj:
            config_rule(engine, acl_obj, rule_id, rule_configuration_dict)
        else:
            acl = Acl()
            acl.set(acl_id).verify_result()
            acl_obj = acl.acl_id[acl_id]
            acl_obj.set(AclConsts.TYPE, acl_type).verify_result()
            config_rule(engine, acl_obj, rule_id, rule_configuration_dict)
            attach_acl_to_interface(acl_id, mgmt_port, rule_direction, control_plane)
        return acl_obj


def attach_acl_to_interface(acl_id, mgmt_port, rule_direction, control_plane=AclConsts.CONTROL_PLANE):
    with allure.step(f"Attach acl {acl_id} to interface {mgmt_port.name}"):
        mgmt_port.interface.acl.set(acl_id).verify_result()
        if rule_direction == AclConsts.INBOUND:
            mgmt_port.interface.acl.acl_id[acl_id].inbound.set(control_plane, apply=True)
        elif rule_direction == AclConsts.OUTBOUND:
            mgmt_port.interface.acl.acl_id[acl_id].outbound.set(control_plane, apply=True)


def validate_counters_after_traffic(engine, rule_direction, mgmt_port, acl_id, rule_id, ping_dest=None, packet=None):
    with allure.step(f"Validate {rule_direction} counters increased"):
        rule_packets_before = get_rule_packets(mgmt_port, acl_id, rule_id, rule_direction=rule_direction)
        if packet:
            scapy_send_packet(engine, packet)
        elif ping_dest:
            engine.run_cmd('ping {} -c {}'.format(ping_dest, 2))
        rule_packets_after = get_rule_packets(mgmt_port, acl_id, rule_id, rule_direction=rule_direction)
        assert int(rule_packets_after[rule_id]) > int(rule_packets_before[rule_id]), \
            "expect to see difference in the counters after the ping"


def dest_ip_test(engines, mgmt_port, acl_type, acl_id, dest_ip_list, ping_dest):
    with allure.step(f"Define ACL {acl_id} type {acl_type}"):
        rule_id = str(len(dest_ip_list))
        acl_obj = None

    for dest_ip in dest_ip_list:
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.DEST_IP: dest_ip}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, acl_type, rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.OUTBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        validate_counters_after_traffic(engines.dut, AclConsts.OUTBOUND, mgmt_port, acl_id, rule_id, ping_dest=ping_dest)
        rule_id = str(int(rule_id) - 1)


def scapy_send_packet(engine, packet):
    cmd_set = ["sudo scapy", f"send({packet})", "exit()"]
    return engine.run_cmd_set(cmd_set, validate=False, patterns_list=[">>>"])


def match_ip_port_test(engines, mgmt_port, acl_type, acl_id, port_list, dest_addr, port_direction=AclConsts.DEST_PORT):
    rule_id = str(len(port_list))
    engine_send_packet = engines.dut if port_direction == AclConsts.DEST_PORT else engines.sonic_mgmt
    acl_obj = None

    for port in port_list:
        rule_configuration_dict = {AclConsts.ACTION: AclConsts.PERMIT, AclConsts.IP_PROTOCOL: 'tcp', port_direction: port}
        acl_obj = config_acl_with_rule_attached_to_interface(engines.dut, acl_id, acl_type, rule_id,
                                                             rule_configuration_dict, mgmt_port, AclConsts.INBOUND,
                                                             AclConsts.CONTROL_PLANE, acl_obj=acl_obj)
        if port == 'ANY':
            port = 1234
        port = port if isinstance(port, int) else f"\"{port}\""
        packet = f"IP(dst=\"{dest_addr}\") / TCP(sport={port}, dport={port})"
        validate_counters_after_traffic(engine_send_packet, AclConsts.INBOUND, mgmt_port, acl_id, rule_id, dest_addr, packet=packet)
        rule_id = str(int(rule_id) - 1)
