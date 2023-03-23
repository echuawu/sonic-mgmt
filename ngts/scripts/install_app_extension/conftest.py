import pytest
import logging
"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""
logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest options')
    parser.addoption("--remove_app_extension", action='store', required=False,
                     help='Specify app extensions you would like to remove after deployment.')


@pytest.fixture(scope='session')
def remove_app_extension(request):
    """
    Method for get setup name from pytest arguments
    :param request: pytest buildin
    :return: app extension names to be removed
    """
    app_extension_input = request.config.getoption('--remove_app_extension')
    app_extension_list = app_extension_input.split(",")
    return app_extension_list
