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


@pytest.fixture(scope='module')
def dest(request):
    return request.config.getoption('--dest')
