import sys
import os

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
community_plugins_path = '/tests/common/plugins/'
full_path_to_community_plugins = sonic_mgmt_path + community_plugins_path
sys.path.append(full_path_to_community_plugins)

from allure_server import pytest_addoption, pytest_sessionfinish, pytest_terminal_summary


def pytest_sessionstart(session):

    session.config.option.allure_server_addr = '10.215.11.120'

    topology = get_topology_by_setup_name(session.config.option.setup_name, slow_cli=False)
    dut_name = topology.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    session.config.option.testbed = dut_name
