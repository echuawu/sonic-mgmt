import sys
import os


path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/tests/')[0]
ngts_plugins_path = '/ngts/tools/'
full_path_to_ngts_plugins = sonic_mgmt_path + ngts_plugins_path
sys.path.append(full_path_to_ngts_plugins)

from mars_test_cases_results import pytest_sessionfinish, pytest_terminal_summary


def pytest_addoption(parser):
    parser.addoption("--disable_exporting_results_to_mars_db", action="store_true", default=False,
                     help="Disable exporting cases results to MARS SQL database")
