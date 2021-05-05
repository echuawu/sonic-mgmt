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
from ngts.tools.allure_report.allure_server import AllureServer
from ngts.tools.skip_test.skip import ngts_skip
from ngts.constants.constants import SonicConst, PytestConst

logger = logging.getLogger()

pytest_plugins = ('ngts.tools.sysdumps', 'ngts.tools.loganalyzer', 'ngts.tools.infra', 'pytester')


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
    parser.addoption(PytestConst.run_config_only_arg, action='store_true', help='If set then only the configuration '
                                                                                'part defined in the push_build '
                                                                                'conftest will be executed')
    parser.addoption(PytestConst.run_test_only_arg, action='store_true', help='If set then only the test(push_build) '
                                                                              'will be executed')
    parser.addoption(PytestConst.run_cleanup_only_arg, action='store_true', help='If set then only the cleanup part '
                                                                                 'defined in the push_build conftest '
                                                                                 'will be executed')


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
    try:
        show_platform_summary_dict = json.loads(
            topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['devdescription'])
    except json.decoder.JSONDecodeError:
        err_msg = 'NOGA Attribute Devdescription is empty! Fetched data: {}' \
                  ' It should look like: {"hwsku":"ACS-MSN3700","platform":' \
                  '"x86_64-mlnx_msn3700-r0"}'.format(
            topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['devdescription'])
        raise Exception(err_msg)
    return show_platform_summary_dict


@pytest.fixture(autouse=True)
def skip_test_according_to_ngts_skip(request, platform_params):
    """
    This fixture doing skip for test cases according to BUG ID in Redmine/GitHub or platform
    :param request: pytest buildin
    :param show_platform_summary: output for cmd 'show platform summary' from fixture show_platform_summary
    """
    skip_marker = 'ngts_skip'
    if request.node.get_closest_marker(skip_marker):
        rm_ticket_list = request.node.get_closest_marker(skip_marker).args[0].get('rm_ticket_list')
        github_ticket_list = request.node.get_closest_marker(skip_marker).args[0].get('github_ticket_list')
        platform_prefix_list = request.node.get_closest_marker(skip_marker).args[0].get('platform_prefix_list')
        operand = request.node.get_closest_marker(skip_marker).args[0].get('operand', 'or')

        ngts_skip(platform_params.platform, rm_ticket_list, github_ticket_list, platform_prefix_list, operand)


def pytest_runtest_setup(item):
    """
    Pytest hook - see https://docs.pytest.org/en/stable/reference.html#pytest.hookspec.pytest_runtest_setup
    """
    ngts_skip_test_change_fixture_execution_order(item)


def ngts_skip_test_change_fixture_execution_order(item):
    """
    The purpose of this method is to change the order of fixtures execution - skip test by ngts logic should be run first
    Otherwise autouse fixtures of ignored tests will be running, even if the test case is skipped.
    :param item: pytest buildin
    """
    ngts_skip_fixture = item.fixturenames.pop(item.fixturenames.index('skip_test_according_to_ngts_skip'))
    if ngts_skip_fixture:
        item.fixturenames.insert(0, ngts_skip_fixture)


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook which are executed after all tests before exist from program
    :param session: pytest buildin
    :param exitstatus: pytest buildin
    """
    if not session.config.getoption("--collectonly"):
        allure_server_ip = '10.215.11.120'
        allure_server_port = '5050'
        allure_report_dir = session.config.known_args_namespace.allure_report_dir
        try:
            AllureServer(allure_server_ip, allure_server_port, allure_report_dir).generate_allure_report()
        except Exception as err:
            logger.error('Failed to upload allure report to server. Allure report not available. '
                         '\nError: {}'.format(err))


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
    config_db_json = engines.dut.run_cmd(cmd='cat {}'.format(SonicConst.CONFIG_DB_JSON_PATH), print_output=False)
    config_db = json.loads(config_db_json)
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
    platform_data.hwsku = show_platform_summary['hwsku']
    platform_data.setup_name = setup_name
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
def players(topology_obj):
    return topology_obj.players


def cleanup_last_config_in_stack(cleanup_list):
    """
    Execute the last function in the cleanup stack
    :param cleanup_list: list with functions to cleanup
    :return: None
    """
    func, args = cleanup_list.pop()
    func(*args)
