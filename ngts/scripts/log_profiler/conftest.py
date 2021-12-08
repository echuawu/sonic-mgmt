"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest builtin
    """
    parser.addoption('--test_files', action='store', required=True,
                     help='Directory name contains test files')
    parser.addoption('--syslog_start_line', action='store', required=True,
                     help='Pattern to search in syslog to reference the beggining of test log')
    parser.addoption('--sairedis_start_line', action='store', required=True,
                     help='Pattern to search in sairedis.rec to reference the beggining of test log')


@pytest.fixture(scope="module")
def test_files(request):
    """
    Method for getting deploy type from pytest arguments
    :param request: pytest builtin
    :return: deploy type
    """
    return request.config.getoption('--test_files')


@pytest.fixture(scope="module")
def syslog_start_line(request):
    """
    Method for getting deploy type from pytest arguments
    :param request: pytest builtin
    :return: deploy type
    """
    return request.config.getoption('--syslog_start_line')


@pytest.fixture(scope="module")
def sairedis_start_line(request):
    """
    Method for getting deploy type from pytest arguments
    :param request: pytest builtin
    :return: deploy type
    """
    return request.config.getoption('--sairedis_start_line')
