import allure
import logging
import os

from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from ngts.helpers.json_file_helper import extract_fw_data

logger = logging.getLogger()

POSSIBLE_CPLD_LIST = ['CPLD1', 'CPLD2', 'CPLD3']


def test_cpld_version_check(engines, platform_params):
    """
    This test validates that the CPLD version(s) deployed on the dut are the latest approved ones,
    as defined in the firmware.json versions file.
    :param engines: engines fixture
    :param platform_params: platform_params fixture
    """
    with allure.step('Getting info about platform components from firmware.json'):
        path_to_current_test_folder = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
        fw_pkg_path = f'{path_to_current_test_folder}/updated-fw.tar.gz'
        fw_data = extract_fw_data(fw_pkg_path)
        current_platform = platform_params.filtered_platform.upper()
        try:
            chassis_components_dict = fw_data['chassis'][current_platform]['component']
        except KeyError as err:
            err_mgs = f'Can not find components list for platform: {current_platform}. Got err: {err}'
            raise KeyError(err_mgs)

    with allure.step('Getting info about CPLD from dut'):
        component_versions_dict = get_info_about_current_components_version_dict(engines.dut)

    for component_name, component_data in chassis_components_dict.items():
        if component_name in POSSIBLE_CPLD_LIST:
            with allure.step(f'Checking CPLD version for: {component_name}'):
                latest_component_ver = get_latest_expected_cpld_version(component_name, component_data)
                current_component_ver = component_versions_dict[component_name]
                assert current_component_ver == latest_component_ver, \
                    f'Current {component_name} version: {current_component_ver} is not latest: {latest_component_ver}'


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


def get_latest_expected_cpld_version(component_name, component_data):
    """
    Get latest expected CPLD version string
    :param component_name: name of component, example: CPLD2
    :param component_data: list, which contain dictionaries with component info
    :return: latest component version, example 'CPLD000162_REV1000'
    """
    with allure.step(f'Getting list of versions for {component_name} from firmware.json'):
        cplds_list = []
        for cpld_data in component_data:
            cplds_list.append(cpld_data['version'])

    with allure.step(f'Getting latest version for: {component_name} from firmware.json'):
        result_dict = {}
        for cpld in cplds_list:
            cpld_main_ver = int(cpld.split('_')[0].strip('CPLD'))
            cpld_minor_ver = int(cpld.split('_')[1].strip('REV'))
            cpld_int_value = cpld_main_ver + cpld_minor_ver
            result_dict[cpld_int_value] = cpld
        latest_component_ver_int = sorted(result_dict, reverse=True)[0]
        latest_component_ver = result_dict[latest_component_ver_int]

    return latest_component_ver
