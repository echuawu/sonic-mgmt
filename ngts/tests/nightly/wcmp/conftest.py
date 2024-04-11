import logging
import pytest
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.helpers.adaptive_routing_helper import ArHelper
from ngts.helpers.wcmp_helper import WcmpHelper
from ngts.tests.nightly.wcmp.constants import WcmpConsts

logger = logging.getLogger()
ar_helper = ArHelper()


@pytest.fixture(scope='session')
def duthost(engines):
    return engines.dut


@pytest.fixture(scope='session')
def ha_obj(engines):
    return engines.ha


@pytest.fixture(scope='session')
def ip_config_dict(interfaces):
    return {
        'dut': [
            {'iface': interfaces.dut_ha_1,
             'ips': [(WcmpConsts.V4_CONFIG['dut_ha_1'], '24'), (WcmpConsts.V6_CONFIG['dut_ha_1'], '64')]},
            {'iface': interfaces.dut_ha_2,
             'ips': [(WcmpConsts.V4_CONFIG['dut_ha_2'], '24'), (WcmpConsts.V6_CONFIG['dut_ha_2'], '64')]},
            {'iface': interfaces.dut_hb_1,
             'ips': [(WcmpConsts.V4_CONFIG['dut_hb_1'], '24'), (WcmpConsts.V6_CONFIG['dut_hb_1'], '64')]},
            {'iface': interfaces.dut_hb_2,
             'ips': [(WcmpConsts.V4_CONFIG['dut_hb_2'], '24'), (WcmpConsts.V6_CONFIG['dut_hb_2'], '64')]},
        ],
        'ha': [
            {'iface': interfaces.ha_dut_1,
             'ips': [(WcmpConsts.V4_CONFIG['ha_dut_1'], '24'), (WcmpConsts.V6_CONFIG['ha_dut_1'], '64')]},
            {'iface': interfaces.ha_dut_2,
             'ips': [(WcmpConsts.V4_CONFIG['ha_dut_2'], '24'), (WcmpConsts.V6_CONFIG['ha_dut_2'], '64')]}
        ],
        'hb': [
            {'iface': interfaces.hb_dut_1,
             'ips': [(WcmpConsts.V4_CONFIG['hb_dut_1'], '24'), (WcmpConsts.V6_CONFIG['hb_dut_1'], '64')]},
            {'iface': interfaces.hb_dut_2,
             'ips': [(WcmpConsts.V4_CONFIG['hb_dut_2'], '24'), (WcmpConsts.V6_CONFIG['hb_dut_2'], '64')]}
        ]
    }


@pytest.fixture(scope='session')
def setup_function(topology_obj, cli_objects, ip_config_dict, request, interfaces):
    # --------------------- Setup -----------------------
    with allure.step("STEP1: Setting 'docker_routing_config_mode': 'split' in config_db.json"):
        cli_objects.dut.general.update_config_db_docker_routing_config_mode(topology_obj)

    with allure.step("STEP2: Enable doai and ar"):
        ar_helper.enable_doai_service(cli_objects)
        ar_helper.enable_ar_function(cli_objects)

    with allure.step("STEP3: Add dummy interface on host"):
        WcmpHelper.add_and_enable_interface(cli_objects.ha, WcmpConsts.DUMMY_INTF_HA)
        WcmpHelper.add_and_enable_interface(cli_objects.hb, WcmpConsts.DUMMY_INTF_HB)

    with allure.step("STEP4: Config IP on hosts and DUT"):
        IpConfigTemplate.configuration(topology_obj, ip_config_dict, request)

    with allure.step("STEP5: Establish BGP neighbor between hosts and DUT"):
        FrrConfigTemplate.configuration(topology_obj, WcmpConsts.FRR_CONFIG_CONFIG_DICT)

    with allure.step("STEP6: Verify BGP neighbor"):
        for neighbor in [WcmpConsts.V4_CONFIG['ha_dut_1'], WcmpConsts.V4_CONFIG['ha_dut_2'],
                         WcmpConsts.V4_CONFIG['hb_dut_1'], WcmpConsts.V4_CONFIG['hb_dut_2'],
                         WcmpConsts.V6_CONFIG['ha_dut_1'], WcmpConsts.V6_CONFIG['ha_dut_2'],
                         WcmpConsts.V6_CONFIG['hb_dut_1'], WcmpConsts.V6_CONFIG['hb_dut_2']]:
            logger.info(f'Validate BGP neighbor {neighbor} established')
            cli_objects.dut.frr.validate_bgp_neighbor_established(neighbor)

    with allure.step("STEP7: Enable ar interface"):
        ar_interface_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
        ar_helper.enable_ar_port(cli_objects, ar_interface_list)

    yield

    # --------------------- Teardown -----------------------
    with allure.step("STEP1: Disable ar interface"):
        ar_helper.disable_ar_port(cli_objects, ar_interface_list)

    with allure.step("STEP2: Cleanup BGP session between hosts and DUT"):
        FrrConfigTemplate.cleanup(topology_obj, WcmpConsts.FRR_CONFIG_CONFIG_DICT)

    with allure.step("STEP3: Delete IP on hosts and DUT"):
        IpConfigTemplate.cleanup(topology_obj, ip_config_dict)

    with allure.step("STEP4: Delete dummy interface on host"):
        cli_objects.ha.interface.del_interface(WcmpConsts.DUMMY_INTF_HA['name'])
        cli_objects.hb.interface.del_interface(WcmpConsts.DUMMY_INTF_HB['name'])

    with allure.step("STEP5: Disable doai and ar"):
        ar_helper.disable_ar(cli_objects)
        ar_helper.disable_doai_service(cli_objects)


@pytest.fixture(scope='function', autouse=True)
def disable_wcmp(cli_objects):
    """
    This fixture is used to disable WCMP after each test case.
    """

    yield

    with allure.step("Disable WCMP"):
        cli_objects.dut.wcmp.config_wcmp_cli(status=WcmpConsts.WCMP_STATUS_DISABLED)
        cli_objects.dut.wcmp.get_frr_bgp_config()
