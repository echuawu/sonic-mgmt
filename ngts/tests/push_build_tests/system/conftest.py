import pytest
import logging

logger = logging.getLogger()


def pytest_addoption(parser):
    parser.addoption('--reboot_type', action='store', default=None,
                     help='Argument related to reboot type, based on it we can specify reboot type which should be '
                          'executed in test. Supported reboot types: fast, warm, reboot, reload')
    parser.addoption('--release_mode', action='store_true', default=False, help='Run test before a release')
    parser.addoption('--min_gap', action='store', default=1, help='Minimum allowed gap in days between tests')


@pytest.fixture(scope='session')
def reboot_type(request):
    """
    Method for get reboot_type from pytest arguments
    """
    return request.config.getoption('reboot_type')


@pytest.fixture(scope="session")
def release_mode(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: base_version argument value
    """
    return request.config.getoption('--release_mode')


@pytest.fixture(scope="session")
def min_gap(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: base_version argument value
    """
    return request.config.getoption('--min_gap')
