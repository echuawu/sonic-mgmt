"""

conftest.py

Defines the methods and fixtures which will be used by pytest,
NOTE: Add here only fixtures and methods that can be used for canonical and community setups alike.

if your methods only apply for canonical setups please add them in ngts/tests/conftest.py

"""

import pytest
import logging
import re
import json
from dotted_dict import DottedDict

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli
from ngts.cli_wrappers.linux.linux_cli import LinuxCli
from ngts.constants.constants import SonicConst, PytestConst
from ngts.tools.infra import get_platform_info
from ngts.tests.nightly.app_extension.app_extension_helper import APP_INFO
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli

logger = logging.getLogger()

pytest_plugins = ('ngts.tools.sysdumps',
                  'ngts.tools.custom_skipif.CustomSkipIf',
                  'ngts.tools.loganalyzer',
                  'ngts.tools.infra',
                  'pytester',
                  'ngts.tools.allure_report',
                  'ngts.tools.mars_test_cases_results'
                  )


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest options')
    parser.addoption('--setup_name', action='store', required=True, default=None,
                     help='Setup name, example: sonic_tigris_r-tigris-06')
    parser.addoption('--base_version', action='store', default=None, help='Path to base SONiC version')
    parser.addoption('--target_version', action='store', default=None, help='Path to target SONiC version')
    parser.addoption('--wjh_deb_url', action='store', default=None, help='URL path to WJH deb package')
    parser.addoption("--session_id", action="store", default=None, help="Number of mars session id.")
    parser.addoption("--mars_key_id", action="store", default=None, help="mars key id.")
    parser.addoption("--tech_support_duration", action="store", default=None, help="duration of tech support for test")
    parser.addoption(PytestConst.run_config_only_arg, action='store_true', help='If set then only the configuration '
                                                                                'part defined in the push_build '
                                                                                'conftest will be executed')
    parser.addoption(PytestConst.run_test_only_arg, action='store_true', help='If set then only the test(push_build) '
                                                                              'will be executed')
    parser.addoption(PytestConst.run_cleanup_only_arg, action='store_true', help='If set then only the cleanup part '
                                                                                 'defined in the push_build conftest '
                                                                                 'will be executed')
    parser.addoption('--app_extension_dict_path', action='store', required=False, default=None,
                     help='''Provide path to application extensions json file.
                          'Example of content: {"p4-sampling":"harbor.mellanox.com/sonic-p4/p4-sampling:0.2.0",
                                      "what-just-happened":"harbor.mellanox.com/sonic-wjh/docker-wjh:1.0.1"} ''')


