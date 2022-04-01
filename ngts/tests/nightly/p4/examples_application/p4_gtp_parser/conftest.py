import pytest
import logging
import allure
from ngts.constants.constants import P4ExamplesConsts
from ngts.config_templates.ip_config_template import IpConfigTemplate


logger = logging.getLogger()

ORI_PARAMS = "ori_params"
UPDATE_PARAMS = "update_params"

DUT_HA_1_IP = "44.0.0.1"
DUT_HA_2_IP = "45.0.0.1"
DUT_HB_1_IP = "46.0.0.1"
DUT_HB_2_IP = "47.0.0.1"
HA_DUT_1_IP = "44.0.0.2"
HA_DUT_2_IP = "45.0.0.2"
HB_DUT_1_IP = "46.0.0.2"
HB_DUT_2_IP = "47.0.0.2"


@pytest.fixture(scope='module')
def gtp_table_params(interfaces, engines, topology_obj, cli_objects):
    """
    Fixture used to create the TableParams object which contains some params used in the test cases
    :param interfaces: interfaces fixture
    :param engines : engines fixture object
    :param topology_obj: topology_obj fixture object
    :param cli_objects: cli_objects fixture object
    """
    gtp_parser_table = {}

    gtp_parser_entry_1 = dict()
    key_ip = "10.2.2.2/24"
    key_teid = "10000"

    gtp_parser_entry_1['traffic_inner_src_ip'] = "10.2.2.1"
    gtp_parser_entry_1['traffic_sender'] = "ha"
    gtp_parser_entry_1['traffic_sender_port'] = interfaces.ha_dut_1
    gtp_parser_entry_1['traffic_receiver'] = "hb"
    gtp_parser_entry_1['traffic_receiver_port'] = interfaces.hb_dut_1
    gtp_parser_entry_1['dst_mac_address'] = cli_objects.dut.mac.get_mac_address_for_interface(interfaces.dut_ha_1)

    gtp_parser_entry_1['ori_params'] = {'action': "ROUTE", 'port': interfaces.dut_hb_1, 'priority': '10'}
    gtp_parser_entry_1['update_params'] = {'action': "DROP", 'port': interfaces.dut_hb_2, 'priority': '30'}
    gtp_parser_entry_key = " ".join([key_ip, key_teid])
    gtp_parser_table[gtp_parser_entry_key] = gtp_parser_entry_1

    gtp_parser_entry_pri_2 = dict()
    key_ip = "20.2.2.2/24"
    key_teid = "20000"

    gtp_parser_entry_pri_2['traffic_inner_src_ip'] = "20.2.2.1"
    gtp_parser_entry_pri_2['traffic_sender'] = "hb"
    gtp_parser_entry_pri_2['traffic_sender_port'] = interfaces.hb_dut_1
    gtp_parser_entry_pri_2['traffic_receiver'] = "ha"
    gtp_parser_entry_pri_2['traffic_receiver_port'] = interfaces.ha_dut_1
    gtp_parser_entry_pri_2['dst_mac_address'] = cli_objects.dut.mac.get_mac_address_for_interface(interfaces.dut_hb_1)

    gtp_parser_entry_pri_2['ori_params'] = {'action': "ROUTE", 'port': interfaces.dut_ha_1, 'priority': '10'}
    gtp_parser_entry_pri_2['update_params'] = {'action': "DROP", 'port': interfaces.dut_ha_2, 'priority': '20'}
    gtp_parser_entry_key = " ".join([key_ip, key_teid])
    gtp_parser_table[gtp_parser_entry_key] = gtp_parser_entry_pri_2

    gtp_parser_entry_pri_3 = gtp_parser_entry_pri_2.copy()
    key_ip = "20.2.2.2/32"
    key_teid = "20000"

    gtp_parser_entry_pri_3['traffic_receiver'] = "ha"
    gtp_parser_entry_pri_3['traffic_receiver_port'] = interfaces.ha_dut_2

    gtp_parser_entry_pri_3['ori_params'] = {'action': "ROUTE", 'port': interfaces.dut_ha_2, 'priority': '5'}
    gtp_parser_entry_pri_3['update_params'] = {'action': "ROUTE", 'port': interfaces.dut_ha_1, 'priority': '10'}
    gtp_parser_entry_key = " ".join([key_ip, key_teid])
    gtp_parser_table[gtp_parser_entry_key] = gtp_parser_entry_pri_3

    yield gtp_parser_table


@pytest.fixture(scope='module')
def gtp_entry_mismatch_params(interfaces, engines, topology_obj):
    mismatch_traffic_params = dict()
    mismatch_traffic_params["outer_src_ip"] = HA_DUT_1_IP
    mismatch_traffic_params["outer_dst_ip"] = HB_DUT_1_IP
    mismatch_traffic_params["traffic_sender"] = "ha"
    mismatch_traffic_params["traffic_sender_port"] = interfaces.ha_dut_1
    mismatch_traffic_params["traffic_receiver"] = "hb"
    mismatch_traffic_params["traffic_receiver_port"] = interfaces.hb_dut_1
    yield mismatch_traffic_params


