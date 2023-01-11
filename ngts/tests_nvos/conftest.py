import pytest
import logging
import time
import os
from ngts.nvos_tools.Devices.DeviceFactory import DeviceFactory
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.linux.linux_general_clis import LinuxGeneralCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.constants.constants import LinuxConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.cli_coverage.nvue_cli_coverage import NVUECliCoverage
from dotted_dict import DottedDict
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse NVOS pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing NVOS pytest options')
    parser.addoption('--release_name', action='store',
                     help='The name of the release to be tested. For example: 25.01.0630')
    parser.addoption('--mst_device', action='store',
                     help='The name of the mst device. For example: /dev/mst/mt4123_pciconf0')
    parser.addoption("--restore_to_image",
                     action="store", default=None, help="restore image after error flow")


@pytest.fixture(scope='session')
def engines(topology_obj):
    engines_data = DottedDict()
    engines_data.dut = topology_obj.players['dut']['engine']
    # ha and hb are the traffic dockers
    if "ha" in topology_obj.players:
        engines_data.ha = topology_obj.players['ha']['engine']
    if "hb" in topology_obj.players:
        engines_data.hb = topology_obj.players['hb']['engine']
    if "server" in topology_obj.players:
        engines_data.server = topology_obj.players['server']['engine']
    if "sonic-mgmt" in topology_obj.players:
        engines_data.sonic_mgmt = topology_obj.players['sonic-mgmt']['engine']

    TestToolkit.update_engines(engines_data)
    return engines_data


@pytest.fixture(scope='session')
def devices(topology_obj):
    devices_date = DottedDict()
    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['switch_type']
    devices_date.dut = DeviceFactory.create_device(dut_name)
    return devices_date


@pytest.fixture
def start_sm(engines):
    """
    Starts OpenSM
    """
    result = OpenSmTool.start_open_sm(engines.dut)
    if not result.result:
        logging.warning("Failed to start openSM using NVUE commands")


@pytest.fixture
def stop_sm(engines):
    """
    Stops OpenSM
    """
    result = OpenSmTool.stop_open_sm(engines.dut)
    if not result.result:
        logging.warning("Failed to stop openSM using NVUE commands")


@pytest.fixture(scope="session")
def release_name(request):
    """
    Method for getting release_name from pytest arguments
    :param request: pytest builtin
    :return: release_name
    """
    return request.config.getoption('--release_name')


@pytest.fixture(scope="session")
def mst_device(request):
    return request.config.getoption('--mst_device')


@pytest.fixture(scope='session', autouse=True)
def api_type(nvos_api_type):
    apitype = ApiType.NVUE
    if nvos_api_type.lower() == "openapi":
        apitype = ApiType.OPENAPI

    logger.info('updating API type to: ' + apitype)
    TestToolkit.update_apis(apitype)


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
def log_test_wrapper(request, engines):
    test_name = request.module.__name__
    pytest.s_time = time.time()
    logging.info(' ---------------- TEST STARTED - {test_name} ---------------- '.format(test_name=test_name))
    if 'no_log_test_wrapper' in request.keywords:
        return
    try:
        SendCommandTool.execute_command(LinuxGeneralCli(engines.dut).clear_history)
    except Exception as exc:
        logger.error(" the command 'history -c' failed and this is the exception info : {}".format(exc))
        # should not fail the test
        pass


@pytest.fixture(scope='session')
def interfaces(topology_obj):
    interfaces_data = DottedDict()
    interfaces_data.ha_dut_1 = topology_obj.ports['ha-dut-1']
    interfaces_data.hb_dut_1 = topology_obj.ports['hb-dut-1']
    return interfaces_data


def clear_config():
    try:
        NvueGeneralCli.detach_config(TestToolkit.engines.dut)
        show_config_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            NvueGeneralCli.show_config(TestToolkit.engines.dut)).get_returned_value()
        for comp in show_config_output:
            if "set" in comp.keys() and "interface" in comp["set"].keys():
                result = Tools.RandomizationTool.select_random_ports(num_of_ports_to_select=1)
                active_port = None
                if result.result:
                    active_port = result.returned_value[0]
                NvueGeneralCli.apply_empty_config(TestToolkit.engines.dut)
                if active_port:
                    active_port.ib_interface.wait_for_port_state(state='up').verify_result()
                break
        else:
            NvueSystemCli.unset(TestToolkit.engines.dut, 'system')
            NvueSystemCli.unset(TestToolkit.engines.dut, 'ib')
            NvueSystemCli.unset(TestToolkit.engines.dut, 'interface')
            NvueGeneralCli.apply_config(engine=TestToolkit.engines.dut, option='--assume-yes')
    except Exception as err:
        logging.warning("Failed to clear config:" + str(err))


@pytest.hookimpl(trylast=True)
def pytest_runtest_call(item):
    try:
        markers = item.keywords._markers
        logging.info(' ---------------- The test completed successfully ---------------- ')
        if TestToolkit.tested_api == ApiType.NVUE and os.path.exists('/auto/sw/tools/comet/nvos/') \
                and 'no_cli_coverage_run' not in markers and not pytest.is_sanitizer:
            logging.info("API type is NVUE and is it not a sanitizer version, so CLI coverage script will run")
            NVUECliCoverage.run(item, pytest.s_time)
    except KeyboardInterrupt:
        raise
    except Exception as err:
        logging.exception(' ---------------- The test failed - an exception occurred: ---------------- ')
        raise AssertionError(err)
    finally:
        clear_config()


@pytest.fixture(scope="session", autouse=True)
def configure_same_time_zone(engines):
    '''
    @summary: configure same time zone for local engine running device
    and device under test
    '''
    # TODO: add ntp enable when ntp is implemented
    logger.info("Configuring same time zone for dut and local engine to {}".format(LinuxConsts.JERUSALEM_TIMEZONE))
    engines.dut.run_cmd('sudo timedatectl set-timezone {}'.format(LinuxConsts.JERUSALEM_TIMEZONE))
    os.popen('sudo timedatectl set-timezone {}'.format(LinuxConsts.JERUSALEM_TIMEZONE))