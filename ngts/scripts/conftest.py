import logging
import pytest
from ngts.constants.constants import SonicConst
logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest builtin
    """
    logger.info('Parsing pytest script options')
    parser.addoption("--preset", action="store", default=None,
                     help="the configuration setting required on the switch, i.e. \"l2\"")
    parser.addoption("--shutdown_ifaces", action="store", default=None,
                     help="interfaces on the switch required shutdown, i.e. \"Ethernet0,Ethernet2\" ")
    parser.addoption('--dockers_list', action="store", help='Dockers that should verified to be up, '
                                                            'i.e  --dockers_list=database,swss '
                                                            'will verify database and swss dockers are up',
                     default=",".join(SonicConst.DOCKERS_LIST))
    parser.addoption('--dut_name', action='store', default=None, help='DUT name, example: r-tigris-06')


@pytest.fixture(scope='function')
def preset(request):
    """
    Method for get the configuration setting required on the switch
    :param request: pytest builtin
    :return: the configuration setting required on the switch, i.e. "l2"
    """
    return request.config.getoption('--preset')


@pytest.fixture(scope='function')
def dockers_list(request):
    """
    Method for getting a list of dockers that should be up on the switch
    :param request: pytest builtin
    :return: a list of dockers that should be up on the switch, i.e ['database','swss']
    """
    return request.config.getoption('--dockers_list').split(',')


@pytest.fixture(scope="module")
def sonic_topo(request):
    """
    Method for getting sonic-topo from pytest arguments
    :param request: pytest builtin
    :return: sonic-topo (for example: t0, t1, t1-lag, ptf32)
    """
    return request.config.getoption('--sonic-topo')


@pytest.fixture(scope='session')
def dut_name(request):
    """
    Method for get dut name from pytest arguments
    :param request: pytest builtin
    :return: dut name
    """
    return request.config.getoption('--dut_name')
