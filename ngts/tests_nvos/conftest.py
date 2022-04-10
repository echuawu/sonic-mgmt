import pytest
import logging

from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import ApiType
from dotted_dict import DottedDict

logger = logging.getLogger()


@pytest.fixture(scope='session')
def engines(topology_obj):
    engines_data = DottedDict()
    engines_data.dut = topology_obj.players['dut']['engine']
    if "ha" in topology_obj.players:
        engines_data.ha = topology_obj.players['ha']['engine']
    if "hb" in topology_obj.players:
        engines_data.hb = topology_obj.players['hb']['engine']
    return engines_data


@pytest.fixture(scope='session', autouse=True)
def api_type():
    logger.info('updating API type to: ' + ApiType.NVUE)
    TestToolkit.update_apis(ApiType.NVUE)


@pytest.fixture(scope='session')
def cli_objects(topology_obj):
    cli_obj_data = DottedDict()
    cli_obj_data.dut = topology_obj.players['dut']['cli']
    if "ha" in topology_obj.players:
        cli_obj_data.ha = topology_obj.players['ha']['cli']
    if "hb" in topology_obj.players:
        cli_obj_data.hb = topology_obj.players['hb']['cli']
    return cli_obj_data


@pytest.fixture(scope='function', autouse=True)
def log_test_wrapper(request):
    test_name = request.module.__name__
    logging.info(' ---------------- TEST STARTED - {test_name} ---------------- '.format(test_name=test_name))


def pytest_runtest_call(__multicall__):
    try:
        __multicall__.execute()
        logging.info(' ---------------- The test completed successfully ---------------- ')
    except KeyboardInterrupt:
        raise
    except Exception as err:
        logging.exception(' ---------------- The test failed - an exception occurred: ---------------- ')
        raise AssertionError(err)
