import pytest
import logging
import allure
import os
import itertools

from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.config_templates.vxlan_config_template import VxlanConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.constants.constants import SonicConst
from ngts.tests.nightly.app_extension.app_extension_helper import APP_INFO, app_cleanup
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
import ngts.helpers.p4_sampling_fixture_helper as fixture_helper
from ngts.constants.constants import P4SamplingEntryConsts
from ngts.helpers.p4_sampling_utils import P4SamplingUtils
from ngts.cli_wrappers.sonic.sonic_vxlan_clis import SonicVxlanCli
from ngts.scripts.install_app_extension.install_app_extesions import install_all_supported_app_extensions
from ngts.conftest import update_topology_with_cli_class
import ngts.helpers.acl_helper as acl_helper
from ngts.helpers.acl_helper import ACLConstants


PRE_UPGRADE_CONFIG = '/tmp/config_db_{}_base.json'
POST_UPGRADE_CONFIG = '/tmp/config_db_{}_target.json'
FRR_CONFIG_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger()


def get_app_ext_info(engine):
    is_support_app_ext = SonicAppExtensionCli.verify_version_support_app_ext(engine)
    app_name = APP_INFO["name"]
    app_repository_name = APP_INFO["repository"]
    version = APP_INFO["shut_down"]["version"]
    return is_support_app_ext, app_name, version, app_repository_name


