import logging
import pytest
import re
import time
import subprocess
import os
import signal

from retry import retry
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.tools.test_utils.allure_utils import step as allure_step
from ngts.nvos_constants.constants_nvos import HealthConsts, NvosConst, DatabaseConst, SystemConsts
from ngts.nvos_tools.infra.Tools import Tools
from ngts.constants.constants import GnmiConsts


logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_basic_flow_poll(engines):
    """
    Check gnmi basic flow: show command , disable and enable commands, validate stream updates to gnmi-client,
     with subscribe mode - poll.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. Disable gnmi-server
            7. validate gnmi-server is not running
            8. validate health status is OK
            9. enable gnmi-server
            10. validate gnmi-server is running
            11. validate gnmi-server stream updates
    """
    gnmi_basic_flow(engines, flags='-poll')


@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_basic_flow_once(engines):
    """
    Check gnmi basic flow: show command , disable and enable commands, validate stream updates to gnmi-client,
     with subscribe mode - once.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. Disable gnmi-server
            7. validate gnmi-server is not running
            8. validate health status is OK
            9. enable gnmi-server
            10. validate gnmi-server is running
            11. validate gnmi-server stream updates
    """
    gnmi_basic_flow(engines, flags='-once')


@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_gnmi_basic_flow_stream(test_api, engines):
    """
    Check gnmi basic flow: show command , disable and enable commands, validate stream updates to gnmi-client,
     with subscribe mode - stream.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. Disable gnmi-server
            7. validate gnmi-server is not running
            8. validate health status is OK
            9. enable gnmi-server
            10. validate gnmi-server is running
            11. validate gnmi-server stream updates
    """
    TestToolkit.tested_api = test_api
    gnmi_basic_flow(engines, flags='')


@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_simulate_gnmi_server_failure(test_api, engines):
    """
    In this test we will simulate a gnmi-server failure,
    by disabling the auto restart and stop the gnmi-server docker,
    will validate that its still enabled but not running, health status changes and reconnect after restart the docker.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. simulate gnmi-server failure
            7. validate gnmi-server is not running but enabled
            8. validate health status is not OK
            9. fix gnmi-server failure
            10. validate gnmi-server is running
            11. validate gnmi-server stream updates
    """
    TestToolkit.tested_api = test_api
    system = System()
    gnmi_server_obj = system.gnmi_server
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)

    try:
        with allure_step('Simulate gnmi server failure'):
            Tools.RedisTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_ID, "FEATURE|gnmi-server", "auto_restart", "disabled")
            engines.dut.run_cmd("docker stop gnmi-server")
            validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_ENABLED,
                               gnmi_is_running=GnmiConsts.GNMI_IS_NOT_RUNNING)
            sleep_time_for_health_issue = 6
            logger.info(f"sleep {sleep_time_for_health_issue} seconds until the health output will be updated")
            time.sleep(sleep_time_for_health_issue)
            validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=True)
            logger.info(f"{GnmiConsts.GNMI_DOCKER} appears in the health issues as we expect, "
                        f"after the gnmi-server failure")
    finally:
        with allure_step('re-enable gnmi server'):
            Tools.RedisTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_ID, "FEATURE|gnmi-server", "auto_restart", "enabled")
            engines.dut.run_cmd("docker start gnmi-server")
            gnmi_server_obj.disable_gnmi_server()
            gnmi_server_obj.enable_gnmi_server()
            logger.info("sleep 90 sec until validate stream updates")
            time.sleep(90)
            validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)


