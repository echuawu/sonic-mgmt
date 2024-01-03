import pytest
import itertools

import ngts.helpers.acl_helper as acl_helper
from ngts.helpers.acl_helper import ACLConstants


@pytest.fixture(scope='package')
def acl_table_config_list(engines, interfaces):
    """
    The acl table config list fixture, which will return the list acl tables config params
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    return: list of dictionary,the item of the list include all the information used to created one acl table and
    the acl rules for this table
            example:[{'table_name': 'DATA_INGRESS_L3TEST',
                    'table_ports': ['Ethernet236'],
                    'table_stage': 'ingress',
                    'table_type': 'L3',
                    'rules_template_file': 'acl_rules_ipv4.j2',
                    'rules_template_file_args': {
                            'acl_table_name': 'DATA_INGRESS_L3TEST',
                            'ether_type': '2048',
                            'forward_src_ip_match':
                            '10.0.1.2/32',
                            'forward_dst_ip_match': '121.0.0.2/32',
                            'drop_src_ip_match': '10.0.1.6/32',
                            'drop_dst_ip_match': '123.0.0.2/32',
                            'unmatch_dst_ip': '125.0.0.2/32',
                            'unused_src_ip': '10.0.1.11/32',
                            'unused_dst_ip': '192.168.0.1/32'}}, ...]
    """
    ip_version_list = ACLConstants.IP_VERSION_LIST
    stage_list = ACLConstants.STAGE_LIST
    port_list = [interfaces.dut_ha_2]
    acl_table_config_list = []
    for ip_version, stage in itertools.product(ip_version_list, stage_list):
        acl_table_config_list.append(acl_helper.generate_acl_table_config(stage, ip_version, port_list))

    yield acl_table_config_list


@pytest.fixture(scope='package')
def acl_base_configuration(cli_objects, engines, acl_table_config_list):
    """
    Configure base configuration for basic acl test
    """
    acl_helper.add_acl_table(cli_objects.dut, acl_table_config_list)
    acl_helper.add_acl_rules(engines.dut, cli_objects.dut, acl_table_config_list)
    yield
    acl_helper.clear_acl_rules(engines.dut, cli_objects.dut)
    acl_helper.remove_acl_table(cli_objects.dut, acl_table_config_list)