@pytest.fixture(scope='package', autouse=True)
def push_gate_configuration(topology_obj, engines, interfaces, platform_params, upgrade_params,
                            run_config_only, run_test_only, run_cleanup_only, p4_sampling_table_params, shared_params,
                            app_extension_dict_path, update_branch_in_topology, acl_table_config_list):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :param platform_params: platform_params fixture
    :param upgrade_params: upgrade_params fixture
    :param run_config_only: test run mode run_config_only
    :param run_test_only: test run mode run_test_only
    :param run_cleanup_only: test run mode run_cleanup_only
    :param p4_sampling_table_params: p4_sampling_table_params fixture
    :param shared_params: fixture which provide dictionary which can be shared between tests
    :param app_extension_dict_path: app_extension_dict_path
    :param update_branch_in_topology: fixture which doing update branch in topology
    """
    full_flow_run = all(arg is False for arg in [run_config_only, run_test_only, run_cleanup_only])
    skip_tests = False

    cli_object = topology_obj.players['dut']['cli']

    # Check if app_ext supported and get app name, repo, version
    shared_params.app_ext_is_app_ext_supported, app_name, version, app_repository_name = get_app_ext_info(engines.dut)
    if run_config_only or full_flow_run:
        if upgrade_params.is_upgrade_required:
            with allure.step('Installing base version from ONIE'):
                logger.info('Deploying via ONIE or call manufacture script with arg onie')
                reboot_after_install = True if '201911' in upgrade_params.base_version else None
                SonicGeneralCli.deploy_image(topology_obj, upgrade_params.base_version, apply_base_config=True,
                                             setup_name=platform_params.setup_name, platform_params=platform_params,
                                             deploy_type='onie', reboot_after_install=reboot_after_install)

            with allure.step('Check that APP Extension supported on base version'):
                shared_params.app_ext_is_app_ext_supported, app_name, version, app_repository_name = \
                    get_app_ext_info(engines.dut)

        with allure.step('Check that links in UP state'.format()):
            ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
            retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ports_list], tries=10, delay=10,
                       logger=logger)

        # Install app here in order to test migrating app from base image to target image
        if shared_params.app_ext_is_app_ext_supported:
            with allure.step("Install app {}".format(app_name)):
                install_app(engines.dut, app_name, app_repository_name, version)
    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, [interfaces.dut_ha_1,
                                                                                          interfaces.dut_hb_2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_1, '10G')},
                {'iface': interfaces.dut_hb_2, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '10G')}
                ]
    }

    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [interfaces.dut_ha_1]},
                {'type': 'lacp', 'name': 'PortChannel0002', 'members': [interfaces.dut_hb_2]}
                ],
        'ha': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.ha_dut_1]}],
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.hb_dut_2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 40, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 69, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 690, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 691, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 10, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 50, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]},
                {'vlan_id': 100, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 101, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]}
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 690, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 691, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 10, 'vlan_members': [{interfaces.ha_dut_2: None}]}
               ],
        'hb': [{'vlan_id': 40, 'vlan_members': [{'bond0': None}]},
               {'vlan_id': 69, 'vlan_members': [{'bond0': None}]},
               {'vlan_id': 50, 'vlan_members': [{interfaces.hb_dut_1: None}]},
               {'vlan_id': 101, 'vlan_members': [{'bond0': None}]}
               ]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan40', 'ips': [('40.0.0.1', '24'), ('4000::1', '64')]},
                {'iface': 'PortChannel0001', 'ips': [('30.0.0.1', '24'), ('3000::1', '64')]},
                {'iface': 'Vlan69', 'ips': [('69.0.0.1', '24'), ('6900::1', '64')]},
                {'iface': 'Vlan690', 'ips': [('69.0.1.1', '24'), ('6900:1::1', '64')]},
                {'iface': 'Vlan691', 'ips': [('69.1.0.1', '24'), ('6910::1', '64')]},
                {'iface': 'Vlan50'.format(interfaces.dut_hb_1), 'ips': [(P4SamplingEntryConsts.duthb1_ip, '24')]},
                {'iface': 'Vlan10', 'ips': [(P4SamplingEntryConsts.dutha2_ip, '24')]},
                {'iface': 'Loopback0', 'ips': [('10.1.0.32', '32')]},
                {'iface': 'Vlan100', 'ips': [('100.0.0.1', '24'), ('100::1', '64')]},
                {'iface': 'Vlan101', 'ips': [('101.0.0.1', '24'), ('101::1', '64')]}
                ],
        'ha': [{'iface': '{}.40'.format(interfaces.ha_dut_2), 'ips': [('40.0.0.2', '24'), ('4000::2', '64')]},
               {'iface': '{}.10'.format(interfaces.ha_dut_2), 'ips': [(P4SamplingEntryConsts.hadut2_ip, '24')]},
               {'iface': 'bond0', 'ips': [('30.0.0.2', '24'), ('3000::2', '64')]}
               ],
        'hb': [{'iface': 'bond0.40', 'ips': [('40.0.0.3', '24'), ('4000::3', '64')]},
               {'iface': 'bond0.69', 'ips': [('69.0.0.2', '24'), ('6900::2', '64')]},
               {'iface': '{}.50'.format(interfaces.hb_dut_1), 'ips': [(P4SamplingEntryConsts.hbdut1_ip, '24')]},
               {'iface': 'bond0.101', 'ips': [('101.0.0.3', '24'), ('101::3', '64')]}
               ]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'hb': [{'dst': '69.0.1.0', 'dst_mask': 24, 'via': ['69.0.0.1']},
               {'dst': '69.1.0.0', 'dst_mask': 24, 'via': ['69.0.0.1']},
               {'dst': '6900:1::', 'dst_mask': 64, 'via': ['6900::1']},
               {'dst': '6910::', 'dst_mask': 64, 'via': ['6900::1']}]
    }

    """
    TODO: once EVPN-VXLAN will be supported - need to change line:
    FROM: 'dut': [{'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
    TO:   'dut': [{'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32', 'evpn_nvo': 'nvo',
    For now if add 'evpn_nvo': 'nvo' - VXLAN decap test will fail
    """
    vxlan_config_dict = {
        'dut': [{'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                 'tunnels': [{'vni': 76543, 'vlan': 69}]  # , {'vni': 500100, 'vlan': 100}, {'vni': 500101, 'vlan': 101}
                 }
                ],
        # TODO: Enable VNI 500100 and 500101 configuration once EVPN-VXLAN will be supported
        # 'ha': [{'vtep_name': 'vtep_500100', 'vtep_src_ip': '30.0.0.2', 'vni': 500100,
        #         'vtep_ips': [('100.0.0.2', '24'), ('100::2', '64')]},
        #        {'vtep_name': 'vtep_500101', 'vtep_src_ip': '30.0.0.2', 'vni': 500101,
        #         'vtep_ips': [('101.0.0.2', '24'), ('101::2', '64')]}],
        # 'hb': [{'vtep_name': 'vtep_500100', 'vtep_src_ip': '40.0.0.3', 'vni': 500100,
        #         'vtep_ips': [('100.0.0.3', '24'), ('100::3', '24')]}]
    }

    frr_config_dict = {
        'dut': {'configuration': {'config_name': 'dut_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER},
                'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
        'ha': {'configuration': {'config_name': 'ha_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER},
               'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']},
        'hb': {'configuration': {'config_name': 'hb_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER},
               'cleanup': ['configure terminal', 'no router bgp 65000', 'exit', 'exit']}
    }

    # Update CLI classes based on current SONiC branch
    update_branch_in_topology(topology_obj)
    update_topology_with_cli_class(topology_obj)

    if run_config_only or full_flow_run:
        logger.info('Starting PushGate Common configuration')
        InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
        LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
        VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
        IpConfigTemplate.configuration(topology_obj, ip_config_dict)
        RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
        if not upgrade_params.is_upgrade_required:
            VxlanConfigTemplate.configuration(topology_obj, vxlan_config_dict)
            FrrConfigTemplate.configuration(topology_obj, frr_config_dict)
        # add p4 sampling entries, need to check is the p4-sampling is installed or not
        if P4SamplingUtils.check_p4_sampling_installed(engines.dut) and \
                fixture_helper.is_p4_sampling_supported(platform_params):
            fixture_helper.add_p4_sampling_entries(engines, p4_sampling_table_params)
        with allure.step('Doing debug logs print'):
            log_debug_info(engines.dut, cli_object)

        with allure.step('Doing conf save'):
            logger.info('Doing config save')
            cli_object.general.save_configuration(engines.dut)

        logger.info('PushGate Common configuration completed')

        if upgrade_params.is_upgrade_required:
            with allure.step('Doing upgrade to target version'):
                with allure.step('Copying config_db.json from base version'):
                    engines.dut.copy_file(source_file='config_db.json',
                                          dest_file=PRE_UPGRADE_CONFIG.format(engines.dut.ip),
                                          file_system=SonicConst.SONIC_CONFIG_FOLDER, overwrite_file=True,
                                          verify_file=False, direction='get')
                with allure.step('Performing sonic to sonic upgrade'):
                    logger.info('Performing sonic to sonic upgrade')
                    SonicGeneralCli.deploy_image(topology_obj, upgrade_params.target_version, apply_base_config=False,
                                                 deploy_type='sonic')

                # Update CLI classes based on current SONiC branch
                update_branch_in_topology(topology_obj)
                update_topology_with_cli_class(topology_obj)

                with allure.step('Copying config_db.json from target version'):
                    engines.dut.copy_file(source_file='config_db.json',
                                          dest_file=POST_UPGRADE_CONFIG.format(engines.dut.ip),
                                          file_system=SonicConst.SONIC_CONFIG_FOLDER, overwrite_file=True,
                                          verify_file=False,
                                          direction='get')
                with allure.step("Installing wjh deb url"):
                    if upgrade_params.wjh_deb_url:
                        SonicGeneralCli.install_wjh(engines.dut, upgrade_params.wjh_deb_url)
                    else:
                        install_all_supported_app_extensions(engines.dut, app_extension_dict_path)

    if run_test_only or full_flow_run:
        yield
    else:
        skip_tests = True

    if run_cleanup_only or full_flow_run:
        logger.info('Starting PushGate Common configuration cleanup')
        if not upgrade_params.is_upgrade_required:
            FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
            VxlanConfigTemplate.cleanup(topology_obj, vxlan_config_dict)

        RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
        IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
        VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
        LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
        InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
        if P4SamplingUtils.check_p4_sampling_installed(engines.dut) and \
                fixture_helper.is_p4_sampling_supported(platform_params):
            fixture_helper.remove_p4_sampling_entries(topology_obj, interfaces, engines, p4_sampling_table_params)
        if shared_params.app_ext_is_app_ext_supported:
            app_cleanup(engines.dut, app_name)
        logger.info('Doing config save after cleanup')
        cli_object.general.save_configuration(engines.dut)

        logger.info('PushGate Common cleanup completed')

    if skip_tests:
        pytest.skip('Skipping test according to flags: run_config_only/run_test_only/run_cleanup_only')


@pytest.fixture(scope='package')
def p4_sampling_table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac):
    """
    Fixture used to create the TableParams object which contains some params used in the testcases
    :param interfaces: interfaces fixture
    :param engines : engines fixture object
    :param topology_obj: topology_obj fixture object
    :param ha_dut_2_mac: ha_dut_2_mac fixture object
    :param hb_dut_1_mac: hb_dut_1_mac fixture object
    """
    return fixture_helper.get_table_params(interfaces, engines, topology_obj, ha_dut_2_mac, hb_dut_1_mac)


def log_debug_info(dut_engine, cli_obj):
    logger.info('Started debug prints')
    SonicInterfaceCli.show_interfaces_status(dut_engine)
    SonicIpCli.show_ip_interfaces(dut_engine)
    cli_obj.vlan.show_vlan_config(dut_engine)
    SonicRouteCli.show_ip_route(dut_engine)
    SonicRouteCli.show_ip_route(dut_engine, ipv6=True)
    SonicVxlanCli.show_vxlan_tunnel(dut_engine)
    SonicVxlanCli.show_vxlan_vlanvnimap(dut_engine)
    logger.info('Finished debug prints')


def install_app(dut_engine, app_name, app_repository_name, version):
    try:
        with allure.step("Clean up app before install"):
            app_cleanup(dut_engine, app_name)
        with allure.step("Install {}, verison=".format(app_name, version)):
            SonicAppExtensionCli.add_repository(dut_engine, app_name, app_repository_name, version=version)
            SonicAppExtensionCli.install_app(dut_engine, app_name)
        with allure.step("Enable app and save config"):
            SonicAppExtensionCli.enable_app(dut_engine, app_name)
    except Exception as err:
        raise AssertionError(err)


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
    logger.info("Creating temporary folder \"{}\" for ACL test".format(ACLConstants.DUT_ACL_TMP_DIR))
    engines.dut.run_cmd("mkdir -p {}".format(ACLConstants.DUT_ACL_TMP_DIR))

    yield acl_table_config_list
    logger.info("Removing temporary directory \"{}\"".format(ACLConstants.DUT_ACL_TMP_DIR))
    engines.dut.run_cmd("rm -rf {}".format(ACLConstants.DUT_ACL_TMP_DIR))
