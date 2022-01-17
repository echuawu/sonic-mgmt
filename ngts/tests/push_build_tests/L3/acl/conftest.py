import pytest
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
import ngts.helpers.acl_helper as acl_helper


@pytest.fixture(scope='package', autouse=True)
def acl_configuration(topology_obj, interfaces, acl_table_config_list, engines):
    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 120, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 121, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]},
                {'vlan_id': 122, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 123, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]},
                {'vlan_id': 124, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 125, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]}
                ],
        'ha': [{'vlan_id': 120, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 122, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 124, 'vlan_members': [{interfaces.ha_dut_2: None}]}
               ],
        'hb': [{'vlan_id': 121, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               {'vlan_id': 123, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               {'vlan_id': 125, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               ]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan120', 'ips': [('120.0.0.1', '24'), ('7000:120::1', '64')]},
                {'iface': 'Vlan121', 'ips': [('121.0.0.1', '24'), ('7000:121::1', '64')]},
                {'iface': 'Vlan122', 'ips': [('122.0.0.1', '24'), ('7000:122::1', '64')]},
                {'iface': 'Vlan123', 'ips': [('123.0.0.1', '24'), ('7000:123::1', '64')]},
                {'iface': 'Vlan124', 'ips': [('124.0.0.1', '24'), ('7000:124::1', '64')]},
                {'iface': 'Vlan125', 'ips': [('125.0.0.1', '24'), ('7000:125::1', '64')]}
                ],
        'ha': [{'iface': '{}.120'.format(interfaces.ha_dut_2), 'ips': [('120.0.0.2', '24'), ('7000:120::2', '64')]},
               {'iface': '{}.122'.format(interfaces.ha_dut_2), 'ips': [('122.0.0.2', '24'), ('7000:122::2', '64')]},
               {'iface': '{}.124'.format(interfaces.ha_dut_2), 'ips': [('124.0.0.2', '24'), ('7000:124::2', '64')]}
               ],
        'hb': [{'iface': '{}.121'.format(interfaces.hb_dut_1), 'ips': [('121.0.0.2', '24'), ('7000:121::2', '64')]},
               {'iface': '{}.123'.format(interfaces.hb_dut_1), 'ips': [('123.0.0.2', '24'), ('7000:123::2', '64')]},
               {'iface': '{}.125'.format(interfaces.hb_dut_1), 'ips': [('125.0.0.2', '24'), ('7000:125::2', '64')]}
               ]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'ha': [{'dst': '121.0.0.0', 'dst_mask': 24, 'via': ['120.0.0.1']},
               {'dst': '123.0.0.0', 'dst_mask': 24, 'via': ['122.0.0.1']},
               {'dst': '125.0.0.0', 'dst_mask': 24, 'via': ['124.0.0.1']},
               {'dst': '7000:121::0', 'dst_mask': 64, 'via': ['7000:120::1'], 'ip_version': 'ipv6'},
               {'dst': '7000:123::0', 'dst_mask': 64, 'via': ['7000:122::1'], 'ip_version': 'ipv6'},
               {'dst': '7000:125::0', 'dst_mask': 64, 'via': ['7000:124::1'], 'ip_version': 'ipv6'}
               ],
        'hb': [{'dst': '120.0.0.0', 'dst_mask': 24, 'via': ['121.0.0.1']},
               {'dst': '122.0.0.0', 'dst_mask': 24, 'via': ['123.0.0.1']},
               {'dst': '124.0.0.0', 'dst_mask': 24, 'via': ['125.0.0.1']},
               {'dst': '7000:120::0', 'dst_mask': 64, 'via': ['7000:121::1'], 'ip_version': 'ipv6'},
               {'dst': '7000:122::0', 'dst_mask': 64, 'via': ['7000:123::1'], 'ip_version': 'ipv6'},
               {'dst': '7000:124::0', 'dst_mask': 64, 'via': ['7000:125::1'], 'ip_version': 'ipv6'}]
    }

    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    ping_from_host(engines)
    acl_helper.add_acl_table(engines.dut, acl_table_config_list)
    acl_helper.add_acl_rules(engines.dut, acl_table_config_list)
    yield
    acl_helper.clear_acl_rules(engines.dut)
    acl_helper.remove_acl_table(engines.dut, acl_table_config_list)
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)


def ping_from_host(engines):
    """
    Do ping from the host to the DUT interface to make the ip address on the host can be learnt add added to
    the ACL table. Else, the egress test will always have some pkt lost, For detail info can refer to
    [SONiC  Verification] Bug SW #2921562: [Functional] [ACL] | ACL egress rule can not hit all the pkts which
    match the rule. | Assignee: Nana He | Status: Assigned

    :param engines: engines fixture object
    :return: None
    """
    ip_list_ping_from_ha = ["120.0.0.1", "122.0.0.1", "124.0.0.1", "7000:120::1", "7000:122::1", "7000:124::1"]
    ip_list_ping_from_hb = ["121.0.0.1", "123.0.0.1", "125.0.0.1", "7000:121::1", "7000:123::1", "7000:124::1"]
    for ip in ip_list_ping_from_ha:
        engines.ha.run_cmd(f"ping {ip} -c 1")
    for ip in ip_list_ping_from_hb:
        engines.hb.run_cmd(f"ping {ip} -c 1")
