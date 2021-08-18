import logging
import pytest

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest script options')
    parser.addoption("--preset", action="store", default=None,
                     help="the configuration setting required on the switch, i.e. \"l2\"")
    parser.addoption("--shutdown_ifaces", action="store", default=None,
                     help="interfaces on the switch required shutdown, i.e. \"Ethernet0,Ethernet2\" ")


@pytest.fixture(scope='function')
def preset(request):
    """
    Method for get the configuration setting required on the switch
    :param request: pytest buildin
    :return: the configuration setting required on the switch, i.e. "l2"
    """
    return request.config.getoption('--preset')
