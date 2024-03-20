"""

conftest.py

Defines the methods and fixtures which will be used by pytest for only canonical setups.

"""

import pytest
import os
import yaml
import logging

from deepdiff import DeepDiff
from ngts.constants.constants import PytestConst

logger = logging.getLogger()
RAM_SYNCD_USAGE_ASAN_COEFFICIENT = 4
CPU_SDK_USAGE_SIMX_COEFFICIENT = 6


@pytest.fixture(scope='session', autouse=True)
def get_dut_device_info(cli_objects):
    """
    Print show version output and running configuration to logs
    :param cli_objects: cli_objects fixture
    """
    cli_objects.dut.general.show_version()
    config_before_tests = cli_objects.dut.general.get_config_db_from_running_config()

    yield

    config_after_tests = cli_objects.dut.general.get_config_db_from_running_config()
    configs_diff = DeepDiff(config_before_tests, config_after_tests)

    new_items_added = configs_diff.get('dictionary_item_added')
    values_changed = configs_diff.get('values_changed')
    values_removed = configs_diff.get('dictionary_item_removed')

    logger.info(f'SONiC configuration diff before/after pytest session execution:\n'
                f'New items added: {new_items_added}\n'
                f'Values changed: {values_changed}\n'
                f'Values removed: {values_removed}\n')


@pytest.fixture(scope='session')
def run_config_only(request):
    """
    Method for get run_config_only from pytest arguments
    """
    return request.config.getoption(PytestConst.run_config_only_arg)


@pytest.fixture(scope='session')
def run_test_only(request):
    """
    Method for get run_test_only from pytest arguments
    """
    return request.config.getoption(PytestConst.run_test_only_arg)


@pytest.fixture(scope='session')
def run_cleanup_only(request):
    """
    Method for get run_cleanup_only from pytest arguments
    """
    return request.config.getoption(PytestConst.run_cleanup_only_arg)


@pytest.fixture(scope='session')
def expected_cpu_usage_dict(platform, sonic_branch, is_simx, chip_type):
    """
    Pytest fixture which used to return the expected cpu usage dictionary
    :param platform: platform fixture
    :param sonic_branch: sonic branch fixture
    :param is_simx: True if dut is a simx switch, else False
    :param chip_type: dut chip type
    :return: expected cpu usage dictionary
    """
    expected_cpu_usage_file = "expected_cpu_usage.yaml"
    return get_expected_cpu_or_ram_usage_dict(expected_cpu_usage_file, sonic_branch, platform,
                                              is_simx=is_simx, chip_type=chip_type)


@pytest.fixture(scope='session')
def expected_ram_usage_dict(platform, sonic_branch, is_sanitizer_image):
    """
    Pytest fixture which used to return the expected ram usage dictionary
    :param platform: platform fixture
    :param sonic_branch: sonic branch fixture
    :param is_sanitizer_image: True if dut has a sanitizer image, else False
    :return: expected ram usage dictionary
    """
    expected_ram_usage_file = "expected_ram_usage.yaml"
    return get_expected_cpu_or_ram_usage_dict(expected_ram_usage_file, sonic_branch,
                                              platform, is_sanitizer_image=is_sanitizer_image)


@pytest.fixture(scope='session')
def platform(platform_params):
    """
    get the platform value from the hwsku
    :param platform_params: platform_params fixture. Example of platform_params.hwsku: Mellanox-SN3800-D112C8
    """
    platform_index = 1
    return platform_params.hwsku.split('-')[platform_index]


def get_expected_cpu_or_ram_usage_dict(expected_cpu_or_ram_usage_file, sonic_branch, platform,
                                       is_sanitizer_image=False, is_simx=False, chip_type=None):
    """
    Get the expected cpu or ram usage dictionary
    :param expected_cpu_or_ram_usage_file: yaml file name
    :param sonic_branch: sonic branch
    :param platform: platform
    :param is_sanitizer_image: True if dut has a asan image, False otherwise
    :param is_simx: True if dut is a simx switch, else False
    :param chip_type: dut chip type
    :return: expected cpu or ram usage dictionary
    """
    current_folder = os.path.dirname(__file__)
    expected_cpu_or_ram_usage_file_path = os.path.join(current_folder, expected_cpu_or_ram_usage_file)
    with open(expected_cpu_or_ram_usage_file_path) as raw_data:
        expected_cpu_or_ram_usage_dict = yaml.load(raw_data, Loader=yaml.FullLoader)
    default_branch = "master"
    branch = sonic_branch if sonic_branch in expected_cpu_or_ram_usage_dict.keys() else default_branch
    expected_cpu_or_ram_usage_dict = expected_cpu_or_ram_usage_dict[branch][platform]
    update_ram_usage_for_sanitizer_image(expected_cpu_or_ram_usage_file, is_sanitizer_image,
                                         expected_cpu_or_ram_usage_dict)
    update_cpu_usage_for_simx(expected_cpu_or_ram_usage_file, is_simx,
                              chip_type, expected_cpu_or_ram_usage_dict)
    return expected_cpu_or_ram_usage_dict


def update_ram_usage_for_sanitizer_image(expected_cpu_or_ram_usage_file,
                                         is_sanitizer_image, expected_cpu_or_ram_usage_dict):
    """
    RAM usage for syncd on asan image is expected to be higher, that's why
    the fix is to update the threshold for syncd if it's a sanitizer image.
    :param expected_cpu_or_ram_usage_file: i.e, "expected_ram_usage.yaml" or "expected_cpu_usage.yaml"
    :param is_sanitizer_image: True if dut has a sanitizer image, else False
    :param expected_cpu_or_ram_usage_dict: a dictionary with expected ram usage/ cpu usage
    :return: none
    """
    if is_sanitizer_image and expected_cpu_or_ram_usage_file == "expected_ram_usage.yaml":
        expected_cpu_or_ram_usage_dict['syncd'] *= RAM_SYNCD_USAGE_ASAN_COEFFICIENT


def update_cpu_usage_for_simx(expected_cpu_or_ram_usage_file, is_simx, chip_type, expected_cpu_or_ram_usage_dict):
    """
    CPU usage for sx_sdk on SIMX spc3 setups is expected to be higher, that's why
    the fix is to update the threshold for sx_sdk if it's a simx and SPC3.
    :param expected_cpu_or_ram_usage_file: i.e, "expected_ram_usage.yaml" or "expected_cpu_usage.yaml"
    :param is_simx: True if dut is a simx switch, else False
    :param chip_type: dut chip type
    :param expected_cpu_or_ram_usage_dict: a dictionary with expected ram usage/ cpu usage
    :return: none
    """
    if is_simx and expected_cpu_or_ram_usage_file == "expected_cpu_usage.yaml" and chip_type == 'SPC3':
        expected_cpu_or_ram_usage_dict['sx_sdk'] *= CPU_SDK_USAGE_SIMX_COEFFICIENT
