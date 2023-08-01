import datetime
import pytest
import logging
import time
import os
import re
import math
import smtplib
from retry import retry
from email.mime.text import MIMEText
from ngts.nvos_tools.Devices.DeviceFactory import DeviceFactory
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.linux.linux_general_clis import LinuxGeneralCli
from ngts.nvos_constants.constants_nvos import ApiType, OperationTimeConsts
from ngts.constants.constants import LinuxConsts
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.cli_coverage.nvue_cli_coverage import NVUECliCoverage
from dotted_dict import DottedDict
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tests_nvos.system.clock.ClockTools import ClockTools
from infra.tools.sql.connect_to_mssql import ConnectMSSQL
from ngts.constants.constants import DbConstants, CliType, DebugKernelConsts, InfraConst

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse NVOS pytest options
    :param parser: pytest build in
    """
    logger.info('Parsing NVOS pytest options')
    parser.addoption('--release_name', action='store',
                     help='The name of the release to be tested. For example: 25.01.0630')
    parser.addoption("--restore_to_image",
                     action="store", default=None, help="restore image after error flow")
    parser.addoption("--traffic_available",
                     action="store", default='True', help="True to run traffic tests")
    parser.addoption("--tst_all_pwh_confs",
                     action="store", default='False', help="True to test functionality of all password hardening "
                                                           "configurations; False otherwise (only several random "
                                                           "configurations will be picked to testing)")
    parser.addoption("--disable_cli_coverage", action="store_true", default=False, help="Do not run cli coverage")


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


@pytest.fixture(scope="session")
def mst_device(request, engines):
    return ""


@pytest.fixture(scope='session')
def devices(topology_obj):
    devices_date = DottedDict()
    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['switch_type']
    devices_date.dut = DeviceFactory.create_device(dut_name)
    return devices_date


@pytest.fixture
def traffic_available(request):
    """
    True is traffic functionality is available for current setup
    :param request: pytest builtin
    :return: True/False
    """
    return bool(request.config.getoption('--traffic_available'))


@pytest.fixture(scope='function')
def serial_engine(topology_obj):
    """
    :return: serial connection
    """
    return ConnectionTool.create_serial_connection(topology_obj)


@pytest.fixture
def tst_all_pwh_confs(request):
    """
    True to test functionality of all password hardening configurations;
        False otherwise (only several random configurations will be picked to testing)
    :param request: pytest builtin
    :return: True/False
    """
    param_val = request.config.getoption('--tst_all_pwh_confs')
    return True if param_val == 'True' else False


@pytest.fixture
def start_sm(engines, traffic_available):
    """
    Starts OpenSM
    """
    if traffic_available:
        result = OpenSmTool.start_open_sm(engines.dut)
        if not result.result:
            logging.warning("Failed to start openSM using NVUE commands")
    else:
        logging.warning("Traffic is not available on this setup")


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


def check_switch_capacity(engine):
    try:
        logger.info("Check used capacity for /var/lib/python/coverage")
        engine.run_cmd("df -h /var/lib/python/coverage/")
        engine.run_cmd("du -h /var/lib/python/coverage")
        engine.run_cmd("du -h /sonic")
    except BaseException as ex:
        logger.warning(str(ex))


@pytest.fixture(scope='function', autouse=True)
def log_test_wrapper(request, engines):
    pytest.item = request.node
    test_name = request.module.__name__
    pytest.s_time = time.time()
    logging.info(' ---------------- TEST STARTED - {test_name} ---------------- '.format(test_name=test_name))
    if 'no_log_test_wrapper' in request.keywords:
        return
    try:
        SendCommandTool.execute_command(LinuxGeneralCli(engines.dut).clear_history)
    except BaseException as exc:
        logger.error(" the command 'history -c' failed and this is the exception info : {}".format(exc))
        # should not fail the test
        pass


@pytest.fixture(scope='session')
def interfaces(topology_obj):
    interfaces_data = DottedDict()
    interfaces_data.ha_dut_1 = topology_obj.ports['ha-dut-1']
    interfaces_data.hb_dut_1 = topology_obj.ports['hb-dut-1']
    return interfaces_data


def clear_config(markers):
    try:
        TestToolkit.update_apis(ApiType.NVUE)
        if 'system_profile_cleanup' in markers:
            clear_system_profile_config()
        NvueGeneralCli.detach_config(TestToolkit.engines.dut)
        show_config_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            NvueGeneralCli.show_config(TestToolkit.engines.dut)).get_returned_value()

        set_comp = {k: v for comp in show_config_output for k, v in comp.get("set", {}).items()}

        if not(len(set_comp.keys()) == 1 and "system" in set_comp.keys() and
               len(set_comp["system"].keys()) == 1 and "timezone" in set_comp["system"]):
            should_wait_for_nvued_after_apply = 'aaa' in set_comp["system"].keys() \
                                                and 'authentication' in set_comp["system"]['aaa'].keys() \
                                                and 'order' in set_comp["system"]['aaa']['authentication'].keys()
            if len(set_comp["system"].keys()) > 1:
                NvueBaseCli.unset(TestToolkit.engines.dut, 'system')
            if "ib" in set_comp.keys():
                NvueBaseCli.unset(TestToolkit.engines.dut, 'ib')
            active_port = None
            if "interface" in set_comp.keys():
                result = Tools.RandomizationTool.select_random_ports(num_of_ports_to_select=1)
                if result.result:
                    active_port = result.returned_value[0]
                NvueBaseCli.unset(TestToolkit.engines.dut, 'interface')

            system = System()
            system.aaa.authentication.restrictions.set(RestrictionsConsts.LOCKOUT_STATE, RestrictionsConsts.DISABLED)\
                .verify_result()
            system.aaa.authentication.restrictions.set(RestrictionsConsts.FAIL_DELAY, 0).verify_result()
            ClockTools.set_timezone(LinuxConsts.JERUSALEM_TIMEZONE, system, apply=False)
            NvueGeneralCli.apply_config(engine=TestToolkit.engines.dut, option='--assume-yes')
            if should_wait_for_nvued_after_apply:
                DutUtilsTool.wait_for_nvos_to_become_functional(TestToolkit.engines.dut).verify_result()
            if active_port:
                active_port.ib_interface.wait_for_port_state(state='up').verify_result()

    except Exception as err:
        logging.warning("Failed to clear config:" + str(err))


def clear_system_profile_config():
    system = System(None)
    system_profile_output = OutputParsingTool.parse_json_str_to_dictionary(system.profile.show()).get_returned_value()
    try:
        ValidationTool.validate_fields_values_in_output(SystemConsts.PROFILE_OUTPUT_FIELDS,
                                                        SystemConsts.DEFAULT_SYSTEM_PROFILE_VALUES,
                                                        system_profile_output).verify_result()
    except AssertionError:
        system.profile.action_profile_change(
            params='adaptive-routing enabled breakout-mode disabled')


def pytest_exception_interact(report):
    try:
        TestToolkit.engines.dut.run_cmd("docker ps")
        TestToolkit.engines.dut.run_cmd("systemctl --type=service")
    except BaseException as err:
        logging.warning(err)
    save_results_and_clear_after_test(pytest.item)
    logging.error(f'---------------- The test failed - an exception occurred: ---------------- \n{report.longreprtext}')


@pytest.hookimpl(trylast=True)
def pytest_runtest_call(item):
    save_results_and_clear_after_test(item)


def save_results_and_clear_after_test(item):
    markers = item.keywords._markers
    try:
        logging.info(' ---------------- The test completed successfully ---------------- ')
        run_cli_coverage(item, markers)
    except KeyboardInterrupt:
        raise
    except Exception as err:
        logging.exception(' ---------------- The test failed - an exception occurred: ---------------- ')
        raise AssertionError(err)
    finally:
        clear_config(markers)


@pytest.fixture(scope='function', autouse=True)
def debug_kernel_check(engines, test_name, setup_name, session_id):
    yield
    if pytest.is_debug_kernel:
        engines.dut.run_cmd("sudo dmesg | grep {}".format(DebugKernelConsts.KMEMLEAK))
        engines.dut.run_cmd("sudo echo scan | sudo tee {}".format(DebugKernelConsts.KMEMLEAK_PATH))
        mem_leaks_output = engines.dut.run_cmd("sudo cat {}".format(DebugKernelConsts.KMEMLEAK_PATH))
        if mem_leaks_output:
            logger.info("kernel memory leaks were found, will send mail with the leaks")
            context = f"Kernel memory leaks were found during test:{test_name}\n" \
                      f"Setup: {setup_name}\n" \
                      f"Session ID: {session_id}\n" \
                      f"{mem_leaks_output}"
            try:
                s = smtplib.SMTP(InfraConst.NVIDIA_MAIL_SERVER)
                email_contents = MIMEText(context)
                email_contents['Subject'] = "debug kernel issue nvos"
                email_contents['To'] = ", ".join(['bshpigel@nvidia.com', 'ncaro@nvidia.com', 'yport@nvidia.com'])
                s.sendmail('noreply@debugkernel.com', email_contents['To'], email_contents.as_string())
                logger.info("Mail was sent to: {}".format(email_contents['To']))
            finally:
                s.quit()

            engines.dut.run_cmd("sudo echo clear | sudo tee {}".format(DebugKernelConsts.KMEMLEAK_PATH))


@pytest.fixture(scope="session", autouse=True)
def insert_operation_time_to_db(setup_name, session_id, platform_params, topology_obj):
    '''
    @summary:   insert operation times to operation_time table DB.
    during the tests we will add to pytest.operation_list the operations that we want to measure,
    and at the end of the test we will insert it to the DB.
    '''
    pytest.operation_list = []
    yield
    if len(pytest.operation_list) > 0:
        try:
            type = platform_params['filtered_platform']
            version = OutputParsingTool.parse_json_str_to_dictionary(System().version.show()).get_returned_value()['image']
            release_name = TestToolkit.version_to_release(version)
            if not TestToolkit.is_special_run() and pytest.is_mars_run and release_name and not pytest.is_ci_run:
                insert_operation_duration_to_db(setup_name, type, version, session_id, release_name)
        except Exception as err:
            logger.warning("Failed to save operation duration data, because: {}".format(err))


@retry(Exception, tries=3, delay=3)
def insert_operation_duration_to_db(setup_name, type, version, session_id, release_name):
    connections_params = DbConstants.CREDENTIALS[CliType.NVUE]
    mssql_connection_obj = ConnectMSSQL(connections_params['server'], connections_params['database'],
                                        connections_params['username'], connections_params['password'])
    mssql_connection_obj.connect_db()
    logger.info("Insert {} operations info to operation_time DB".format(len(pytest.operation_list)))
    try:
        values = ""
        for operation in pytest.operation_list:
            value = "('{operation}', '{command}', '{duration}', '{setup_name}', '{type}', '{version}', " \
                    "'{release}', '{session_id}', '{test_name}', '{date}')".format(
                        operation=operation[OperationTimeConsts.OPERATION_COL],
                        command=operation[OperationTimeConsts.PARAMS_COL],
                        duration=operation[OperationTimeConsts.DURATION_COL], setup_name=setup_name, type=type,
                        version=version, release=release_name, session_id=session_id,
                        test_name=operation[OperationTimeConsts.TEST_NAME_COL], date=datetime.date.today())

            values = values + ', ' + value if values else value

        if values:
            columns = "({operation_col}, {params_col}, {duration_col}, {setup_name_col}, {type_col}, {version_col}," \
                      " {release_col}, {session_id_col}, {test_name_col}, {date_col})".format(
                          operation_col=OperationTimeConsts.OPERATION_COL, params_col=OperationTimeConsts.PARAMS_COL,
                          duration_col=OperationTimeConsts.DURATION_COL, setup_name_col=OperationTimeConsts.SETUP_COL,
                          type_col=OperationTimeConsts.TYPE_COL, version_col=OperationTimeConsts.VERSION_COL,
                          release_col=OperationTimeConsts.RELEASE_COL, session_id_col=OperationTimeConsts.SESSION_ID_COL,
                          test_name_col=OperationTimeConsts.TEST_NAME_COL, date_col=OperationTimeConsts.DATE_COL)
            query = "INSERT operation_time {columns} values {values};".format(columns=columns, values=values)

        mssql_connection_obj.query_insert(query)
        logger.info("--------- insert to operation time DB table successfully ---------\n")
    finally:
        mssql_connection_obj.disconnect_db()


@pytest.fixture(autouse=True)
def disable_cli_coverage(request):
    """
    Method for getting disable_cli_coverage from pytest arguments
    :param request: pytest builtin
    """
    pytest.disable_cli_coverage = request.config.getoption('--disable_cli_coverage')


def run_cli_coverage(item, markers):
    if TestToolkit.tested_api == ApiType.NVUE and \
            os.path.exists('/auto/sw/tools/comet/nvos/') and \
            'no_cli_coverage_run' not in markers and \
            not pytest.is_sanitizer and \
            pytest.is_mars_run and \
            not pytest.disable_cli_coverage:
        logging.info("API type is NVUE and is it not a sanitizer version, so CLI coverage script will run")
        NVUECliCoverage.run(item, pytest.s_time)