@pytest.fixture(scope='module', autouse=True)
def p4_gtp_configuration(topology_obj, engines, interfaces):
    """
    Pytest fixture which are doing configuration for P4 gtp parser test cases
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    """

    ip_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'ips': [(DUT_HA_1_IP, '24')]},
                {'iface': interfaces.dut_ha_2, 'ips': [(DUT_HA_2_IP, '24')]},
                {'iface': interfaces.dut_hb_1, 'ips': [(DUT_HB_1_IP, '24')]},
                {'iface': interfaces.dut_hb_2, 'ips': [(DUT_HB_2_IP, '24')]},
                ],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [(HA_DUT_1_IP, '24')]},
               {'iface': interfaces.ha_dut_2, 'ips': [(HA_DUT_2_IP, '24')]}
               ],
        'hb': [{'iface': interfaces.hb_dut_1, 'ips': [(HB_DUT_1_IP, '24')]},
               {'iface': interfaces.hb_dut_2, 'ips': [(HB_DUT_2_IP, '24')]},
               ]
    }

    logger.info('Starting the common configuration for P4 GTP test')
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('The common configuration for P4 GTP test completed')
    yield
    logger.info('Starting the common configuration cleanup for P4 GTP test')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    logger.info('The common configuration cleanup for P4 GTP test completed')


@pytest.fixture(scope='module', autouse=True)
def p4_gtp_entry_configuration(engines, gtp_table_params, cli_objects):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param engines: engines fixture
    :param gtp_table_params: gtp_table_params fixture object
    :param cli_objects: cli_objects fixture
    """
    with allure.step(f"Start feature {P4ExamplesConsts.GTP_PARSER_FEATURE_NAME} in the p4 examples app"):
        cli_objects.dut.p4_examples.start_p4_example_feature(P4ExamplesConsts.GTP_PARSER_FEATURE_NAME)
    with allure.step("Add P4 gtp parser entries"):
        add_gtp_entries(gtp_table_params, cli_objects.dut)
    yield
    logger.info('Starting P4 GTP entries configuration cleanup')
    with allure.step("Delete P4 gtp parser entries"):
        delete_gtp_entries(gtp_table_params, cli_objects.dut)
    with allure.step("Verify the entries deleted correctly"):
        verify_entries_removed(gtp_table_params, cli_objects.dut)
        gtp_entries = cli_objects.dut.p4_gtp.show_and_parse_entries()
        assert len(gtp_entries) == 0, "The gtp entries not cleaned."

    with allure.step(f"Stop feature {P4ExamplesConsts.GTP_PARSER_FEATURE_NAME} in the p4 examples app"):
        cli_objects.dut.p4_examples.stop_p4_example_feature()


def add_gtp_entries(gtp_table_params, cli_obj):
    """
    Add the gtp entries
    :param gtp_table_params: gtp_table_params fixture object.
    :param cli_obj: cli_obj object
    :return: None
    """
    for entry_key, entry_param_dict in gtp_table_params.items():
        entry_params = get_entry_params(entry_param_dict['ori_params'])
        cli_obj.p4_gtp.add_entry(entry_key, entry_params)


def delete_gtp_entries(gtp_table_params, cli_obj):
    """
    Delete the gtp entries
    :param gtp_table_params: gtp_table_params fixture object.
    :param cli_obj: cli_obj object
    :return: None
    """
    for entry_key, entry_param_dict in gtp_table_params.items():
        cli_obj.p4_gtp.delete_entry(entry_key)


def update_gtp_entries(gtp_table_params, cli_obj, params_type=UPDATE_PARAMS):
    """
    Update the params of the gtp entries.
    :param gtp_table_params: gtp_table_params fixture object.
    :param cli_obj: cli_obj object
    :param params_type: ori_params or update_params,
    :return: None
    """
    for entry_key, entry_param_dict in gtp_table_params.items():
        entry_params = get_entry_params(entry_param_dict[params_type])
        cli_obj.p4_gtp.update_entry(entry_key, entry_params)


def get_entry_params(entry_param_dict):
    """
    Get the entry params
    :param entry_param_dict: the entry params in dictionary format
    :return: string of entry params which can be used in cli command
        Example: "-action ROUTE -port Ethernet0 -priority 10"
    """
    entry_param_keys = ['action', 'port', 'priority']
    entry_params = ""
    for entry_param_key in entry_param_keys:
        entry_params += f" --{entry_param_key} {entry_param_dict[entry_param_key]}"
    return entry_params


def verify_entries_removed(entries_expected, cli_obj):
    """
    Verify that the entries have been deleted
    :param entries_expected: entries that expected to be deleted
    :param cli_obj: cli_obj object
    :return: None
    """
    gtp_entries = cli_obj.p4_gtp.show_and_parse_entries()
    for entry_key, entry_params in entries_expected.items():
        assert entry_key not in gtp_entries, f"{entry_key} is not removed"