@pytest.fixture(scope="package")
def app_extension_dict_path(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: app_extension_dict
    """
    return request.config.getoption('--app_extension_dict_path')


@pytest.fixture(scope="session")
def base_version(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: base_version argument value
    """
    return request.config.getoption('--base_version')


@pytest.fixture(scope="session")
def target_version(request):
    """
    Method for getting target version from pytest arguments
    :param request: pytest builtin
    :return: target_version argument value
    """
    return request.config.getoption('--target_version')


@pytest.fixture(scope="session")
def wjh_deb_url(request):
    """
    Method for getting what-just-happend deb file URL from pytest arguments
    :param request: pytest builtin
    :return: wjh_deb_url argument value
    """
    return request.config.getoption('--wjh_deb_url')


@pytest.fixture(scope='session')
def setup_name(request):
    """
    Method for get setup name from pytest arguments
    :param request: pytest buildin
    :return: setup name
    """
    return request.config.getoption('--setup_name')


@pytest.fixture(scope='session', autouse=True)
def topology_obj(setup_name):
    """
    Fixture which create topology object before run tests and doing cleanup for ssh engines after test executed
    :param setup_name: example: sonic_tigris_r-tigris-06
    """
    logger.debug('Creating topology object')
    topology = get_topology_by_setup_name(setup_name, slow_cli=False)
    update_topology_with_cli_class(topology)
    yield topology
    logger.debug('Cleaning-up the topology object')
    for player_name, player_attributes in topology.players.items():
        player_attributes['engine'].disconnect()


def update_topology_with_cli_class(topology):
    # TODO: determine player type by topology attribute, rather than alias
    for player_key, player_info in topology.players.items():
        if player_key == 'dut':
            player_info['cli'] = SonicCli()
        else:
            player_info['cli'] = LinuxCli()


@pytest.fixture(scope='session')
def show_platform_summary(topology_obj):
    return get_platform_info(topology_obj)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook which are executed in all phases: Setup, Call, Teardown
    :param item: pytest buildin
    :param call: pytest buildin
    """
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope='session')
def dut_mac(engines):
    """
    Fixture which get DUT mac address from DUT config_db.json file
    :param engines: engines fixture
    :return: dut mac address
    """
    logger.info('Getting DUT mac address')
    config_db = SonicGeneralCli.get_config_db(engines.dut)
    dut_mac = config_db.get('DEVICE_METADATA').get('localhost').get('mac')
    logger.info('DUT mac address is: {}'.format(dut_mac))
    return dut_mac


@pytest.fixture(scope='session')
def chip_type(topology_obj):
    chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']
    return chip_type


@pytest.fixture(scope='session')
def sonic_version(engines):
    """
    Pytest fixture which are returning current SONiC installed version
    :param engines: dictionary with available engines
    :return: string with current SONiC version
    """
    show_version_output = engines.dut.run_cmd('sudo show version')
    sonic_ver = re.search(r'SONiC\sSoftware\sVersion:\s(.*)', show_version_output, re.IGNORECASE).group(1)
    return sonic_ver


@pytest.fixture(scope='session')
def platform_params(show_platform_summary, setup_name):
    """
    Method for getting all platform related data
    :return: dictionary with platform data
    """
    platform_data = DottedDict()
    platform_data.platform = show_platform_summary['platform']
    platform_data.filtered_platform = re.search(r"(msn\d{4}c|msn\d{4}|sn\d{4})", show_platform_summary['platform'], re.IGNORECASE).group(1)
    platform_data.hwsku = show_platform_summary['hwsku']
    platform_data.setup_name = setup_name
    platform_data.asic_type = show_platform_summary["asic_type"]
    platform_data.asic_count = show_platform_summary["asic_count"]
    return platform_data


@pytest.fixture(scope="session")
def upgrade_params(base_version, target_version, wjh_deb_url):
    """
    Method for getting all upgrade related parameters
    :return: dictionary with upgrade parameters
    """
    upgrade_data = DottedDict()

    upgrade_data.base_version = base_version
    upgrade_data.target_version = target_version
    upgrade_data.wjh_deb_url = wjh_deb_url
    upgrade_data.is_upgrade_required = False
    if base_version and target_version:
        upgrade_data.is_upgrade_required = True
    else:
        logger.info('Either one or all the upgrade arguments is missing, skipping the upgrade flow')
    return upgrade_data


@pytest.fixture(scope="session")
def shared_params():
    shared_dict = DottedDict()
    shared_dict.app_ext_is_app_ext_supported = False
    shared_dict.app_ext_app_name = APP_INFO["name"]
    shared_dict.app_ext_app_repository_name = APP_INFO["repository"]
    shared_dict.app_ext_version = APP_INFO["shut_down"]["version"]

    return shared_dict


@pytest.fixture(scope="session")
def players(topology_obj):
    return topology_obj.players


@pytest.fixture(scope="session")
def is_simx(platform_params):
    is_simx_setup = False
    if re.search('simx', platform_params.setup_name):
        is_simx_setup = True
    return is_simx_setup


def cleanup_last_config_in_stack(cleanup_list):
    """
    Execute the last function in the cleanup stack
    :param cleanup_list: list with functions to cleanup
    :return: None
    """
    func, args = cleanup_list.pop()
    func(*args)
