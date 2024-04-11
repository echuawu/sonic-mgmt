import logging
import pytest
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.helpers.vxlan_helper import sonic_ports_flap
from ngts.helpers.wcmp_helper import WcmpHelper
from ngts.tests.nightly.wcmp.constants import WcmpConsts
logger = logging.getLogger()

"""

WCMP Test Cases on canonical setup

Documentation:
https://confluence.nvidia.com/display/SW/Weighted+Cost+Multi+Path+Test+Plan#WeightedCostMultiPathTestPlan-CanonicalSetup

"""


def test_config_wcmp_by_cli(cli_objects, setup_function, topology_obj, duthost):
    with allure.step("STEP1: Enable WCMP"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)

    with allure.step("STEP2: Verify WCMP enabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP3: Verify bgp bandwidth community is configured in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config

    with allure.step("STEP4: Disable WCMP"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_DISABLED)

    with allure.step("STEP5: Verify WCMP disabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_DISABLED

    with allure.step("STEP6: Verify bgp bandwidth community does not exist in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG not in frr_bgp_config

    with allure.step("STEP7: Config WCMP negative test"):
        for invalid_value in WcmpConsts.WCMP_STATUS_INVALID:
            error_msg = cli_objects.dut.wcmp.config_wcmp_cli(invalid_value)
            assert "Error: No such command" in error_msg


def test_config_wcmp_by_redis_cli(cli_objects, setup_function, topology_obj, duthost):
    with allure.step("STEP1: Enable WCMP by redis-cli"):
        cli_objects.dut.wcmp.config_wcmp_redis_cli(WcmpConsts.WCMP_STATUS_REDIS_CLI_ENABLED)

    with allure.step("STEP2: Verify WCMP enabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP3: Verify bgp bandwidth community is configured in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config

    with allure.step("STEP4: Disable WCMP by redis-cli"):
        cli_objects.dut.wcmp.config_wcmp_redis_cli(WcmpConsts.WCMP_STATUS_REDIS_CLI_DISABLED)

    with allure.step("STEP5: Verify WCMP disabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_DISABLED

    with allure.step("STEP6: Verify bgp bandwidth community does not exist in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG not in frr_bgp_config


def test_wcmp_no_link_failure(cli_objects, setup_function, topology_obj, ha_obj, interfaces):
    with allure.step("STEP1: Enable WCMP"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with (allure.step(f"STEP2: Verify the weight value is {WcmpConsts.WEIGHT_VALUE_50}")):
        interface_weights = {**dict.fromkeys([interfaces.ha_dut_1, interfaces.ha_dut_2], WcmpConsts.WEIGHT_VALUE_50)}
        WcmpHelper.get_route_and_verify_weight(ha_obj, WcmpConsts.HB_ADVERTISED_ROUTE, interface_weights)

    with allure.step("STEP3: Verify traffic forwarding success when WCMP is enabled"):
        WcmpHelper.send_recv_traffic(topology_obj, interfaces)

    with allure.step("STEP4: Disable WCMP"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_DISABLED)

    with allure.step(f"STEP5: Verify the weight value is {WcmpConsts.WEIGHT_VALUE_DEFAULT}"):
        interface_weights = {**dict.fromkeys([interfaces.ha_dut_1, interfaces.ha_dut_2], WcmpConsts.WEIGHT_VALUE_DEFAULT)}
        WcmpHelper.get_route_and_verify_weight(ha_obj, WcmpConsts.HB_ADVERTISED_ROUTE, interface_weights)


def test_interface_flap(cli_objects, setup_function, topology_obj, duthost, interfaces, ha_obj):
    with allure.step("STEP1: Enable WCMP and verify status"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step(f"STEP2: DUT interface flap {WcmpConsts.INTERFACE_FLAP_COUNT} times"):
        sonic_ports_flap(cli_objects.dut, [interfaces.dut_ha_1], flap_count=WcmpConsts.INTERFACE_FLAP_COUNT)

    with allure.step(f"STEP3: Verify the weight value of each link is {WcmpConsts.WEIGHT_VALUE_50}"):
        interface_weights = {**dict.fromkeys([interfaces.ha_dut_1, interfaces.ha_dut_2], WcmpConsts.WEIGHT_VALUE_50)}
        WcmpHelper.get_route_and_verify_weight(ha_obj, WcmpConsts.HB_ADVERTISED_ROUTE, interface_weights)

    with allure.step("STEP4: Verify traffic forwarding success after interface flap"):
        WcmpHelper.send_recv_traffic(topology_obj, interfaces)


def test_wcmp_status_flap(cli_objects, setup_function, topology_obj, duthost, interfaces, ha_obj):
    with allure.step("STEP1: Enable WCMP and verify status"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP2: Verify bgp bandwidth community config is config in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config

    with allure.step(f"STEP3: Verify the weight value is {WcmpConsts.WEIGHT_VALUE_50} before flap"):
        interface_weights = {**dict.fromkeys([interfaces.ha_dut_1, interfaces.ha_dut_2], WcmpConsts.WEIGHT_VALUE_50)}
        WcmpHelper.get_route_and_verify_weight(ha_obj, WcmpConsts.HB_ADVERTISED_ROUTE, interface_weights)

    with allure.step(f"STEP4: WCMP status flap {WcmpConsts.WCMP_STATUS_FLAP_COUNT} times"):
        for _ in range(WcmpConsts.WCMP_STATUS_FLAP_COUNT):
            cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_DISABLED)
            cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)

    with allure.step("STEP5: Verify WCMP enabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP6: Verify bgp bandwidth community is configured in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config

    with allure.step(f"STEP7: Verify the weight value is {WcmpConsts.WEIGHT_VALUE_50} after flap"):
        interface_weights = {**dict.fromkeys([interfaces.ha_dut_1, interfaces.ha_dut_2], WcmpConsts.WEIGHT_VALUE_50)}
        WcmpHelper.get_route_and_verify_weight(ha_obj, WcmpConsts.HB_ADVERTISED_ROUTE, interface_weights)

    with allure.step("STEP8: Verify traffic forwarding success after WCMP status flap"):
        WcmpHelper.send_recv_traffic(topology_obj, interfaces)


@pytest.mark.parametrize("reboot_type", WcmpConsts.REBOOT_TYPE)
def test_dut_reboot(cli_objects, setup_function, topology_obj, reboot_type):
    with allure.step("STEP1: Enable WCMP and verify status"):
        cli_objects.dut.wcmp.config_wcmp_cli(WcmpConsts.WCMP_STATUS_ENABLED)
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP2: Verify bgp bandwidth community is configured in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config

    with allure.step("STEP3: DUT reboot"):
        logger.info(f'Starting {reboot_type}')
        cli_objects.dut.general.save_configuration()
        cli_objects.dut.general.reboot_reload_flow(r_type=reboot_type, topology_obj=topology_obj)

    with allure.step("STEP4: Verify WCMP still enabled"):
        wcmp_status = cli_objects.dut.wcmp.get_wcmp_status()
        assert wcmp_status == WcmpConsts.WCMP_STATUS_ENABLED

    with allure.step("STEP5: Verify bgp bandwidth community config still exist in FRR"):
        frr_bgp_config = cli_objects.dut.wcmp.get_frr_bgp_config()
        assert WcmpConsts.BGP_BANDWIDTH_COMMUNITY_CONFIG in frr_bgp_config


def test_wcmp_config_reflect_in_syslog(cli_objects, setup_function, duthost, loganalyzer):
    with allure.step("STEP1: Config WCMP by redis-cli with invalid parameter"):
        cli_objects.dut.wcmp.config_wcmp_redis_cli(WcmpConsts.WCMP_STATUS_REDIS_CLI_INVALID)
        if loganalyzer:
            for dut in loganalyzer:
                ignoreRegex = [r".*ERR bgp#bgpcfgd: WCMP: invalid value.*"]
                loganalyzer[dut].ignore_regex.extend(ignoreRegex)

    with allure.step("STEP2: Verify error config info reflect in syslog"):
        WcmpHelper.verify_wcmp_config_error_info(duthost, WcmpConsts.WCMP_STATUS_REDIS_CLI_INVALID)
