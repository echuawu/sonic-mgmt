"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging
import allure

import ngts.helpers.p4_sampling_fixture_helper as fixture_helper
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.constants.constants import P4SamplingEntryConsts
from ngts.helpers.p4_sampling_utils import P4SamplingUtils, TrafficParams
logger = logging.getLogger()


@pytest.fixture(scope='package', autouse=False)
def install_sampling_pipline(topology_obj):
    """
    This fixture will be used for local debug, change the autouse to True when need to install the p4-sampling in script.
    Fixture used to install the p4-sampling app before run the testcase, and uninstall it after the testcase
    :param topology_obj: topology object fixture
    """
    engine = topology_obj.players['dut']['engine']
    fixture_helper.install_p4_sampling(engine)
    yield
    fixture_helper.uninstall_p4_sampling(engine)


@pytest.fixture(scope="package", autouse=False)
def skipping_p4_sampling_test_case_for_spc1(platform_params):
    """
    If platform is SPC1, skip all testcases except test_p4_sampling_not_support_on_spc1
    :param platform_params: platform_params fixture
    """
    fixture_helper.skipping_p4_sampling_test_case_for_spc1(platform_params)


@pytest.fixture(scope="package", autouse=False)
def skipping_p4_sampling_test_case(cli_objects):
    """
    If p4-sampling is not ready, skipping all p4-sampling test cases execution
    :param cli_objects: cli_objects fixture
    """
    fixture_helper.skipping_p4_sampling_test_case(cli_objects.dut)


@pytest.fixture(scope='package', autouse=True)
def p4_sampling_configuration(skipping_p4_sampling_test_case, topology_obj, engines, interfaces):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param skipping_p4_sampling_test_case: skipping_p4_sampling_test_case object fixture
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :param interfaces: clean_p4_entries fixture
    """

    ip_config_dict = {
        'dut': [{'iface': '{}'.format(interfaces.dut_ha_1), 'ips': [(P4SamplingEntryConsts.dutha1_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_ha_2), 'ips': [(P4SamplingEntryConsts.dutha2_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_hb_1), 'ips': [(P4SamplingEntryConsts.duthb1_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_hb_2), 'ips': [(P4SamplingEntryConsts.duthb2_ip, '24')]}
                ],
        'ha': [{'iface': '{}'.format(interfaces.ha_dut_1), 'ips': [(P4SamplingEntryConsts.hadut1_ip, '24')]},
               {'iface': '{}'.format(interfaces.ha_dut_2), 'ips': [(P4SamplingEntryConsts.hadut2_ip, '24')]}],
        'hb': [{'iface': '{}'.format(interfaces.hb_dut_1), 'ips': [(P4SamplingEntryConsts.hbdut1_ip, '24')]},
               {'iface': '{}'.format(interfaces.hb_dut_2), 'ips': [(P4SamplingEntryConsts.hbdut2_ip, '24')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'ha': [{'dst': '50.0.0.0', 'dst_mask': 24, 'via': [P4SamplingEntryConsts.dutha1_ip]},
               {'dst': '50.0.1.0', 'dst_mask': 24, 'via': [P4SamplingEntryConsts.dutha2_ip]}],
        'hb': [{'dst': '10.0.0.0', 'dst_mask': 24, 'via': [P4SamplingEntryConsts.duthb1_ip]},
               {'dst': '10.0.1.0', 'dst_mask': 24, 'via': [P4SamplingEntryConsts.duthb2_ip]}]
    }

    logger.info('Starting P4 Sampling configuration')
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('P4 Sampling Common configuration completed')
    yield
    logger.info('Starting P4 Sampling configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    logger.info('P4 Sampling cleanup completed')


@pytest.fixture(scope='class', autouse=False)
def p4_sampling_entries(skipping_p4_sampling_test_case_for_spc1, topology_obj, interfaces, engines, cli_objects,
                        table_params):
    """
    Fixture used to add entries and remove entries after test case finish
    :param skipping_p4_sampling_test_case_for_spc1: skipping_p4_sampling_test_case_for_spc1 fixture object
    :param topology_obj: topology_obj fixture object
    :param engines: engines fixture object
    :param cli_objects: cli_objects fixture
    :param interfaces: interfaces fixture object
    :param table_params: table_params fixture object
    """
    fixture_helper.add_p4_sampling_entries(cli_objects.dut, table_params)
    yield
    fixture_helper.remove_p4_sampling_entries(topology_obj, interfaces, engines, table_params)


@pytest.fixture(scope='class')
def table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac):
    """
    Fixture used to create the TableParams object which contains some params used in the testcases
    :param interfaces: interfaces fixture
    :param engines : engines fixture object
    :param topology_obj: topology_obj fixture object
    :param ha_dut_2_mac: ha_dut_2_mac fixture object
    :param hb_dut_1_mac: hb_dut_1_mac fixture object
    """
    return fixture_helper.get_table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac)


@pytest.fixture(scope='class')
def port_traffic_params_list(engines, interfaces, topology_obj, table_params):
    chksum_type = 'match'
    indices = [0]
    port_traffic_params_list = TrafficParams.prepare_port_table_send_receive_traffic_params(interfaces, topology_obj,
                                                                                            table_params.port_entry, indices,
                                                                                            chksum_type)
    return port_traffic_params_list


@pytest.fixture(scope='class')
def flow_traffic_params_list(engines, interfaces, topology_obj, table_params):
    chksum_type = 'match'
    indices = [0]
    _, flow_traffic_params_list = TrafficParams.prepare_flow_table_send_receive_traffic_params(interfaces, topology_obj,
                                                                                               table_params.flow_entry, indices,
                                                                                               chksum_type)
    return flow_traffic_params_list


@pytest.fixture(scope='function')
def start_stop_continuous_traffic(topology_obj, port_traffic_params_list, flow_traffic_params_list):
    with allure.step("Send continuous traffic"):
        port_table_scapy_senders = P4SamplingUtils.start_background_port_table_traffic(topology_obj, port_traffic_params_list)
        flow_table_scapy_senders = P4SamplingUtils.start_background_flow_table_traffic(topology_obj, flow_traffic_params_list)
    yield
    with allure.step("Stop continuous traffic"):
        P4SamplingUtils.stop_background_traffic(port_table_scapy_senders)
        P4SamplingUtils.stop_background_traffic(flow_table_scapy_senders)
