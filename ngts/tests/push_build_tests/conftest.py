import pytest
import logging
import allure
import os
import itertools
import time
import random

from retry.api import retry_call
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vrf_config_template import VrfConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.config_templates.vxlan_config_template import VxlanConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.constants.constants import SonicConst
from ngts.constants.constants import SflowConsts
from ngts.tests.nightly.app_extension.app_extension_helper import APP_INFO, app_cleanup
from ngts.constants.constants import P4SamplingEntryConsts
from ngts.scripts.install_app_extension.install_app_extensions import install_all_supported_app_extensions
from ngts.conftest import update_topology_with_cli_class
import ngts.helpers.acl_helper as acl_helper
from ngts.helpers.acl_helper import ACLConstants
from ngts.helpers.sonic_branch_helper import update_branch_in_topology, update_sanitizer_in_topology
from ngts.helpers.sflow_helper import kill_sflowtool_process, remove_tmp_sample_file
from ngts.helpers.vxlan_helper import clean_frr_vrf_config
from ngts.helpers.rocev2_acl_counter_helper import copy_apply_rocev2_acl_config, remove_rocev2_acl_rule_and_talbe, \
    is_support_rocev2_acl_counter_feature
from ngts.helpers.sonic_branch_helper import get_sonic_branch
from ngts.constants.constants import AppExtensionInstallationConstants
from ngts.common.checkers import is_feature_ready


PRE_UPGRADE_CONFIG = '/tmp/config_db_{}_base.json'
POST_UPGRADE_CONFIG = '/tmp/config_db_{}_target.json'
FRR_CONFIG_FOLDER = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger()
ROCEV2_ACL_COUNTER_PATH = os.path.join(FRR_CONFIG_FOLDER, "L3/rocev2_acl_counter")


def get_test_app_ext_info(cli_obj):
    is_support_app_ext = cli_obj.app_ext.verify_version_support_app_ext()
    app_name = APP_INFO["name"]
    app_repository_name = APP_INFO["repository"]
    version = APP_INFO["shut_down"]["version"]
    return is_support_app_ext, app_name, version, app_repository_name


def is_evpn_support(image_branch):
    logger.info(f"SONiC image version: {image_branch}")
    unsupport_version_list = ['202012', '202205']
    for version in unsupport_version_list:
        if version in image_branch:
            return False
    return True


