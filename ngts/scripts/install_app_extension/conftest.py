"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest builtin
    """
    parser.addoption('--app_extension_dict_path', action='store', required=False, default=None,
                     help='''Provide path to application extensions json file.
                          'Example of content: {"p4-sampling":"harbor.mellanox.com/sonic-p4/p4-sampling:0.2.0",
                                      "what-just-happened":"harbor.mellanox.com/sonic-wjh/docker-wjh:1.0.1"} ''')


@pytest.fixture(scope="module")
def app_extension_dict_path(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: app_extension_dict
    """
    return request.config.getoption('--app_extension_dict_path')
