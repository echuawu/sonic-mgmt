import logging
import pytest
import re
import time

from retry import retry
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.tools.test_utils.allure_utils import step as allure_step
from ngts.nvos_constants.constants_nvos import HealthConsts, NvosConst, DatabaseConst
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
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
def test_gnmi_basic_flow_stream(engines):
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
    gnmi_basic_flow(engines, flags='')


@pytest.mark.system
@pytest.mark.gnmi
def test_simulate_gnmi_server_failure(engines):
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
    system = System()
    gnmi_server_obj = system.gnmi_server
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)

    try:
        with allure_step('Simulate gnmi server failure'):
            Tools.RedisTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_NAME, "FEATURE|gnmi-server", "auto_restart", "disabled")
            engines.dut.run_cmd("docker stop gnmi-server")
            validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_ENABLED,
                               gnmi_is_running=GnmiConsts.GNMI_IS_NOT_RUNNING)
            logger.info("sleep 3 seconds until the health output will be updated")
            time.sleep(3)
            system.validate_health_status(HealthConsts.NOT_OK)
            health_issues = OutputParsingTool.parse_json_str_to_dictionary(system.health.show()).get_returned_value()[HealthConsts.ISSUES]
            assert GnmiConsts.GNMI_DOCKER in list(health_issues.keys()), f"{GnmiConsts.GNMI_DOCKER} is not in the " \
                                                                         f"health issues as we expect, after the " \
                                                                         f"gnmi-server failure"
            logger.info(f"{GnmiConsts.GNMI_DOCKER} appears in the health issues as we expect, "
                        f"after the gnmi-server failure")
    finally:
        with allure_step('re-enable gnmi server'):
            Tools.RedisTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_NAME, "FEATURE|gnmi-server", "auto_restart", "enable")
            engines.dut.run_cmd("docker start gnmi-server")
            validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, engines.dut.ip)


# ------------ test functions -----------------

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
        system.validate_health_status(HealthConsts.OK)

    with allure_step('Enable gnmi'):
        gnmi_server_obj.enable_gnmi_server()
        logger.info("sleep 90 sec until validate stream updates")
        time.sleep(90)
        validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, flags=flags)


def validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, flags='', port_name='sw1p1'):
    with allure_step('Validate gnmi is running and stream updates'):
        validate_gnmi_enabled_and_running(gnmi_server_obj, engines)
        system.validate_health_status(HealthConsts.OK)
        port_description = Tools.RandomizationTool.get_random_string(7)
        change_port_description_and_validate_gnmi_updates(engines, port_name=port_name, port_description=port_description,
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


def change_port_description_and_validate_gnmi_updates(engines, port_name, port_description, target_ip, flags=''):
    selected_port = Port(port_name, "", "")
    selected_port.ib_interface.set(NvosConst.DESCRIPTION, port_description, apply=True).verify_result()
    selected_port.update_output_dictionary()
    Tools.ValidationTool.verify_field_value_in_output(selected_port.show_output_dictionary, NvosConst.DESCRIPTION,
                                                      port_description).verify_result()

    xpath = f'/interfaces/interface[name={port_name}]/state/description'
    logger.info("sleep 35 sec until we start validate the gnmi stream")
    time.sleep(35)
    gnmi_stream_updates = run_gnmi_client_and_parse_output(engines, xpath, target_ip, flags=flags)
    assert port_description in list(gnmi_stream_updates.values()), \
        "we expect to see the new port description in the gnmi-client output but we didn't.\n" \
        f"port description: {port_description}\n" \
        f"but got: {list(gnmi_stream_updates.values())}"


# ------------ Open API tests -----------------


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_basic_flow_poll_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_gnmi_basic_flow_poll(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_basic_flow_once_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_gnmi_basic_flow_once(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_basic_flow_stream_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_gnmi_basic_flow_stream(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.gnmi
def test_simulate_gnmi_server_failure_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_simulate_gnmi_server_failure(engines)
