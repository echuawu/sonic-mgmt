"""

conftest.py

Defines the methods and fixtures which will be used by pytest,
NOTE: Add here only fixtures and methods that can be used for canonical and community setups alike.

if your methods only apply for canonical setups please add them in ngts/tests/conftest.py

"""

import pytest
import logging
import re
import sys
import json
from dotted_dict import DottedDict

from ngts.tools.topology_tools.topology_by_setup import get_topology_by_setup_name_and_aliases
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli, SonicCliStub
from ngts.cli_wrappers.linux.linux_cli import LinuxCli, LinuxCliStub
from ngts.cli_wrappers.nvue.nvue_cli import NvueCli
from ngts.constants.constants import PytestConst, NvosCliTypes
from ngts.tools.infra import get_platform_info, get_devinfo, is_deploy_run
from ngts.tests.nightly.app_extension.app_extension_helper import APP_INFO
from ngts.helpers.sonic_branch_helper import get_sonic_branch, update_branch_in_topology, update_sanitizer_in_topology
from ngts.tools.allure_report.allure_report_attacher import add_fixture_end_tag, add_fixture_name, clean_stored_cmds_with_fixture_scope, update_fixture_scope_list, enable_record_cmds

logger = logging.getLogger()


def pytest_sessionstart(session):
    """Clear cached variables from previous pytest session"""

    session.config.cache.set(PytestConst.LA_DYNAMIC_IGNORES_LIST, None)
    session.config.cache.set(PytestConst.CUSTOM_SKIP_IF_DICT, None)
    session.config.cache.set(PytestConst.CUSTOM_TEST_SKIP_PLATFORM_TYPE, None)
    session.config.cache.set(PytestConst.CUSTOM_TEST_SKIP_BRANCH_NAME, None)


def pytest_collection(session):
    topology = get_topology_by_setup_name_and_aliases(session.config.option.setup_name, slow_cli=False)
    logger.debug('Get switch devdescription from Noga')
    switch_attributes = topology.players['dut']['attributes'].noga_query_data['attributes']
    devinfo = get_devinfo(switch_attributes)

    platform = json.loads(devinfo).get('platform')
    session.config.cache.set(PytestConst.CUSTOM_TEST_SKIP_PLATFORM_TYPE, platform)

    if is_deploy_run():
        # Required for prevent SSH attempts into DUT at the beginning of deploy image test(in case when device in ONIE)
        branch = 'master'
        session.config.cache.set(PytestConst.IS_SANITIZER_IMAGE, False)
    else:
        branch = get_sonic_branch(topology)

    session.config.cache.set(PytestConst.CUSTOM_TEST_SKIP_BRANCH_NAME, branch)


