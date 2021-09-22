import sys
import os
import logging
import json

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name

CUSTOM_SKIP_IF_DICT = 'custom_skip_if_dict'
CUSTOM_TEST_SKIP_PLATFORM_TYPE = 'dynamic_tests_skip_platform_type'
CUSTOM_TEST_SKIP_BRANCH_NAME = 'dynamic_tests_skip_branch_name'

logger = logging.getLogger()

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
community_plugins_path = '/tests/common/plugins/custom_skipif'
full_path_to_community_plugins = sonic_mgmt_path + community_plugins_path
sys.path.append(full_path_to_community_plugins)

from CustomSkipIf import pytest_runtest_setup  # noqa: E402
from Branch import get_branch_from_version  # noqa: E402


def pytest_collection(session):

    topology = get_topology_by_setup_name(session.config.option.setup_name, slow_cli=False)
    devdescription = topology.players['dut']['attributes'].noga_query_data['attributes']['Specific']['devdescription']
    platform = json.loads(devdescription).get('platform')
    branch = get_branch(topology)

    session.config.cache.set(CUSTOM_SKIP_IF_DICT, None)
    session.config.cache.set(CUSTOM_TEST_SKIP_PLATFORM_TYPE, platform)
    session.config.cache.set(CUSTOM_TEST_SKIP_BRANCH_NAME, branch)


def get_branch(topology):
    try:
        show_version_raw_output = topology.players['dut']['engine'].run_cmd('show version')
        branch = get_branch_from_version(show_version_raw_output)
        return branch
    except Exception as err:
        logger.error('Unable to get branch name. Custom skip by branch impossible. Error: {}'.format(err))
