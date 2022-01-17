import sys
import os
import logging
import json

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.helpers.sonic_branch_helper import get_sonic_branch

CUSTOM_TEST_SKIP_PLATFORM_TYPE = 'dynamic_tests_skip_platform_type'
CUSTOM_TEST_SKIP_BRANCH_NAME = 'dynamic_tests_skip_branch_name'
LA_DYNAMIC_IGNORES_LIST = 'LA_DYNAMIC_IGNORES_LIST'

logger = logging.getLogger()

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
community_plugins_path = 'tests/common/plugins/loganalyzer_dynamic_errors_ignore'
full_path_to_community_plugins = sonic_mgmt_path + community_plugins_path
sys.path.append(full_path_to_community_plugins)

from loganalyzer_dynamic_errors_ignore.la_dynamic_errors_ignore import pytest_runtest_call  # noqa: E402


def pytest_collection(session):

    session.config.cache.set(LA_DYNAMIC_IGNORES_LIST, None)

    branch = session.config.cache.get(CUSTOM_TEST_SKIP_BRANCH_NAME, None)
    platform = session.config.cache.get(CUSTOM_TEST_SKIP_PLATFORM_TYPE, None)

    if not branch or not platform:
        topology = get_topology_by_setup_name(session.config.option.setup_name, slow_cli=False)
        devinfo = topology.players['dut']['attributes'].noga_query_data['attributes']['Specific']['devdescription']

        if not platform:
            platform = json.loads(devinfo).get('platform')
            session.config.cache.set(CUSTOM_TEST_SKIP_PLATFORM_TYPE, platform)
        if not branch:
            branch = get_sonic_branch(topology)
            session.config.cache.set(CUSTOM_TEST_SKIP_BRANCH_NAME, branch)
