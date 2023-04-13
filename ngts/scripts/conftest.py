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
