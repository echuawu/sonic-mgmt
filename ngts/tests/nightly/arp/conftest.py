import pytest

from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.helpers.arp_helper import INTERFACE_TYPE_LIST, \
    clear_dynamic_arp_table_and_check_the_specified_arp_entry_deleted
from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli


@pytest.fixture(scope='module', autouse=True)
def pre_configure_for_arp(engines, topology_obj, interfaces):
    """
    Pytest fixture which are doing configuration for test case based for arp test
    :param engines: engines object fixture
    :param topology_obj: topology object fixture
    :param interfaces: topology object fixture
    """
    dut_original_interfaces_speeds = SonicInterfaceCli(engine=engines.dut).get_interfaces_speed([interfaces.dut_hb_2])
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_hb_2, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '10G')}
                ]
    }
    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel0002', 'members': [interfaces.dut_hb_2]}],
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.hb_dut_2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 40, 'vlan_members': [{interfaces.dut_ha_2: 'access'},
                                                 {interfaces.dut_hb_1: 'access'}]},
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               ],
        'hb': [{'vlan_id': 40, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               ]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan40', 'ips': [('40.0.0.1', '24')]},
                {'iface': interfaces.dut_ha_1, 'ips': [('30.0.0.1', '24')]},
                {'iface': 'PortChannel0002', 'ips': [('50.0.0.1', '24')]}
                ],
        'hb': [{'iface': interfaces.hb_dut_1, 'ips': [('40.0.0.10', '24')]}]
    }
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)

    yield

    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)


@pytest.fixture(scope='module', autouse=True)
def pre_test_interface_data(engines, interfaces):
    """
    Pytest fixture which are doing configuration for test case based for arp test
    :param engines: engines object fixture
    :param topology_obj: topology object fixture
    :param interfaces: topology object fixture
    """
    test_interface_data = {}
    for interface_type in INTERFACE_TYPE_LIST:
        test_interface_data[interface_type] = gen_test_interface_data(engines, interfaces, interface_type)
    yield test_interface_data


@pytest.fixture(scope='function', autouse=True)
def pre_clear_arp(cli_objects):
    """
    Pytest fixture which is to clear the static arp and  dynamic arp before test
    :param cli_objects: cli_objects fixture
    """
    ip_list = ["40.0.0.2", "30.0.0.2"]
    cli_objects.dut.ip.del_static_neigh()
    for ip in ip_list:
        clear_dynamic_arp_table_and_check_the_specified_arp_entry_deleted(cli_objects.dut, ip)


def gen_test_interface_data(engines, interfaces, interface_type):
    """
    Pytest fixture which is to prepare the interface test data
    :param engines: engines object fixture
    :param interfaces: interfaces object fixture
    :param interface_type:  interface type such as "ethernet", "vlan", "portchannel"
    """
    test_interface_data = {}
    if interface_type == "ethernet":
        test_interface_data["host_ip"] = "30.0.0.2"
        test_interface_data["dut_ip"] = "30.0.0.1"
        test_interface_data["host_interface"] = interfaces.ha_dut_1
        test_interface_data["dut_interface"] = interfaces.dut_ha_1
        test_interface_data["host_mac"] = SonicMacCli(engine=engines.ha).get_mac_address_for_interface(interfaces.ha_dut_1)
        test_interface_data["dut_mac"] = SonicMacCli(engine=engines.dut).get_mac_address_for_interface(interfaces.dut_ha_1)
        test_interface_data["dut_vlan_id"] = "-"
        test_interface_data["host_alias"] = "ha"
    elif interface_type == "vlan":
        test_interface_data["host_ip"] = "40.0.0.2"
        test_interface_data["dut_ip"] = "40.0.0.1"
        test_interface_data["host_interface"] = interfaces.ha_dut_2
        test_interface_data["dut_interface"] = interfaces.dut_ha_2
        test_interface_data["host_mac"] = SonicMacCli(engine=engines.ha).get_mac_address_for_interface(interfaces.ha_dut_2)
        test_interface_data["dut_mac"] = SonicMacCli(engine=engines.dut).get_mac_address_for_interface(interfaces.dut_ha_2)
        test_interface_data["dut_vlan_id"] = "40"
        test_interface_data["host_alias"] = "ha"
    elif interface_type == "portchannel":
        test_interface_data["host_ip"] = "50.0.0.2"
        test_interface_data["dut_ip"] = "50.0.0.1"
        test_interface_data["host_interface"] = "bond0"
        test_interface_data["dut_interface"] = "PortChannel0002"
        test_interface_data["host_mac"] = SonicMacCli(engine=engines.hb).get_mac_address_for_interface("bond0")
        test_interface_data["dut_mac"] = SonicMacCli(engine=engines.dut).get_mac_address_for_interface(interfaces.dut_hb_2)
        test_interface_data["dut_vlan_id"] = "-"
        test_interface_data["host_alias"] = "hb"

    return test_interface_data
