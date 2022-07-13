from ngts.tools.topology_tools.topology_by_setup import get_topology_by_setup_name_and_aliases
from ngts.tools.infra import update_sys_path_by_community_plugins_path

update_sys_path_by_community_plugins_path()

from plugins.allure_server import pytest_addoption, pytest_sessionfinish, pytest_terminal_summary, \
    cache_pytest_session_run_cmd, attach_pytest_specific_test_run_cmd_to_allure_report  # noqa: E402


def testbed_param_already_loaded(session):
    return hasattr(session.config.option, 'testbed')


def get_setup_topology(session):
    setup_topology = 'ptf-any'
    if hasattr(session.config.option, 'sonic_topo'):
        if session.config.option.sonic_topo:
            setup_topology = session.config.option.sonic_topo
    return setup_topology


def pytest_sessionstart(session):
    session.config.option.allure_server_addr = '10.215.11.120'
    if not testbed_param_already_loaded(session):
        topology = get_topology_by_setup_name_and_aliases(session.config.option.setup_name, slow_cli=False)
        dut_name = topology.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        setup_topology = get_setup_topology(session)
        session.config.option.testbed = f'{dut_name}-{setup_topology}'