@pytest.mark.system
@pytest.mark.gnmi
def test_updates_on_gnmi_stream_mode(engines):
    """
        Test flow:
            1. validate gnmi is running and send updates
            2. change port description
            3. wait until get port description update
    """
    system = System()
    gnmi_server_obj = system.gnmi_server
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)

    with allure_step("Change port description and wait until gnmi-client gets description update"):
        selected_port = Tools.RandomizationTool.select_random_port().returned_value
        xpath = f'/interfaces/interface[name={selected_port.name}]/state/description'

        with allure_step('Run gnmi client command in the background'):
            background_process = run_gnmi_client_in_the_background(engines.dut.ip, xpath)

        with allure_step('Set port description'):
            port_description = Tools.RandomizationTool.get_random_string(7)
            selected_port.ib_interface.set(NvosConst.DESCRIPTION, port_description, apply=True).verify_result()
            selected_port.update_output_dictionary()
            Tools.ValidationTool.verify_field_value_in_output(selected_port.show_output_dictionary, NvosConst.DESCRIPTION,
                                                              port_description).verify_result()

        with allure_step('Kill gnmi client command and verify updates'):
            logger.info(f"sleep {GnmiConsts.SLEEP_TIME_FOR_UPDATE} sec until verify gnmi updates")
            time.sleep(GnmiConsts.SLEEP_TIME_FOR_UPDATE)
            os.killpg(os.getpgid(background_process.pid), signal.SIGTERM)
        gnmi_client_output, error = background_process.communicate()
        assert port_description in str(gnmi_client_output), \
            "we expect to see the new port description in the gnmi-client output but we didn't.\n" \
            f"port description: {port_description}\n" \
            f"but got: {str(gnmi_client_output)}"


@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_gnmi_bad_flow(test_api, engines):
    """
    Check gnmi bad flow:
        Test flow:
            1. validate gnmi is running and send updates
            2. invalid command
            3. Subscribe to the gnmi server for data that is not supported
            5. Subscribe to the gnmi server with bad xpath
    """
    TestToolkit.tested_api = test_api
    system = System()
    gnmi_server_obj = system.gnmi_server
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)

    with allure_step("invalid command"):
        gnmi_server_obj.set(GnmiConsts.GNMI_STATE_FIELD, Tools.RandomizationTool.get_random_string(7), "Error")

    with allure_step("Subscribe to the gnmi server for data that is not supported"):
        xpath = '/interfaces/interface[name=sw1p1]/state/counters/in-broadcast-pkts'
        gnmi_stream_updates = run_gnmi_client_and_parse_output(engines, xpath, engines.dut.ip)
        gnmi_stream_updates_value = list(gnmi_stream_updates.values())[0]
        assert gnmi_stream_updates_value == '0', f'{xpath} is unsupported field,' \
                                                 f' so we expect to have 0, but got {gnmi_stream_updates_value}'

    with allure_step("Subscribe to the gnmi server with bad xpath"):
        xpath = f'/{Tools.RandomizationTool.get_random_string(5)}/{Tools.RandomizationTool.get_random_string(5)}'
        run_gnmi_client_and_parse_output(engines, xpath, engines.dut.ip)
        # just want to be sure no LA errors


@pytest.mark.system
@pytest.mark.gnmi
def test_simulate_gnmi_client_failure(engines):
    """
    In this test we will simulate a gnmi-client failure by killing the gnmi-client process,
    will validate that it’s still enabled and running on the switch, health status doesn’t change
     and reconnect after restart the process.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. simulate gnmi-client failure
            7. validate gnmi-server is running and enabled
            8. validate health status is  OK
    """
    system = System()
    gnmi_server_obj = system.gnmi_server
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)

    with allure_step('Simulate gnmi client failure'):
        with allure_step('Run gnmi client command in the background and sleep 3 sec'):
            background_process = run_gnmi_client_in_the_background(engines.dut.ip, '/interfaces')
            time.sleep(3)
        with allure_step('Kill gnmi client command'):
            os.killpg(os.getpgid(background_process.pid), signal.SIGTERM)
        validate_gnmi_enabled_and_running(gnmi_server_obj, engines)
        validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=False)


