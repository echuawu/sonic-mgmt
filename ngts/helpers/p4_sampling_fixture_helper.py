import pytest
import logging
import allure
import time
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.constants.constants import P4SamplingConsts
from ngts.constants.constants import P4SamplingEntryConsts
from ngts.cli_wrappers.sonic.sonic_p4_sampling_clis import P4SamplingCli
from ngts.helpers.p4_sampling_utils import P4SamplingUtils
from dotted_dict import DottedDict
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli

logger = logging.getLogger()
SPEED = '10G'
APP_NAME = P4SamplingConsts.APP_NAME
PORT_TABLE_NAME = P4SamplingConsts.PORT_TABLE_NAME
FLOW_TABLE_NAME = P4SamplingConsts.FLOW_TABLE_NAME
ACTION_NAME = P4SamplingConsts.ACTION_NAME


def is_p4_sampling_supported(platform_params):
    """
    If platform is SPC1,p4-sampling dose not support
    :param platform_params: platform_params fixture
    :return: True is supported, else False
    """
    return 'SN2' not in platform_params.hwsku


def skipping_p4_sampling_test_case_for_spc1(platform_params):
    """
    If platform is SPC1, skip all test cases except test_p4_sampling_not_support_on_spc1
    :param platform_params: platform_params fixture
    """
    if not is_p4_sampling_supported(platform_params):
        pytest.skip("Skipping p4-sampling test cases as SPC1 does not support it")


def skipping_p4_sampling_test_case(engine_dut):
    """
    If p4-sampling is not ready, skipping all p4-sampling test cases execution
    :param engine_dut: dut ssh engine
    """
    if not P4SamplingUtils.check_p4_sampling_installed(engine_dut):
        pytest.skip("Skipping p4-sampling test cases as p4-sampling is not installed.")


def install_p4_sampling(engine_dut):
    """
    install p4-sampling app
    :param engine_dut: dut ssh engine object
    :return: None
    """
    with allure.step('Check if the repository of the {} added and if it is Installed '.format(APP_NAME)):
        app_list = SonicAppExtensionCli.parse_app_package_list_dict(engine_dut)
        if APP_NAME in app_list:
            app_data = app_list[APP_NAME]
            app_status = app_data['Status']
            if app_status == 'Installed':
                with allure.step('Disable {}'.format(APP_NAME)):
                    SonicGeneralCli().set_feature_state(
                        engine_dut, APP_NAME, 'disabled')
                with allure.step('Uninstall {}'.format(APP_NAME)):
                    SonicAppExtensionCli.uninstall_app(engine_dut, APP_NAME)
            with allure.step('Remove {} app from {} Repository'.format(APP_NAME, P4SamplingConsts.REPOSITORY)):
                SonicAppExtensionCli.remove_repository(engine_dut, APP_NAME)

    with allure.step('Add {} app to {} Repository'.format(APP_NAME, P4SamplingConsts.REPOSITORY)):
        SonicAppExtensionCli.add_repository(engine_dut, APP_NAME, P4SamplingConsts.REPOSITORY)
    with allure.step('Install {} with version {}'.format(APP_NAME, P4SamplingConsts.VERSION)):
        SonicAppExtensionCli.install_app(engine_dut, APP_NAME, P4SamplingConsts.VERSION)
    with allure.step('Enable {}'.format(APP_NAME)):
        SonicGeneralCli().set_feature_state(engine_dut, APP_NAME, 'enabled')

    # TODO: after the bug 2684913 is fixed, need to remove the sleep
    time.sleep(10)
    logger.info('{} installation completed'.format(APP_NAME))


def uninstall_p4_sampling(engine_dut):
    """
    uninstall p4-sampling app
    :param engine_dut: dut ssh engine object
    :return: None
    """
    with allure.step('Disable {}'.format(APP_NAME)):
        SonicGeneralCli().set_feature_state(engine_dut, APP_NAME, 'disabled')
    with allure.step('Uninstall {}'.format(APP_NAME)):
        SonicAppExtensionCli.uninstall_app(engine_dut, APP_NAME)
    with allure.step('Remove {} app from {} Repository'.format(APP_NAME, P4SamplingConsts.REPOSITORY)):
        SonicAppExtensionCli.remove_repository(engine_dut, APP_NAME)
    with allure.step('Verify the app is uninstalled'):
        app_list = SonicAppExtensionCli.parse_app_package_list_dict(engine_dut)
        assert APP_NAME not in app_list
    logger.info('{} uninstallation completed'.format(APP_NAME))
    logger.info("Check the sdk acl value after the p4-sampling is installed")
    logger.info(engine_dut.run_cmd("docker exec -i syncd bash -c 'sx_api_flex_acl_dump.py'"))


