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
    logger.info('Parsing deploy type')
    parser.addoption('--deploy_type', action='store', choices=['onie', 'sonic'], required=True, default='onie',
                     help='Deploy type')
    logger.info('Parsing apply_base_config')
    parser.addoption('--apply_base_config', action='store', required=False, default=None,
                     help='Apply base config or not, for canonical True, for community False')
    logger.info('Parsing reboot after install')
    parser.addoption('--reboot_after_install', action='store', required=False, default=None,
                     help='Reboot after installation or not to overcome swss issue')
    logger.info('Parsing is shutdown bgp ')
    parser.addoption('--is_shutdown_bgp', action='store_true', required=False, default=False,
                     help='For sonic install, need shutdown bgp, or it can not access the external IP')


@pytest.fixture(scope="module")
def deploy_type(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: setup name
    """
    return request.config.getoption('--deploy_type')


@pytest.fixture(scope="module")
def apply_base_config(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: setup name
    """
    return request.config.getoption('--apply_base_config')


@pytest.fixture(scope="module")
def reboot_after_install(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: whether to do reboot after installation to overcome swss docker in exited state
    """
    return request.config.getoption('--reboot_after_install')


@pytest.fixture(scope="module")
def is_shutdown_bgp(request):
    """
    Method for getting shutdown bgp flag from pytest arguments
    :param request: pytest builtin
    :return: True or False
    """
    return request.config.getoption('--is_shutdown_bgp')