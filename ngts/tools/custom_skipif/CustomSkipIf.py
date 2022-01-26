import sys
import os
import logging

logger = logging.getLogger()

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
community_plugins_path = '/tests/common/plugins/custom_skipif'
full_path_to_community_plugins = sonic_mgmt_path + community_plugins_path
sys.path.append(full_path_to_community_plugins)

from CustomSkipIf import pytest_runtest_setup  # noqa: E402