def clean_p4_sampling_entries(engines):
    """
    clean the p4 sampling entries
    :param engines: engines fixture object
    :return: port entries and flow entries that have been removed.
    """
    SonicAppExtensionCli.enable_app(engines.dut, APP_NAME)
    with allure.step('Get existing entries'):
        port_entries = P4SamplingCli.show_and_parse_table_entries(engines.dut, PORT_TABLE_NAME, exclude_keys=['rule'])
        flow_entries = P4SamplingCli.show_and_parse_table_entries(engines.dut, FLOW_TABLE_NAME, exclude_keys=['rule'])

    with allure.step('Remove the entries'):
        for port_entry in port_entries:
            P4SamplingCli.delete_entry_from_table(engines.dut, PORT_TABLE_NAME, 'key {}'.format(port_entry['key']))
        for flow_entry in flow_entries:
            P4SamplingCli.delete_entry_from_table(engines.dut, FLOW_TABLE_NAME, 'key {}'.format(flow_entry['key']))
    return port_entries, flow_entries


def recover_p4_sampling_entries(engines, port_entries, flow_entries):
    """
    recover the p4 sampling entries that have been removed
    :param engines: engines fixture object
    :param port_entries: port entry list which need to be add back
    :param flow_entries:  flow etry list which need to be add back
    :return: None
    """
    with allure.step('Add the entries back'):
        for port_entry in port_entries:
            port_table_entry_params = 'key {} action {} {} priority {}'.format(port_entry.key, ACTION_NAME,
                                                                               port_entry.action, port_entry.priority)
            P4SamplingCli.add_entry_to_table(engines.dut, PORT_TABLE_NAME, port_table_entry_params)
        for flow_entry in flow_entries:
            flow_table_entry_params = 'key {} action {} {} priority {}'.format(flow_entry.key, ACTION_NAME,
                                                                               flow_entry.action,
                                                                               flow_entry.priority)
            P4SamplingCli.add_entry_to_table(engines.dut, PORT_TABLE_NAME, flow_table_entry_params)


def add_p4_sampling_entries(engines, table_params):
    """
    Add p4 sampling entries with entry params defined in table_params
    :param engines: engines fixture object
    :param table_params: table_params fixture object
    """
    SonicAppExtensionCli.enable_app(engines.dut, APP_NAME)

    port_entry = table_params.port_entry
    with allure.step('Add {} entries for {}'.format(len(port_entry.keys()), PORT_TABLE_NAME)):
        for key in port_entry.keys():
            params = port_entry[key]
            port_table_entry_params = 'key {} action {} {} priority {}'.format(key, ACTION_NAME, params.action,
                                                                               params.priority)
            P4SamplingCli.add_entry_to_table(
                engines.dut, PORT_TABLE_NAME, port_table_entry_params)
    flow_entry = table_params.flow_entry
    with allure.step('Add {} entries for {}'.format(len(flow_entry.keys()), FLOW_TABLE_NAME)):
        for key in flow_entry.keys():
            params = flow_entry[key]
            flow_table_entry_params = 'key {} action {} {} priority {}'.format(
                key, ACTION_NAME, params.action, params.priority)
            P4SamplingCli.add_entry_to_table(
                engines.dut, FLOW_TABLE_NAME, flow_table_entry_params)


def remove_p4_sampling_entries(topology_obj, interfaces, engines, table_params):
    """
    remove the p4 sampling entries.
    :param topology_obj: topology_obj fixture object
    :param interfaces: interfaces fixture object
    :param engines: engines fixture object
    :param table_params: table_params fixture object
    :return: None
    """
    port_entry = table_params.port_entry
    flow_entry = table_params.flow_entry
    with allure.step('Remove {} entries for {}'.format(len(port_entry.keys()), PORT_TABLE_NAME)):
        for port_entry_key in table_params.port_entry.keys():
            P4SamplingCli.delete_entry_from_table(
                engines.dut, PORT_TABLE_NAME, 'key {}'.format(port_entry_key))
    with allure.step('Remove {} entries for {}'.format(len(flow_entry.keys()), FLOW_TABLE_NAME)):
        for flow_entry_key in table_params.flow_entry.keys():
            P4SamplingCli.delete_entry_from_table(
                engines.dut, FLOW_TABLE_NAME, 'key {}'.format(flow_entry_key))

    with allure.step(
            'Verify entries count in table {} and {} after the added entries are removed'.format(
                PORT_TABLE_NAME, FLOW_TABLE_NAME)):
        P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.flow_entry, False)
        P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, False)
    with allure.step('Send traffic after the entries are removed'):
        count = 50
        P4SamplingUtils.verify_traffic_miss(
            topology_obj,
            engines,
            interfaces,
            table_params,
            count, 0)


