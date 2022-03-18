"""

conftest.py

Defines the methods and fixtures which will be used by pytest for only canonical setups.

"""

import pytest
import os
import yaml
import logging
from dotted_dict import DottedDict

from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.constants.constants import PytestConst

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def show_version(cli_objects):
    """
    Print show version output to logs
    :param cli_objects: cli_objects fixture
    """
    cli_objects.dut.general.show_version()


@pytest.fixture(scope='session')
def engines(topology_obj):
    engines_data = DottedDict()
    engines_data.dut = topology_obj.players['dut']['engine']
    engines_data.ha = topology_obj.players['ha']['engine']
    engines_data.hb = topology_obj.players['hb']['engine']
    return engines_data


@pytest.fixture(scope='session')
def cli_objects(topology_obj):
    cli_obj_data = DottedDict()
    cli_obj_data.dut = topology_obj.players['dut']['cli']
    cli_obj_data.ha = topology_obj.players['ha']['cli']
    cli_obj_data.hb = topology_obj.players['hb']['cli']
    return cli_obj_data


@pytest.fixture(scope='session')
def interfaces(topology_obj):
    interfaces_data = DottedDict()
    interfaces_data.ha_dut_1 = topology_obj.ports['ha-dut-1']
    interfaces_data.ha_dut_2 = topology_obj.ports['ha-dut-2']
    interfaces_data.hb_dut_1 = topology_obj.ports['hb-dut-1']
    interfaces_data.hb_dut_2 = topology_obj.ports['hb-dut-2']
    interfaces_data.dut_ha_1 = topology_obj.ports['dut-ha-1']
    interfaces_data.dut_ha_2 = topology_obj.ports['dut-ha-2']
    interfaces_data.dut_hb_1 = topology_obj.ports['dut-hb-1']
    interfaces_data.dut_hb_2 = topology_obj.ports['dut-hb-2']
    return interfaces_data


@pytest.fixture(scope='session')
def ha_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-1
    """
    return LinuxMacCli(engine=engines.ha).get_mac_address_for_interface(interfaces.ha_dut_1)


@pytest.fixture(scope='session')
def ha_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-2
    """
    return LinuxMacCli(engine=engines.ha).get_mac_address_for_interface(interfaces.ha_dut_2)


@pytest.fixture(scope='session')
def hb_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-1
    """
    return LinuxMacCli(engine=engines.hb).get_mac_address_for_interface(interfaces.hb_dut_1)


@pytest.fixture(scope='session')
def hb_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-2
    """
    return LinuxMacCli(engine=engines.hb).get_mac_address_for_interface(interfaces.hb_dut_2)


@pytest.fixture(scope='session')
def dut_ha_1_mac(engines, cli_objects, topology_obj):
    """
    Pytest fixture which are returning mac address for link: dut-ha-1
    """
    return cli_objects.dut.mac.get_mac_address_for_interface(topology_obj.ports['dut-ha-1'])


@pytest.fixture(scope='session')
def dut_hb_2_mac(engines, cli_objects, topology_obj):
    """
    Pytest fixture which are returning mac address for link: dut-hb-2
    """
    return cli_objects.dut.mac.get_mac_address_for_interface(topology_obj.ports['dut-hb-2'])


@pytest.fixture(scope='session', autouse=True)
def simx_disable_counters(is_simx, engines, cli_objects, topology_obj, sonic_version):
    """
    Pytest fixture which disable counters on SIMX workaround for issue: https://redmine.mellanox.com/issues/2807805
    """
    if is_simx:
        if '202012' not in sonic_version:
            counterpoll_status_dict = cli_objects.dut.counterpoll.parse_counterpoll_show(engines.dut)
            for counter, value in counterpoll_status_dict.items():
                if value['Status'] == 'enable':
                    cli_objects.dut.counterpoll.disable_counterpoll(engines.dut)
                    cli_objects.dut.general.reload_flow(engines.dut, topology_obj=topology_obj, reload_force=True)
                    break


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
def expected_cpu_usage_dict(platform, sonic_branch):
    """
    Pytest fixture which used to return the expected cpu usage dictionary
    :param platform: platform fixture
    :param sonic_branch: sonic branch fixture
    :return: expected cpu usage dictionary
    """
    expected_cpu_usage_file = "expected_cpu_usage.yaml"
    return get_expected_cpu_or_ram_usage_dict(expected_cpu_usage_file, sonic_branch, platform)


@pytest.fixture(scope='session')
def expected_ram_usage_dict(platform, sonic_branch):
    """
    Pytest fixture which used to return the expected ram usage dictionary
    :param platform: platform fixture
    :param sonic_branch: sonic branch fixture
    :return: expected ram usage dictionary
    """
    expected_ram_usage_file = "expected_ram_usage.yaml"
    return get_expected_cpu_or_ram_usage_dict(expected_ram_usage_file, sonic_branch, platform)


@pytest.fixture(scope='session')
def platform(platform_params):
    """
    get the platform value from the hwsku
    :param platform_params: platform_params fixture. Example of platform_params.hwsku: Mellanox-SN3800-D112C8
    """
    platform_index = 1
    return platform_params.hwsku.split('-')[platform_index]


def get_expected_cpu_or_ram_usage_dict(expected_cpu_or_ram_usage_file, sonic_branch, platform):
    """
    Get the expected cpu or ram usage dictionary
    :param expected_cpu_or_ram_usage_file: yaml file name
    :param sonic_branch: sonic branch
    :param platform: platform
    :return: expected cpu or ram usage dictionary
    """
    file_folder = "push_build_tests/system/"
    current_folder = os.path.dirname(__file__)
    expected_cpu_or_ram_usage_file_path = os.path.join(current_folder, file_folder, expected_cpu_or_ram_usage_file)
    with open(expected_cpu_or_ram_usage_file_path) as raw_data:
        expected_cpu_or_ram_usage_dict = yaml.load(raw_data, Loader=yaml.FullLoader)
    default_branch = "master"
    branch = sonic_branch if sonic_branch in expected_cpu_or_ram_usage_dict.keys() else default_branch
    expected_cpu_or_ram_usage_dict = expected_cpu_or_ram_usage_dict[branch][platform]
    return expected_cpu_or_ram_usage_dict