@pytest.fixture(scope='package', autouse=True)
def push_gate_configuration(topology_obj, cli_objects, engines, interfaces, platform_params, upgrade_params,
                            run_config_only, run_test_only, run_cleanup_only, shared_params,
                            app_extension_dict_path, acl_table_config_list, request, is_simx, sonic_branch):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param cli_objects: cli_objects fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :param platform_params: platform_params fixture
    :param upgrade_params: upgrade_params fixture
    :param run_config_only: test run mode run_config_only
    :param run_test_only: test run mode run_test_only
    :param run_cleanup_only: test run mode run_cleanup_only
    :param shared_params: fixture which provide dictionary which can be shared between tests
    :param app_extension_dict_path: app_extension_dict_path
    :param acl_table_config_list: acl_table_config_list fixture
    """
    full_flow_run = all(arg is False for arg in [run_config_only, run_test_only, run_cleanup_only])
    skip_tests = False
    ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]

    # Check if app_ext supported and get app name, repo, version
    base_sonic_branch = sonic_branch
    shared_params.app_ext_is_app_ext_supported, app_name, version, app_repository_name = \
        get_test_app_ext_info(cli_objects.dut)
    if run_config_only or full_flow_run:
        if upgrade_params.is_upgrade_required:
            with allure.step('Installing base version from ONIE'):
                logger.info('Deploying via ONIE or call manufacture script with arg onie')
                reboot_after_install = True if '201911' in upgrade_params.base_version else None
                cli_objects.dut.general.deploy_image(topology_obj, upgrade_params.base_version, apply_base_config=True,
                                                     setup_name=platform_params.setup_name,
                                                     platform_params=platform_params,
                                                     deploy_type='onie', reboot_after_install=reboot_after_install,
                                                     disable_ztp=True, configure_dns=True)
                base_sonic_branch = get_sonic_branch(topology_obj)

            with allure.step('Check that APP Extension supported on base version'):
                shared_params.app_ext_is_app_ext_supported, app_name, version, app_repository_name = \
                    get_test_app_ext_info(cli_objects.dut)

        if is_evpn_support(base_sonic_branch):
            with allure.step('Setting "docker_routing_config_mode": "split" in config_db.json'):
                cli_objects.dut.general.update_config_db_docker_routing_config_mode(topology_obj)

        with allure.step('Check that links in UP state'):
            retry_call(cli_objects.dut.interface.check_ports_status, fargs=[ports_list], tries=10,
                       delay=10, logger=logger)

        # Install app here in order to test migrating app from base image to target image
        if shared_params.app_ext_is_app_ext_supported:
            with allure.step("Install app {}".format(app_name)):
                install_app(engines.dut, cli_objects.dut, app_name, app_repository_name, version)
    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = cli_objects.dut.interface.get_interfaces_speed([interfaces.dut_ha_1,
                                                                                     interfaces.dut_hb_2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_1, '10G')},
                {'iface': interfaces.dut_hb_2, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '10G')}
                ]
    }

    # vrf related VLAN config in evpn vxlan test
    vrf_vlan_config_dict = {
        'dut': [{'vlan_id': 20, 'vlan_members': [{'PortChannel0002': 'trunk'}]}, {'vlan_id': 200, 'vlan_members': []}],
        'hb': [{'vlan_id': 20, 'vlan_members': [{'bond0': None}]}]
    }

    # vrf config
    vrf_config_dict = {
        'dut': [{'vrf': 'Vrf1', 'vrf_interfaces': ['Vlan20', "Vlan200"]}],
        'ha': [{'vrf': 'Vrf1', 'table': '10'}]
    }

    # vrf related IP config in evpn vxlan test
    vrf_ip_config_dict = {
        'dut': [{'iface': 'Vlan20', 'ips': [('20.0.0.1', '24')]}],
        'hb': [{'iface': 'bond0.20', 'ips': [('20.0.0.3', '24')]}]
    }

    # vrf related static route in evpn vxlan test
    vrf_static_route_config_dict = {
        'hb': [{'dst': '200.0.0.0', 'dst_mask': 24, 'via': ['20.0.0.1']}]
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
                {'vlan_id': 10, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 50, 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]},
                {'vlan_id': 100, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 101, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]}
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 690, 'vlan_members': [{interfaces.ha_dut_2: None}]},
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
                {'iface': 'Vlan50', 'ips': [(P4SamplingEntryConsts.duthb1_ip, '24')]},
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
               {'dst': '6900:1::', 'dst_mask': 64, 'via': ['6900::1']}]
    }

    vxlan_config_dict = {
        'dut': [{'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                 'tunnels': [{'vni': 76543, 'vlan': 69}]
                 }
                ]
    }

    evpn_vxlan_config_dict = {
        'dut': [{'evpn_nvo': 'my-nvo', 'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                 'vrf_vni_map': [{'vrf': 'Vrf1', 'vni': 500200}],
                 'tunnels': [{'vni': 76543, 'vlan': 69}, {'vni': 500100, 'vlan': 100}, {'vni': 500101, 'vlan': 101},
                             {'vni': 50020, 'vlan': 20}, {'vni': 500200, 'vlan': 200}]
                 }
                ],
        'ha': [{'vtep_name': 'vtep_50020', 'vtep_src_ip': '30.0.0.2', 'vni': 50020, 'vrf': 'Vrf1',
                'vtep_ips': [('20.0.0.2', '24'), ('20::2', '64')]},
               {'vtep_name': 'vtep_500200', 'vtep_src_ip': '30.0.0.2', 'vni': 500200, 'vrf': 'Vrf1',
                'vtep_ips': [('200.0.0.2', '24'), ('200::2', '64')]},
               {'vtep_name': 'vtep_500100', 'vtep_src_ip': '30.0.0.2', 'vni': 500100,
                'vtep_ips': [('100.0.0.2', '24'), ('100::2', '64')]},
               {'vtep_name': 'vtep_500101', 'vtep_src_ip': '30.0.0.2', 'vni': 500101,
                'vtep_ips': [('101.0.0.2', '24'), ('101::2', '64')]}],
        'hb': [{'vtep_name': 'vtep_500100', 'vtep_src_ip': '40.0.0.3', 'vni': 500100,
                'vtep_ips': [('100.0.0.3', '24'), ('100::3', '24')]}]
    }

    frr_config_dict = {
        'dut': {'configuration': {'config_name': 'dut_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER}},
        'ha': {'configuration': {'config_name': 'ha_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER}},
        'hb': {'configuration': {'config_name': 'hb_frr_conf.conf', 'path_to_config_file': FRR_CONFIG_FOLDER}}
    }

    clean_frr_dut = {
        'dut': [
            ['configure terminal', 'vrf Vrf1', 'no vni 500200', 'end'],
            ['configure terminal', 'no router bgp 65000 vrf Vrf1', 'end'],
            ['configure terminal', 'no router bgp', 'end']
        ]
    }

    clean_frr_ha = {
        'ha': clean_frr_dut['dut']
    }

    clean_frr_hb = {
        'hb': [
            ['configure terminal', 'no router bgp', 'end']
        ]
    }

    clean_frr_base_config_list = [clean_frr_dut, clean_frr_ha, clean_frr_hb]

    # Update CLI classes based on current SONiC branch
    update_branch_in_topology(topology_obj)
    update_sanitizer_in_topology(topology_obj)
    update_topology_with_cli_class(topology_obj)

    if run_config_only or full_flow_run:
        logger.info('Starting PushGate Common configuration')
        InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
        LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
        VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
        IpConfigTemplate.configuration(topology_obj, ip_config_dict)
        RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
        acl_helper.add_acl_table(cli_objects.dut, acl_table_config_list)
        acl_helper.add_acl_rules(engines.dut, cli_objects.dut, acl_table_config_list)
        if is_support_rocev2_acl_counter_feature(cli_objects, is_simx, base_sonic_branch):
            copy_apply_rocev2_acl_config(engines.dut, "rocev2_acl.json", ROCEV2_ACL_COUNTER_PATH)
        if not upgrade_params.is_upgrade_required:
            VxlanConfigTemplate.configuration(topology_obj, vxlan_config_dict)

        if is_evpn_support(base_sonic_branch):
            VlanConfigTemplate.configuration(topology_obj, vrf_vlan_config_dict)
            VrfConfigTemplate.configuration(topology_obj, vrf_config_dict)
            IpConfigTemplate.configuration(topology_obj, vrf_ip_config_dict)
            VxlanConfigTemplate.configuration(topology_obj, evpn_vxlan_config_dict)
            RouteConfigTemplate.configuration(topology_obj, vrf_static_route_config_dict)
            # in case there is useless bgp configuration exist
            clean_frr_vrf_config(topology_obj, clean_frr_base_config_list)
            FrrConfigTemplate.configuration(topology_obj, frr_config_dict)

        with allure.step('Doing debug logs print'):
            log_debug_info(cli_objects.dut)

        with allure.step('Doing conf save'):
            logger.info('Doing config save')
            cli_objects.dut.general.save_configuration()

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
                    cli_objects.dut.general.deploy_image(topology_obj, upgrade_params.target_version,
                                                         platform_params=platform_params, apply_base_config=False,
                                                         deploy_type='sonic', configure_dns=True)

                # Update CLI classes based on current SONiC branch
                update_branch_in_topology(topology_obj)
                update_sanitizer_in_topology(topology_obj)
                update_topology_with_cli_class(topology_obj)

                with allure.step('Copying config_db.json from target version'):
                    engines.dut.copy_file(source_file='config_db.json',
                                          dest_file=POST_UPGRADE_CONFIG.format(engines.dut.ip),
                                          file_system=SonicConst.SONIC_CONFIG_FOLDER, overwrite_file=True,
                                          verify_file=False,
                                          direction='get')
                with allure.step("Installing wjh deb url"):
                    if upgrade_params.wjh_deb_url:
                        cli_objects.dut.general.install_wjh(engines.dut, upgrade_params.wjh_deb_url)
                    else:
                        install_all_supported_app_extensions(cli_objects.dut, app_extension_dict_path, platform_params)

    if run_test_only or full_flow_run:
        yield
    else:
        skip_tests = True

    if run_cleanup_only or full_flow_run:
        logger.info('Starting PushGate Common configuration cleanup')
        if not upgrade_params.is_upgrade_required:
            VxlanConfigTemplate.cleanup(topology_obj, vxlan_config_dict)
        if is_evpn_support(base_sonic_branch):
            with allure.step('Removing "docker_routing_config_mode" from config_db.json'):
                cli_objects.dut.general.update_config_db_docker_routing_config_mode(
                    topology_obj, remove_docker_routing_config_mode=True)
            logger.info('Check that links in UP state')
            cli_objects.dut.interface.check_link_state(ports_list)

            clean_frr_vrf_config(topology_obj, clean_frr_base_config_list)
            IpConfigTemplate.cleanup(topology_obj, vrf_ip_config_dict)
            VrfConfigTemplate.cleanup(topology_obj, vrf_config_dict)
            RouteConfigTemplate.cleanup(topology_obj, vrf_static_route_config_dict)
            VxlanConfigTemplate.cleanup(topology_obj, evpn_vxlan_config_dict)
            VlanConfigTemplate.cleanup(topology_obj, vrf_vlan_config_dict)

        if is_support_rocev2_acl_counter_feature(cli_objects, is_simx, base_sonic_branch):
            acl_type_list = ['CUSTOM_L3']
            remove_rocev2_acl_rule_and_talbe(topology_obj, ["ROCE_ACL_INGRESS"], acl_type_list)

        acl_helper.clear_acl_rules(engines.dut, cli_objects.dut)
        acl_helper.remove_acl_table(cli_objects.dut, acl_table_config_list)
        RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
        IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
        VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
        LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
        InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
        if shared_params.app_ext_is_app_ext_supported:
            app_cleanup(engines.dut, cli_objects.dut, app_name)
        logger.info('Doing config save after cleanup')
        cli_objects.dut.general.save_configuration()

        logger.info('PushGate Common cleanup completed')

    if skip_tests:
        pytest.skip('Skipping test according to flags: run_config_only/run_test_only/run_cleanup_only')


def log_debug_info(cli_obj):
    logger.info('Started debug prints')
    cli_obj.interface.show_interfaces_status()
    cli_obj.ip.show_ip_interfaces()
    cli_obj.vlan.show_vlan_config()
    cli_obj.route.show_ip_route()
    cli_obj.route.show_ip_route(ipv6=True)
    cli_obj.vxlan.show_vxlan_tunnel()
    cli_obj.vxlan.show_vxlan_vlanvnimap()
    logger.info('Finished debug prints')


def install_app(dut_engine, cli_obj, app_name, app_repository_name, version):
    try:
        with allure.step("Clean up app before install"):
            app_cleanup(dut_engine, cli_obj, app_name)
        with allure.step("Install {}, version={}".format(app_name, version)):
            cli_obj.app_ext.add_repository(app_name, app_repository_name, version=version)
            cli_obj.app_ext.install_app(app_name)
        with allure.step("Enable app and save config"):
            cli_obj.app_ext.enable_app(app_name)
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

    yield acl_table_config_list


@pytest.fixture(scope='package', autouse=True)
def basic_sflow_configuration_for_function(engines, cli_objects, interfaces, push_gate_configuration):
    """
    Pytest fixture used to configure basic sflow configuration for test function
    :param engines: engines fixture
    :param cli_objects: cli_objects fixture
    :param interfaces: interfaces fixture
    """
    cli_obj = cli_objects.dut
    with allure.step(f"Start feature {SflowConsts.SFLOW_FEATURE_NAME}"):
        cli_obj.sflow.enable_sflow_feature()
        time.sleep(2)
    with allure.step(f"Enable {SflowConsts.SFLOW_FEATURE_NAME} globally"):
        cli_obj.sflow.enable_sflow()
    with allure.step(f"Add collector {SflowConsts.COLLECTOR_0} with udp port {SflowConsts.DEFAULT_UDP}"):
        cli_obj.sflow.add_collector(SflowConsts.COLLECTOR_0, SflowConsts.COLLECTOR_0_IP)
    with allure.step("Disable all sflow interface"):
        cli_obj.sflow.disable_all_sflow_interface()
    with allure.step(f"Enable sflow interface {interfaces.dut_ha_1}"):
        cli_obj.sflow.enable_sflow_interface(interfaces.dut_ha_1)
    with allure.step(f"Enable sflow interface {interfaces.dut_ha_2}"):
        cli_obj.sflow.enable_sflow_interface(interfaces.dut_ha_2)

    yield

    with allure.step(f"Delete collector {SflowConsts.COLLECTOR_0}"):
        cli_obj.sflow.del_collector(SflowConsts.COLLECTOR_0)
    with allure.step("Delete agent id"):
        cli_obj.sflow.del_agent_id()
    with allure.step(f"Disable sflow interface {interfaces.dut_ha_1}"):
        cli_obj.sflow.disable_sflow_interface(interfaces.dut_ha_1)
    with allure.step(f"Disable sflow interface {interfaces.dut_ha_2}"):
        cli_obj.sflow.disable_sflow_interface(interfaces.dut_ha_2)
    with allure.step(f"Disable {SflowConsts.SFLOW_FEATURE_NAME} globally"):
        cli_obj.sflow.disable_sflow()
    with allure.step("Kill all sflowtool process"):
        kill_sflowtool_process(engines)
    with allure.step(f"Stop feature {SflowConsts.SFLOW_FEATURE_NAME}"):
        cli_obj.sflow.disable_sflow_feature()
    with allure.step("Remove sflowtool sample files"):
        remove_tmp_sample_file(engines)


def check_feature_enabled(cli_objects, feature):
    """
    This function is used to check the feature installed status
    """
    with allure.step(f"Validating {feature} is installed and enabled on the DUT"):
        status, msg = is_feature_ready(cli_objects, feature_name=feature, docker_name=feature)

    return status, msg


@pytest.fixture(scope='package', autouse=True)
def randomly_enable_sflow_wjh(cli_objects, basic_sflow_configuration_for_function):
    """
    Pytest fixture which is used to disable feature sflow and wjh then enable them randomly
    """
    feature_list = [SflowConsts.SFLOW_FEATURE_NAME, AppExtensionInstallationConstants.WJH_APP_NAME]

    with allure.step("Check feature sflow and wjh feature installed status and docker status"):
        for feature in feature_list:
            status, msg = check_feature_enabled(cli_objects, feature)
            if not status:
                logger.info(f"Skipping randomly enable sflow and whj - {msg}")
                return

    with allure.step("Disable feature sflow and wjh"):
        cli_objects.dut.general.set_feature_state(SflowConsts.SFLOW_FEATURE_NAME, 'disabled')
        cli_objects.dut.general.set_feature_state(AppExtensionInstallationConstants.WJH_APP_NAME, 'disabled')

    with allure.step("Enable feature sflow and wjh randomly"):
        random.shuffle(feature_list)
        for feature in feature_list:
            logger.info(f"Enabling feature {feature}")
            cli_objects.dut.general.set_feature_state(feature, 'enabled')