pytest_plugins = ('ngts.tools.sysdumps',
                  'ngts.tools.conditional_mark',
                  'ngts.tools.loganalyzer',
                  'ngts.tools.infra',
                  'pytester',
                  'ngts.tools.allure_report',
                  'ngts.tools.mars_test_cases_results',
                  'ngts.tools.loganalyzer_dynamic_errors_ignore.la_dynamic_errors_ignore',
                  'tests.common.plugins.collect_test_data_to_sql'
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
    parser.addoption("--test_name", action="store", default=None,
                     help="a parameter for script check_and_store_sanitizer_dump.py, "
                          "will check for sanitizer failures and store dump under test name")
    parser.addoption("--send_mail", action="store", default=False,
                     help="a boolean parameter for script check_and_store_sanitizer_dump.py, "
                          "will send mail with the sanitizer failures")
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
    parser.addoption("--nvos_api_type", action="store", default='nvue', help="nvue/openapi")


def pytest_runtest_call(item):
    """
    Pytest hook which is executed at the calling of test case
    :param item: pytest buildin
    """
    topology_obj = item.funcargs.get('topology_obj')
    if topology_obj:
        add_fixture_end_tag(topology_obj)


def pytest_fixture_setup(fixturedef, request):
    """
    Pytest hook which is executed at the beginning of each fixture
    :param fixturedef: pytest buildin
    :param request: pytest buildin
    """
    func_name = request._pyfuncitem.name
    for func in request.session.items:
        if func.name == func_name and getattr(func, 'funcargs', None):
            topology_obj = func.funcargs.get('topology_obj')
            if topology_obj:
                add_fixture_name(topology_obj, request.fixturename, fixturedef.scope)


def pytest_fixture_post_finalizer(fixturedef, request):
    """
    Pytest hook which is executed at the beginning of each fixture
    :param fixturedef: pytest buildin
    :param request: pytest buildin
    """
    func_name = request._pyfuncitem.name
    for func in request.session.items:
        if func.name == func_name and getattr(func, 'funcargs', None):
            topology_obj = func.funcargs.get('topology_obj')
            if topology_obj:
                if getattr(func, 'rep_setup', None) and getattr(func, 'rep_call', None) and func.rep_setup.passed and func.rep_call.failed:
                    update_fixture_scope_list(topology_obj, fixturedef.argname, fixturedef.scope)
                else:
                    clean_stored_cmds_with_fixture_scope(topology_obj, fixturedef.argname, fixturedef.scope)


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
def topology_obj(setup_name, request):
    """
    Fixture which create topology object before run tests and doing cleanup for ssh engines after test executed
    :param setup_name: example: sonic_tigris_r-tigris-06
    :param request: pytest build-in
    """
    logger.debug('Creating topology object')
    topology = get_topology_by_setup_name_and_aliases(setup_name, slow_cli=False)
    # Update CLI classes according to the current SONiC branch
    branch = request.session.config.cache.get(PytestConst.CUSTOM_TEST_SKIP_BRANCH_NAME, None)
    update_branch_in_topology(topology, branch)
    is_sanitizer = request.session.config.cache.get(PytestConst.IS_SANITIZER_IMAGE, None)
    update_sanitizer_in_topology(topology, is_sanitizer=is_sanitizer)
    update_topology_with_cli_class(topology)
    export_cli_type_to_cache(topology, request)
    enable_record_cmds(topology)

    yield topology

    logger.debug('Cleaning-up the topology object')
    for player_name, player_attributes in topology.players.items():
        player_attributes['engine'].disconnect()


@pytest.fixture(scope='session')
def cli_objects(topology_obj):
    cli_obj_data = DottedDict()
    for player in topology_obj.players:
        cli_obj_data[player] = topology_obj.players[player]['cli']
    return cli_obj_data


def export_cli_type_to_cache(topology, request):
    """
    This function will cache set a variable called CLI_TYPE that indicates what is the Cli Type, NVUE Or Sonic.
    :param topology: topology object
    :param request: pytest builtin
    """
    cli_type = topology[0]['dut']['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE']
    request.session.config.cache.set('CLI_TYPE', cli_type)


def update_topology_with_cli_class(topology):
    # TODO: determine player type by topology attribute, rather than alias
    for player_key, player_info in topology.players.items():
        if player_key == 'dut':
            if player_info['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] in NvosCliTypes.NvueCliTypes:
                player_info['cli'] = NvueCli(topology)
                player_info['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] = "NVUE"
            else:
                player_info['cli'] = SonicCli(topology)
                player_info.update({'stub_cli': SonicCliStub(topology)})
        else:
            player_info['cli'] = LinuxCli(player_info['engine'])
            player_info.update({'stub_cli': LinuxCliStub(player_info['engine'])})


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
def dut_mac(engines, cli_objects):
    """
    Fixture which get DUT mac address from DUT config_db.json file
    :param engines: engines fixture
    :param cli_objects: cli_objects fixture
    :return: dut mac address
    """
    logger.info('Getting DUT mac address')
    config_db = cli_objects.dut.general.get_config_db()
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
    sonic_version_output = engines.dut.run_cmd('sudo sonic-cfggen -y /etc/sonic/sonic_version.yml -v build_version')
    sonic_ver = sonic_version_output.strip()
    return sonic_ver


@pytest.fixture(scope='session')
def sonic_branch(topology_obj):
    """
    Pytest fixture which are returning current SONiC branch which defined in the /etc/sonic/sonic_version.yml
    :param topology_obj: topology_obj fixture
    :return: the branch name
    """
    return get_sonic_branch(topology_obj)


@pytest.fixture(scope='session', autouse=True)
def is_sanitizer_image(topology_obj):
    update_sanitizer_in_topology(topology_obj)
    pytest.is_sanitizer = topology_obj.players['dut']['sanitizer']
    return pytest.is_sanitizer


@pytest.fixture(scope='session')
def platform_params(show_platform_summary, setup_name):
    """
    Method for getting all platform related data
    :return: dictionary with platform data
    """
    platform_data = DottedDict()
    platform_data.platform = show_platform_summary['platform']
    platform_data.filtered_platform = re.search(r"(msn\d{4}c|msn\d{4}|sn\d{4}|mqm\d{4}|mbf.*c)", show_platform_summary['platform'], re.IGNORECASE).group(1)
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
def is_simx(platform_params, is_air):
    is_simx_setup = False
    if re.search('simx', platform_params.setup_name):
        is_simx_setup = True
    if is_air:
        is_simx_setup = True
    return is_simx_setup


@pytest.fixture(scope='session')
def is_air(platform_params):
    is_air_setup = False
    if re.search('air', platform_params.setup_name.lower()):
        is_air_setup = True
    return is_air_setup


def cleanup_last_config_in_stack(cleanup_list):
    """
    Execute the last function in the cleanup stack
    :param cleanup_list: list with functions to cleanup
    :return: None
    """
    func, args = cleanup_list.pop()
    func(*args)


@pytest.fixture(scope="session")
def nvos_api_type(request):
    """
    Method for getting nvos_api_type from pytest arguments
    :param request: pytest builtin
    :return: nvos_api_type argument value
    """
    return request.config.getoption('--nvos_api_type')
