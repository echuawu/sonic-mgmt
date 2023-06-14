import pytest


def pytest_addoption(parser):
    parser.addoption('--reboot_type', action='store', default=None,
                     help='Argument related to reboot type, based on it we can specify reboot type which should be '
                          'executed in test. Supported reboot types: fast, warm, reboot, reload')


@pytest.fixture(scope='session')
def reboot_type(request):
    """
    Method for get reboot_type from pytest arguments
    """
    return request.config.getoption('reboot_type')
