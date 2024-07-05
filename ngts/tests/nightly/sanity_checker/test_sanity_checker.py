import allure
import logging
import pytest

from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from ngts.helpers.secure_boot_helper import SonicSecureBootHelper

pytestmark = [
    pytest.mark.disable_loganalyzer
]


logger = logging.getLogger()

POSSIBLE_CPLD_LIST = ['CPLD1', 'CPLD2', 'CPLD3', 'CPLD4']
NOT_DEFINED_CPLD_DEVICES_LIST = ['MSN2010', 'SN4800']


@pytest.mark.sanity_checker_common
def test_cpld_version_check(topology_obj, engines, platform_params, cli_objects):
    """
    This test validates that the CPLD version(s) deployed on the dut are the latest approved ones,
    as defined in the firmware.json versions file. If not, try it install the latest one.
    If case fail,
        The following actions will be handled in analyze_sanity_checker_result_and_take_action.py
        1. For sonic_tigon_r-tigon-15, sonic_anaconda_r-anaconda-15, the regression will be stopped by mars
        2. For the remaining setups,
           we will raise the failed case information in the allure report and disable bug handler tool
    :param engines: engines fixture
    :param platform_params: platform_params fixture
    """
    with allure.step('Getting info about the CPLD component from firmware.json'):
        cpld_component_data = None
        defined_cpld = None
        for cpld in POSSIBLE_CPLD_LIST:
            try:
                cpld_component_data = SonicSecureBootHelper.get_component_data(platform_params, cpld)
                defined_cpld = cpld
                break
            except Exception as e:
                logger.info(e)
                pass
        device_with_not_defined_cpld = platform_params.filtered_platform.upper() in NOT_DEFINED_CPLD_DEVICES_LIST
        assert device_with_not_defined_cpld or (defined_cpld and cpld_component_data), \
            "Failed to get the data for any CPLD from the firmware.json"

    with allure.step('Getting info about CPLD from dut'):
        component_versions_dict = get_info_about_current_components_version_dict(engines.dut)

    with allure.step(f'Checking CPLD version for: {defined_cpld}'):
        if not device_with_not_defined_cpld:
            _, latest_cpld_ver = SonicSecureBootHelper.get_latest_expected_cpld(cpld_component_data, defined_cpld)
            current_cpld_ver = component_versions_dict[defined_cpld]
            if current_cpld_ver != latest_cpld_ver:
                with allure.step(f'Restore CPLD to {latest_cpld_ver}'):
                    logger.info(f"Restore CPLD to the expected one:{latest_cpld_ver}")
                    SonicSecureBootHelper.restore_cpld(cli_objects, engines, topology_obj, platform_params)
                with allure.step(f"Check if the cpld version is updated to {latest_cpld_ver}"):
                    engines.dut.disconnect()
                    component_versions_dict = get_info_about_current_components_version_dict(engines.dut)
                    current_cpld_ver = component_versions_dict[defined_cpld]
                    assert current_cpld_ver == latest_cpld_ver, \
                        f'Current {defined_cpld} version: {current_cpld_ver} is not latest: {latest_cpld_ver}'


@pytest.mark.sanity_checker_common
def test_device_asic_check(engines, platform_params):
    """
    This test is verify that device asic status is ok.
    If case fail, the consequent regression steps will be stopped by mars
    """
    # Todo
    pass


@pytest.mark.sanity_checker_community
def test_cable_connection_between_dut_and_fanout_check(engines, platform_params):
    """
    This test is verify that cable connection between dut and fanout is ok.
    If case fail, the consequent regression steps will be stopped by mars
    """
    # Todo
    pass


@pytest.mark.sanity_checker_common
def test_bgp_session_status_check(engines, platform_params):
    """
    This test is verify that bgp session status is ok.
    If case fail, the consequent regression steps will be stopped by mars
    """
    # Todo
    pass


@pytest.mark.sanity_checker_canonical
def test_cable_connection_for_canonical_check(engines, platform_params):
    """
    This test is verify that the cable connection for canonical setup is ok.
    If case fail, the consequent regression steps will be stopped by mars
    """
    # Todo
    pass


@pytest.mark.sanity_checker_common
def test_fan_status_check(engines, platform_params):
    """
    This test is verify that the fan status is ok.
    If case fail, we will raise the failed case information in the allure report and disable bug handler tool
    """
    # Todo
    pass


@pytest.mark.sanity_checker_common
def test_more_then_2_fan_status_wrong_check(engines, platform_params):
    """
    This test is verify more than 2 fan status are not ok
    If case fail, the consequent regression steps will be stopped by mars
    """
    # Todo
    pass


@pytest.mark.sanity_checker_common
def test_psu_status_check(engines, platform_params):
    """
    This test is verify the psu status is ok or not
    If case fail, we will raise the failed case information in the allure report and disable bug handler tool
    """
    # Todo
    pass


def get_info_about_current_components_version_dict(engine):
    """
    Get dictionary with component name as key and version as value
    :param engine: dut engine
    :return: dictionary with component name as key and version as value
    """

    fwutil_show_status_output = engine.run_cmd('sudo fwutil show status')
    fwutil_show_status_dict = generic_sonic_output_parser(fwutil_show_status_output)
    component_names_list = fwutil_show_status_dict[0]['Component']
    component_versions_list = fwutil_show_status_dict[0]['Version']
    component_versions_dict = {}
    for component, version in zip(component_names_list, component_versions_list):
        component_versions_dict[component] = version

    return component_versions_dict