@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_performance(engines):
    """
    Run 10 gnmi-client process to the same switch, validate stream updates and switch state.
        Test flow:
            1. create 10 gnmi_clients
            2. change port description
            3. validate gnmi-server stream updates
    """
    num_engines = 10
    gnmi_clients_without_updates = 0
    threads = []
    result = []
    port_description = Tools.RandomizationTool.get_random_string(7)
    selected_port = Tools.RandomizationTool.select_random_port().returned_value

    with allure_step(f"run {num_engines} gnmi_client sessions in the background"):
        for engine_id in range(num_engines):
            threads.append(run_gnmi_client_in_the_background(engines.dut.ip, f"/interfaces/interface[name={selected_port.name}]/state/description"))

    with allure_step("validate memory and CPU utilization"):
        validate_memory_and_cpu_utilization()

    with allure_step(f"change port description"):
        selected_port.ib_interface.set(NvosConst.DESCRIPTION, port_description, apply=True).verify_result()
        selected_port.update_output_dictionary()
        Tools.ValidationTool.verify_field_value_in_output(selected_port.show_output_dictionary, NvosConst.DESCRIPTION,
                                                          port_description).verify_result()
        logger.info(f"sleep {GnmiConsts.SLEEP_TIME_FOR_UPDATE} sec until we start validate the gnmi stream")
        time.sleep(GnmiConsts.SLEEP_TIME_FOR_UPDATE)

    with allure_step(f"stop the gnmi_client sessions and validate updates"):
        for thread in threads:
            os.killpg(os.getpgid(thread.pid), signal.SIGTERM)
            output, error = thread.communicate()
            result.append(output)
            if port_description not in str(output):
                gnmi_clients_without_updates += 1
        assert gnmi_clients_without_updates == 0, f"{gnmi_clients_without_updates} gnmi clients didn't get updates.."


# ------------ test functions -----------------
def validate_memory_and_cpu_utilization():
    system = System()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("memory")).get_returned_value()
    memory_util = output_dictionary[SystemConsts.MEMORY_PHYSICAL_KEY]["utilization"]
    assert SystemConsts.MEMORY_PERCENT_THRESH_MIN < memory_util < SystemConsts.MEMORY_PERCENT_THRESH_MAX, \
        "Physical utilization percentage is out of range"
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("cpu")).get_returned_value()
    cpu_utilization = output_dictionary[SystemConsts.CPU_UTILIZATION_KEY]
    assert cpu_utilization < SystemConsts.CPU_PERCENT_THRESH_MAX, \
        "CPU utilization: {actual}% is higher than the maximum limit of: {expected}%" \
        "".format(actual=cpu_utilization, expected=SystemConsts.CPU_PERCENT_THRESH_MAX)


def run_gnmi_client_in_the_background(target_ip, xpath):
    command = f"{GnmiConsts.GNMI_CLIENT_CMD} -target_addr {target_ip}:{GnmiConsts.GNMI_DEFAULT_PORT} -xpath '{xpath}'"
    # Use the subprocess.Popen function to run the command in the background
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return process


def gnmi_basic_flow(engines, flags='', ipv6=False):
    """
    Check gnmi basic flow: show command , disable and enable commands, validate stream updates to gnmi-client.
        Test flow:
            1. validate gnmi-server is running
            2. validate health status is OK
            3. change port description
            5. validate gnmi-server stream updates
            6. Disable gnmi-server
            7. validate gnmi-server is not running
            8. validate health status is OK
            9. enable gnmi-server
            10. validate gnmi-server is running
            11. validate gnmi-server stream updates
    """
    system = System()
    gnmi_server_obj = system.gnmi_server
    target_ip = MgmtPort('eth0').interface.get_ipv6_address() if ipv6 else engines.dut.ip
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, flags=flags)

    with allure_step('Disable gnmi'):
        gnmi_server_obj.disable_gnmi_server()
        validate_gnmi_disabled_and_not_running(gnmi_server_obj, engines)
        validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=False)

    with allure_step('Enable gnmi'):
        gnmi_server_obj.enable_gnmi_server()
        logger.info("sleep 90 sec until validate stream updates")
        time.sleep(90)
        validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, flags=flags)


def validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, flags=''):
    with allure_step('Validate gnmi is running and stream updates'):
        validate_gnmi_enabled_and_running(gnmi_server_obj, engines)
        validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=False)
        port_description = Tools.RandomizationTool.get_random_string(7)
        change_port_description_and_validate_gnmi_updates(engines, port_description=port_description,
                                                          target_ip=target_ip, flags=flags)


@retry(Exception, tries=6, delay=2)
def validate_gnmi_server_docker_state(engines, should_run=True):
    cmd_output = engines.dut.run_cmd('docker ps |grep {}'.format(GnmiConsts.GNMI_DOCKER))
    should_run_str = '' if should_run else 'not'
    is_running_str = '' if cmd_output else 'not'
    assert bool(cmd_output) == should_run, f"The gnmi-server docker is {is_running_str} running, " \
                                           f"but we expect it {should_run_str} to run"


def validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_ENABLED,
                       gnmi_is_running=GnmiConsts.GNMI_IS_RUNNING):
    gnmi_server_obj.compare_show_gnmi_output(expected={GnmiConsts.GNMI_STATE_FIELD: gnmi_state,
                                                       GnmiConsts.GNMI_IS_RUNNING_FIELD: gnmi_is_running,
                                                       GnmiConsts.GNMI_VERSION_FIELD: GnmiConsts.GNMI_VERSION})
    should_run = gnmi_is_running == GnmiConsts.GNMI_IS_RUNNING
    validate_gnmi_server_docker_state(engines, should_run=should_run)


def validate_gnmi_enabled_and_running(gnmi_server_obj, engines):
    validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_ENABLED,
                       gnmi_is_running=GnmiConsts.GNMI_IS_RUNNING)


def validate_gnmi_disabled_and_not_running(gnmi_server_obj, engines):
    validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_DISABLED,
                       gnmi_is_running=GnmiConsts.GNMI_IS_NOT_RUNNING)


def run_gnmi_client_and_parse_output(engines, xpath, target_ip, target_port=GnmiConsts.GNMI_DEFAULT_PORT, flags=''):
    with allure_step("run gnmi-client and parse output"):
        sonic_mgmt_engine = engines.sonic_mgmt
        cmd = f"{GnmiConsts.GNMI_CLIENT_CMD} -target_addr {target_ip}:{target_port} -xpath '{xpath}' {flags}"
        logger.info(f"run on the sonic mgmt docker {sonic_mgmt_engine.ip}: {cmd}")
        if "-poll" == flags:
            gnmi_client_output = sonic_mgmt_engine.run_cmd_set([cmd, '\n', '\x03'], patterns_list=["Press enter to poll"])
            gnmi_client_output = re.sub(r".*xpath.*|Updated:|\^C(.*\n.*)*|\nPress enter to poll", '', gnmi_client_output)
        elif "-once" == flags:
            gnmi_client_output = sonic_mgmt_engine.run_cmd(cmd)
            gnmi_client_output = re.sub(r"Updated:", '', gnmi_client_output)
        else:
            gnmi_client_output = sonic_mgmt_engine.run_cmd_after_cmd([cmd, '\x03'])
            gnmi_client_output = re.sub(r".*xpath.*|Updated:|\^C(.*\n.*)*", '', gnmi_client_output)

        gnmi_updates_dict = {}
        for item in gnmi_client_output.split('\n'):
            if item.strip():
                item_as_list = item.split(":")
                key = re.sub(r"\s+\[|\]", '', item_as_list[0])
                value = re.sub(r"\r|\"", '', item_as_list[-1])
                gnmi_updates_dict.update({key: value})
        return gnmi_updates_dict


def change_port_description_and_validate_gnmi_updates(engines, port_description, target_ip, flags=''):
    selected_port = Tools.RandomizationTool.select_random_port().returned_value
    selected_port.ib_interface.set(NvosConst.DESCRIPTION, port_description, apply=True).verify_result()
    selected_port.update_output_dictionary()
    Tools.ValidationTool.verify_field_value_in_output(selected_port.show_output_dictionary, NvosConst.DESCRIPTION,
                                                      port_description).verify_result()

    xpath = f'/interfaces/interface[name={selected_port.name}]/state/description'
    logger.info(f"sleep {GnmiConsts.SLEEP_TIME_FOR_UPDATE} sec until we start validate the gnmi stream")
    time.sleep(GnmiConsts.SLEEP_TIME_FOR_UPDATE)
    gnmi_stream_updates = run_gnmi_client_and_parse_output(engines, xpath, target_ip, flags=flags)
    assert port_description in list(gnmi_stream_updates.values()), \
        "we expect to see the new port description in the gnmi-client output but we didn't.\n" \
        f"port description: {port_description}\n" \
        f"but got: {list(gnmi_stream_updates.values())}"


@retry(Exception, tries=3, delay=3)
def validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue):
    health_issues = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()[
        HealthConsts.ISSUES]
    error_msg = "gnmi-server is {} in the health issues".format("not" if expected_gnmi_health_issue else "")
    if expected_gnmi_health_issue:
        assert GnmiConsts.GNMI_DOCKER in list(health_issues.keys()), error_msg
    else:
        assert GnmiConsts.GNMI_DOCKER not in list(health_issues.keys()), error_msg
