import logging
import time
import pytest

from ngts.nvos_constants.constants_nvos import ApiType, PlatformConsts, HealthConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


def clear_platform_ps_redundancy(platform, engines):
    """
    Method to unset the platform ps-redundancy policy type
    :param platform:  Platform object
    :param engines: Engines object
    """

    with allure.step('Run unset platform ps-redundancy command and apply config'):
        platform.ps_redundancy.unset(apply=True, dut_engine=engines.dut).verify_result()


@pytest.mark.platform
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_show_platform_ps_redundancy(test_api):
    """nv show platform ps-redundancy"""
    TestToolkit.tested_api = test_api

    with allure.step("Create Platform object"):
        platform = Platform()

    with allure.step("Check show platform ps-redundancy output"):
        output = OutputParsingTool.parse_json_str_to_dictionary(platform.ps_redundancy.show()).get_returned_value()
        ValidationTool.verify_field_exist_in_json_output(output,
                                                         [PlatformConsts.PS_REDUNDANCY_POLICY,
                                                          PlatformConsts.PS_REDUNDANCY_MIN_REQ]).verify_result()


@pytest.mark.platform
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_set_platform_ps_redundancy(engines, test_api):
    """nv set platform ps-redundancy"""
    TestToolkit.tested_api = test_api

    with allure.step("Create Platform object"):
        platform = Platform()

    try:
        for policy_type in PlatformConsts.PS_REDUNDANCY_POLICY_TYPE:
            with allure.step("Set platform ps-redundancy to {} and verify in show output".format(policy_type)):
                platform.ps_redundancy.set(PlatformConsts.PS_REDUNDANCY_POLICY, policy_type,
                                           apply=True, dut_engine=engines.dut)
                output = OutputParsingTool.parse_json_str_to_dictionary(platform.ps_redundancy.show()).\
                    get_returned_value()
                ValidationTool.verify_field_value_in_output(output, PlatformConsts.PS_REDUNDANCY_POLICY,
                                                            policy_type).verify_result()

        with allure.step("Unset platform ps-redundancy and verify show command shows default policy"):
            platform.ps_redundancy.unset(PlatformConsts.PS_REDUNDANCY_POLICY, apply=True, dut_engine=engines.dut).\
                verify_result()

            # To Do : Commenting the below code as the default policy is not defined yet.
            # output=OutputParsingTool.parse_json_str_to_dictionary(platform.ps_redundancy.show()).get_returned_value()
            # ValidationTool.verify_field_value_in_output(output, PlatformConsts.PS_REDUNDANCY_POLICY,
            #                                            PlatformConsts.PS_REDUNDANCY_POLICY_TYPE_DEF).verify_result()

    finally:
        clear_platform_ps_redundancy(platform, engines)


@pytest.mark.platform
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_platform_ps_redundancy_functionality(engines, devices, test_api):
    TestToolkit.tested_api = test_api

    with allure.step("Create Platform object"):
        platform = Platform()

    with allure.step("Create System object"):
        system = System()

    try:
        with allure.step("Verify all PSUs are up"):
            output = OutputParsingTool.parse_json_str_to_dictionary(platform.environment.psu.show()).\
                get_returned_value()
            for psu in output:
                assert output[psu][PlatformConsts.PSU_STATE] == "ok", "State of {} is not ok".format(psu)

        with allure.step("Verify health is good and no issues are found"):
            system_health_check(system, HealthConsts.OK)

        with allure.step("Get the minimum number of PSUs required"):
            output = OutputParsingTool.parse_json_str_to_dictionary(platform.ps_redundancy.show()). \
                get_returned_value()
            assert PlatformConsts.PS_REDUNDANCY_MIN_REQ in output, "Platform ps-redundancy show does not show min-req"
            min_required = int(output[PlatformConsts.PS_REDUNDANCY_MIN_REQ])
            required_for_redundancy = {PlatformConsts.PS_REDUNDANCY_NO: min_required,
                                       PlatformConsts.PS_REDUNDANCY_GRID: min_required * 2,
                                       PlatformConsts.PS_REDUNDANCY_PS: min_required + 1}
        for policy_type in PlatformConsts.PS_REDUNDANCY_POLICY_TYPE:
            with allure.step("Set platform ps-redundancy to {} and verify in functionality".format(policy_type)):
                platform.ps_redundancy.set(PlatformConsts.PS_REDUNDANCY_POLICY, policy_type, apply=True,
                                           dut_engine=engines.dut)
                min_for_redundancy = required_for_redundancy[policy_type]
                platform_ps_redundancy_functionality(engines, system, min_for_redundancy)
                logger.info("Policy {} is validated".format(policy_type))

    finally:
        clear_platform_ps_redundancy(platform, engines)


def platform_ps_redundancy_functionality(engines, system, min_for_redundancy):
    try:
        with allure.step("Deteriorate PSUs till redundancy threshold"):
            skip_str = PlatformConsts.PS_REBOOT_PSU_SKIP_STR
            psu_good_state = str(list(range(1, min_for_redundancy + 1))).replace('[', '').replace(']', '').replace(' ', '')
            psu_bad_state = str(list(range(1, min_for_redundancy))).replace('[', '').replace(']', '').replace(' ', '')
            skip_str_good = skip_str + psu_good_state + ' '
            skip_str_bad = skip_str + psu_bad_state + ' '
            platform_control_psu(engines, skip_str_good, 'off')
            # Wait for PSU states to update
            time.sleep(10)
            system_health_check(system, HealthConsts.OK)

        with allure.step("Deteriorate one more PSU than redundancy threshold to fail PS redundancy"):
            platform_control_psu(engines, skip_str_bad, 'off')

        # Need to consult with design regarding below behaviour
        # with allure.step("Validate System health is not OK and issues are found"):
        #    system_health_check(system, HealthConsts.NOT_OK)

    finally:
        with allure.step("Recover PSUs"):
            platform_control_psu(engines, '', 'on')
            # Wait for PSU states to update
            time.sleep(10)

        with allure.step("Validate System health is OK and issues are not seen"):
            system_health_check(system, HealthConsts.OK)


def platform_control_psu(engines, skip_str, psu_state):
    player = engines['sonic_mgmt']
    with allure.step("Get the hostname of the system"):
        hostname = engines.dut.run_cmd('hostname')
    with allure.step("Switch {} the PSUs using reboot script".format(psu_state)):
        reboot_cmd = skip_str + '/auto/mswg/utils/bin/rreboot ' + hostname + ' ' + psu_state
        player.run_cmd(reboot_cmd)


def system_health_check(system, check_status):
    output = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()
    status = output[HealthConsts.STATUS]
    issues = output[HealthConsts.ISSUES]
    assert status == check_status, "System Health Status is {} instead of {}".format(status, check_status)
    if check_status is HealthConsts.OK:
        assert len(issues) == 0, "Unexpected issue found: {}".format(issues)
    else:
        assert len(issues) != 0, "Issues were expected in show health but not found"
