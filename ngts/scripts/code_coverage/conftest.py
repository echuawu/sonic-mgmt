"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    parser.addoption('--dest', action='store', required=True, help='The directory in which to save the extracted coverage .xml files')
    parser.addoption("--nvos", action="store_true", default=False, help="Run on NVOS system (IB)")


@pytest.fixture(scope='module')
def dest(request):
    return request.config.getoption('--dest')


@pytest.fixture(scope='module')
def nvos(request):
    return request.config.getoption('--nvos')
