"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging
import allure
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.tests.push_build_tests.p4.sampling_example.constants import SamplingConsts
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.tests.push_build_tests.p4.sampling_example.constants import SamplingEntryConsts
logger = logging.getLogger()
SPEED = '10G'


@pytest.fixture(scope='package', autouse=True)
def sampling_pipline(topology_obj):
    """
    Fixture used to install the p4-sampling app before run the testcase, and uninstall it after the testcase
    :param topology_obj: topology object fixture
    """
    engine = topology_obj.players['dut']['engine']
    app_name = SamplingConsts.APP_NAME
    repository = SamplingConsts.REPOSITORY
    version = SamplingConsts.VERSION

    with allure.step('Check if the repository of the {} added and if it is Installed '.format(app_name)):
        app_list = SonicAppExtensionCli.parse_app_package_list_dict(engine)
        if app_name in app_list:
            app_data = app_list[app_name]
            app_status = app_data['Status']
            if app_status == 'Installed':
                with allure.step('Disable {}'.format(app_name)):
                    SonicGeneralCli.set_feature_state(
                        engine, app_name, 'disabled')
                with allure.step('Uninstall {}'.format(app_name)):
                    SonicAppExtensionCli.uninstall_app(engine, app_name)
            with allure.step('Remove {} app from {} Repository'.format(app_name, repository)):
                SonicAppExtensionCli.remove_repository(engine, app_name)

    with allure.step('Add {} app to {} Repository'.format(app_name, repository)):
        SonicAppExtensionCli.add_repository(engine, app_name, repository)
    with allure.step('Install {} with version {}'.format(app_name, version)):
        SonicAppExtensionCli.install_app(engine, app_name, version)
    with allure.step('Enable {}'.format(app_name)):
        SonicGeneralCli.set_feature_state(engine, app_name, 'enabled')
    logger.info('{} installation completed'.format(app_name))

    yield

    with allure.step('Disable {}'.format(app_name)):
        SonicGeneralCli.set_feature_state(engine, app_name, 'disabled')
    with allure.step('Uninstall {}'.format(app_name)):
        SonicAppExtensionCli.uninstall_app(engine, app_name)
    with allure.step('Remove {} app from {} Repository'.format(app_name, repository)):
        SonicAppExtensionCli.remove_repository(engine, app_name)
    with allure.step('Verify the app is uninstalled'):
        app_list = SonicAppExtensionCli.parse_app_package_list_dict(engine)
        assert app_name not in app_list

    logger.info('{} uninstallation completed'.format(app_name))


@pytest.fixture(scope="package", autouse=False)
def skipping_p4_sampling_test_case(engines, platform_params):
    """
    If p4-samping is not ready, skipping all p4-sampling test cases execution
    :param engines: engines fixture
    :param platform_params: platform_params fixture
    """
    if 'SN2' in platform_params.hwsku:
        pytest.skip("Skipping p4-sampling test cases as SPC1 does not support it")
    if not SonicAppExtensionCli.verify_version_support_app_ext(engines.dut):
        pytest.skip("Skipping p4-sampling test cases as the running version does not support app extension feature.")


@pytest.fixture(scope='package', autouse=True)
def p4_sampling_configuration(skipping_p4_sampling_test_case, topology_obj, engines, interfaces):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    """

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, [interfaces.dut_ha_1,
                                                                                          interfaces.dut_ha_2,
                                                                                          interfaces.dut_hb_1,
                                                                                          interfaces.dut_hb_2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'speed': SPEED,
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_1, SPEED)},
                {'iface': interfaces.dut_ha_2, 'speed': SPEED,
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_2, SPEED)},
                {'iface': interfaces.dut_hb_1, 'speed': SPEED,
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_1, SPEED)},
                {'iface': interfaces.dut_hb_2, 'speed': SPEED,
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, SPEED)}
                ]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': '{}'.format(interfaces.dut_ha_1), 'ips': [(SamplingEntryConsts.dutha1_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_ha_2), 'ips': [(SamplingEntryConsts.dutha2_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_hb_1), 'ips': [(SamplingEntryConsts.duthb1_ip, '24')]},
                {'iface': '{}'.format(interfaces.dut_hb_2), 'ips': [(SamplingEntryConsts.duthb2_ip, '24')]}
                ],
        'ha': [{'iface': '{}'.format(interfaces.ha_dut_1), 'ips': [(SamplingEntryConsts.hadut1_ip, '24')]},
               {'iface': '{}'.format(interfaces.ha_dut_2), 'ips': [(SamplingEntryConsts.hadut2_ip, '24')]}],
        'hb': [{'iface': '{}'.format(interfaces.hb_dut_1), 'ips': [(SamplingEntryConsts.hbdut1_ip, '24')]},
               {'iface': '{}'.format(interfaces.hb_dut_2), 'ips': [(SamplingEntryConsts.hbdut2_ip, '24')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'ha': [{'dst': '50.0.0.0', 'dst_mask': 24, 'via': [SamplingEntryConsts.dutha1_ip]},
               {'dst': '50.0.1.0', 'dst_mask': 24, 'via': [SamplingEntryConsts.dutha2_ip]}],
        'hb': [{'dst': '10.0.0.0', 'dst_mask': 24, 'via': [SamplingEntryConsts.duthb1_ip]},
               {'dst': '10.0.1.0', 'dst_mask': 24, 'via': [SamplingEntryConsts.duthb2_ip]}]
    }

    logger.info('Starting P4 Sampling configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('P4 Sampling Common configuration completed')

    yield

    logger.info('Starting P4 Sampling configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
    logger.info('P4 Sampling cleanup completed')