def get_table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac):
    """
    Fixture used to create the TableParams object which contains some params used in the testcases
    :param interfaces: interfaces fixture
    :param:engines : engines fixture object
    :param: topology_obj: topology_obj fixture object
    :param ha_dut_2_mac: ha_dut_2_mac fixture object
    :param hb_dut_1_mac: hb_dut_1_mac fixture object
    """
    table_param_data = DottedDict()
    chksum_value = '0x0001'
    chksum_value1 = '0x0100'
    chksum_mask = '0xffff'
    port_entry_key_list = ['{} {}/{}'.format(interfaces.dut_ha_2, chksum_value, chksum_mask),
                           '{} {}/{}'.format(interfaces.dut_hb_1, chksum_value1, chksum_mask)]

    l3_mirror_vlan = 40
    l3_mirror_is_truc = 'True'
    l3_mirror_truc_size = 300
    cli_object = topology_obj.players['dut']['cli']
    dutha2_mac = cli_object.mac.get_mac_address_for_interface(engines.dut, topology_obj.ports['dut-ha-2'])
    duthb1_mac = cli_object.mac.get_mac_address_for_interface(engines.dut, topology_obj.ports['dut-hb-1'])
    port_entry_action_param_list = ['{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                                     P4SamplingEntryConsts.duthb1_ip,
                                                                     P4SamplingEntryConsts.hbdut1_ip,
                                                                     l3_mirror_vlan, l3_mirror_is_truc,
                                                                     l3_mirror_truc_size),
                                    '{} {} {} {} {} {} {} {}'.format(interfaces.dut_ha_2, dutha2_mac, ha_dut_2_mac,
                                                                     P4SamplingEntryConsts.dutha2_ip,
                                                                     P4SamplingEntryConsts.hadut2_ip,
                                                                     l3_mirror_vlan, l3_mirror_is_truc,
                                                                     l3_mirror_truc_size)]
    port_entry_priority_list = [1, 1]
    port_entry_match_chksum_list = [chksum_value, chksum_value1]
    port_entry_mismatch_chksum_list = [0x0000, 0x0000]
    protocol = 6
    src_port = 20
    dst_port = 80
    l3_mirror_vlan_flow = 50

    flow_entry_key_list = ['{} {} {} {} {} {}/{}'.format(P4SamplingEntryConsts.hbdut1_ip, P4SamplingEntryConsts.dutha1_ip,
                                                         protocol, src_port, dst_port, chksum_value, chksum_mask),
                           '{} {} {} {} {} {}/{}'.format(P4SamplingEntryConsts.hadut2_ip, P4SamplingEntryConsts.duthb2_ip,
                                                         protocol, src_port, dst_port, chksum_value1, chksum_mask)]

    flow_entry_action_param_list = ['{} {} {} {} {} {} {} {}'.format(interfaces.dut_ha_2, dutha2_mac, ha_dut_2_mac,
                                                                     P4SamplingEntryConsts.dutha2_ip,
                                                                     P4SamplingEntryConsts.hadut2_ip,
                                                                     l3_mirror_vlan_flow, l3_mirror_is_truc,
                                                                     l3_mirror_truc_size),
                                    '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                                     P4SamplingEntryConsts.duthb1_ip,
                                                                     P4SamplingEntryConsts.hbdut1_ip,
                                                                     l3_mirror_vlan_flow, l3_mirror_is_truc,
                                                                     l3_mirror_truc_size)]
    flow_entry_priority_list = [1, 1]
    flow_entry_match_chksum_list = [chksum_value, chksum_value1]
    flow_entry_mismatch_chksum_list = [0x0000, 0x0000]
    port_entry = generate_entry_data(
        port_entry_key_list,
        port_entry_action_param_list,
        port_entry_priority_list,
        port_entry_match_chksum_list,
        port_entry_mismatch_chksum_list)
    flow_entry = generate_entry_data(
        flow_entry_key_list,
        flow_entry_action_param_list,
        flow_entry_priority_list,
        flow_entry_match_chksum_list,
        flow_entry_mismatch_chksum_list)

    table_param_data.port_entry = port_entry
    table_param_data.flow_entry = flow_entry
    return table_param_data


def generate_entry_data(entry_key_list, entry_action_list,
                        priority_list, match_chksum_list, mismatch_chksum_list):
    """
    Generate the entry data in the dictionary format
    :param entry_key_list: the key params of the entry
    :param entry_action_list: the action params of the entry
    :param priority_list: the priority params of the entry
    :param match_chksum_list: the match checksum value of the entry
    :param mismatch_chksum_list: the mismatch checksum value of the entry
    :return: entry data in dictionary format.
    """
    entry_data = {}
    for i in range(len(entry_key_list)):
        entry_params = DottedDict()
        entry_params.action = entry_action_list[i]
        entry_params.priority = priority_list[i]
        entry_params.match_chksum = match_chksum_list[i]
        entry_params.mismatch_chksum = mismatch_chksum_list[i]
        entry_data[entry_key_list[i]] = entry_params

    return entry_data
