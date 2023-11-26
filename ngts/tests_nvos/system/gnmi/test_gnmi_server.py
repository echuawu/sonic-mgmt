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
from infra.tools.general_constants.constants import DefaultConnectionValues


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
    gnmi_basic_flow(engines, mode='poll')


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
    gnmi_basic_flow(engines, mode='once')


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
    gnmi_basic_flow(engines, mode='')


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
            Tools.DatabaseTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_ID, "FEATURE|gnmi-server", "auto_restart", "disabled")
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
            Tools.DatabaseTool.redis_cli_hset(engines.dut, DatabaseConst.CONFIG_DB_ID, "FEATURE|gnmi-server", "auto_restart", "enabled")
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
        selected_port = Tools.RandomizationTool.select_random_port(requested_ports_state=None).returned_value
        xpath = f'interfaces/interface[name={selected_port.name}]/state/description'

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
        xpath = 'interfaces/interface[name=sw1p1]/state/counters/in-broadcast-pkts'
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
    selected_port = Tools.RandomizationTool.select_random_port(requested_ports_state=None).returned_value

    with allure_step(f"run {num_engines} gnmi_client sessions in the background"):
        for engine_id in range(num_engines):
            threads.append(run_gnmi_client_in_the_background(engines.dut.ip, f"interfaces/interface[name={selected_port.name}]/state/description"))

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
        assert gnmi_clients_without_updates == 0, f"{gnmi_clients_without_updates} gnmi clients didn't get updates..{output}"


@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_mapping_table(engines):
    """
    test will validate all the mapping tables between the redis DB data and the gnmic output
    """
    selected_port = Tools.RandomizationTool.select_random_port(requested_ports_state=None).returned_value
    port_name = selected_port.name
    infiniband_name = get_infiniband_name_from_port_name(engines.dut, port_name)
    port_oid = get_port_oid_from_infiniband_port(engines.dut, infiniband_name)
    with allure_step("Validate infiniband table mapping"):
        gnmi_list = create_gnmi_infiniband_list(port_name, port_oid, infiniband_name)
        validate_redis_cli_and_gnmi_commands_results(engines, gnmi_list)
    with allure_step("Validate interface state table mapping"):
        gnmi_list = create_interface_state_commands_list(port_name, infiniband_name)
        validate_redis_cli_and_gnmi_commands_results(engines, gnmi_list)
    with allure_step("Validate counter table mapping"):
        gnmi_list = create_gnmi_counter_list(port_name, port_oid)
        validate_redis_cli_and_gnmi_commands_results(engines, gnmi_list)


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
    prefix_and_path = xpath.rsplit("/", 1)
    command = f"gnmic -a {target_ip} --port {GnmiConsts.GNMI_DEFAULT_PORT} --skip-verify subscribe " \
              f"--prefix '{prefix_and_path[0]}' --path '{prefix_and_path[1]}' --target netq " \
              f"-u {DefaultConnectionValues.DEFAULT_USER} -p {DefaultConnectionValues.DEFAULT_PASSWORD} --format flat"
    # Use the subprocess.Popen function to run the command in the background
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return process


def gnmi_basic_flow(engines, mode='', ipv6=False):
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
    validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, mode=mode)

    with allure_step('Disable gnmi'):
        gnmi_server_obj.disable_gnmi_server()
        validate_gnmi_disabled_and_not_running(gnmi_server_obj, engines)
        validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=False)

    with allure_step('Enable gnmi'):
        gnmi_server_obj.enable_gnmi_server()
        validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, mode=mode)


def validate_gnmi_is_running_and_stream_updates(system, gnmi_server_obj, engines, target_ip, mode=''):
    with allure_step('Validate gnmi is running and stream updates'):
        validate_gnmi_enabled_and_running(gnmi_server_obj, engines)
        validate_gnmi_server_in_health_issues(system, expected_gnmi_health_issue=False)
        port_description = Tools.RandomizationTool.get_random_string(7)
        change_port_description_and_validate_gnmi_updates(engines, port_description=port_description,
                                                          target_ip=target_ip, mode=mode)


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
                                                       GnmiConsts.GNMI_IS_RUNNING_FIELD: gnmi_is_running})
    should_run = gnmi_is_running == GnmiConsts.GNMI_IS_RUNNING
    validate_gnmi_server_docker_state(engines, should_run=should_run)


def validate_gnmi_enabled_and_running(gnmi_server_obj, engines):
    validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_ENABLED,
                       gnmi_is_running=GnmiConsts.GNMI_IS_RUNNING)


def validate_gnmi_disabled_and_not_running(gnmi_server_obj, engines):
    validate_show_gnmi(gnmi_server_obj, engines, gnmi_state=GnmiConsts.GNMI_STATE_DISABLED,
                       gnmi_is_running=GnmiConsts.GNMI_IS_NOT_RUNNING)


def run_gnmi_client_and_parse_output(engines, xpath, target_ip, target_port=GnmiConsts.GNMI_DEFAULT_PORT, mode=''):
    with allure_step("run gnmi-client and parse output"):
        sonic_mgmt_engine = engines.sonic_mgmt
        prefix_and_path = xpath.rsplit("/", 1)
        mode_flag = f"--mode {mode}" if mode else ''
        cmd = f"gnmic -a {target_ip} --port {target_port} --skip-verify subscribe --prefix '{prefix_and_path[0]}'" \
              f" --path '{prefix_and_path[1]}' --target netq -u {DefaultConnectionValues.DEFAULT_USER} " \
              f"-p {DefaultConnectionValues.DEFAULT_PASSWORD} {mode_flag} --format flat"
        logger.info(f"run on the sonic mgmt docker {sonic_mgmt_engine.ip}: {cmd}")
        if "poll" == mode:
            gnmi_client_output = sonic_mgmt_engine.run_cmd_set([cmd, '\n', '\n', '\x03', '\x03'], patterns_list=["select target to poll:", "select subscription to poll:", "failed selecting target to poll:"])
            gnmi_client_output = re.findall(f"{re.escape(xpath)}:\\s+\\w+", gnmi_client_output)[0]
        elif "once" == mode:
            gnmi_client_output = sonic_mgmt_engine.run_cmd(cmd)
            gnmi_client_output = re.sub(r'(\\["\\n]+|\s+)', '', gnmi_client_output.split(":")[-1])
        else:
            gnmi_client_output = sonic_mgmt_engine.run_cmd_after_cmd([cmd, '\x03']).replace(cmd, '')
            gnmi_client_output = re.sub(r"\^C(.*\n.*)*", '', gnmi_client_output)
            gnmi_client_output = re.sub(r'(\\["\\n]+|\s+)', '', gnmi_client_output.split(":")[-1])

        gnmi_updates_dict = {}
        for item in gnmi_client_output.split('\n'):
            if item.strip():
                item_as_list = item.split(":")
                key = re.sub(r"\s+\[|\]", '', item_as_list[0])
                value = re.sub(r"\s|\r|\"", '', item_as_list[-1])
                gnmi_updates_dict.update({key: value})
        return gnmi_updates_dict


def change_port_description_and_validate_gnmi_updates(engines, port_description, target_ip, mode=''):
    selected_port = Tools.RandomizationTool.select_random_port(requested_ports_state=None).returned_value
    selected_port.ib_interface.set(NvosConst.DESCRIPTION, port_description, apply=True).verify_result()
    selected_port.update_output_dictionary()
    Tools.ValidationTool.verify_field_value_in_output(selected_port.show_output_dictionary, NvosConst.DESCRIPTION,
                                                      port_description).verify_result()

    xpath = f'interfaces/interface[name={selected_port.name}]/state/description'
    logger.info(f"sleep {GnmiConsts.SLEEP_TIME_FOR_UPDATE} sec until we start validate the gnmi stream")
    time.sleep(GnmiConsts.SLEEP_TIME_FOR_UPDATE)
    gnmi_stream_updates = run_gnmi_client_and_parse_output(engines, xpath, target_ip, mode=mode)
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


def create_gnmi_and_redis_cmd_dict(redis_cmd_db_num, redis_cmd_table, redis_cmd_key, xpath_gnmi_cmd, comparison_dict=None):
    gnmi_cmd_dict = {GnmiConsts.REDIS_CMD_DB_NAME: DatabaseConst.REDIS_DB_NUM_TO_NAME[redis_cmd_db_num],
                     GnmiConsts.REDIS_CMD_TABLE_NAME: redis_cmd_table,
                     GnmiConsts.REDIS_CMD_PARAM: redis_cmd_key,
                     GnmiConsts.XPATH_KEY: xpath_gnmi_cmd,
                     GnmiConsts.COMPARISON_KEY: comparison_dict}
    return gnmi_cmd_dict


def get_infiniband_name_from_port_name(engine, port_name):
    output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engine, asic="", db_name=DatabaseConst.APPL_DB_NAME,
                                                  db_config=f"\"ALIAS_PORT_MAP:{port_name}\"", param="name")
    # output = engine.run_cmd(f"redis-cli -n 0 HGET \"ALIAS_PORT_MAP:{port_name}\" \"name\"")
    infiniband_name = output.replace("\"", "")
    return infiniband_name


def get_port_oid_from_infiniband_port(engine, infiniband_port):
    output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engine, asic="", db_name=DatabaseConst.COUNTERS_DB_NAME,
                                                  db_config="COUNTERS_PORT_NAME_MAP", param=str(infiniband_port))
    # output = engine.run_cmd(f"redis-cli -n 2 HGET \"COUNTERS_PORT_NAME_MAP\" \"{infiniband_port}\"")
    port_oid = output.replace("\"", "")
    return port_oid


def create_interface_state_commands_list(port_name, infiniband_name):
    state_xpath = "interfaces/interface[name={port_name}]/state/{field}"
    gnmi_list = [create_gnmi_and_redis_cmd_dict(4, f"IB_PORT|{infiniband_name}", "admin_status",
                                                state_xpath.format(port_name=port_name, field="admin-status")),
                 create_gnmi_and_redis_cmd_dict(4, f"IB_PORT|{infiniband_name}", "index",
                                                state_xpath.format(port_name=port_name, field="ifindex")),
                 create_gnmi_and_redis_cmd_dict(4, f"IB_PORT|{infiniband_name}", "description",
                                                state_xpath.format(port_name=port_name, field="description")),
                 create_gnmi_and_redis_cmd_dict(4, f"IB_PORT|{infiniband_name}", "admin_status",
                                                state_xpath.format(port_name=port_name, field="enabled"),
                                                comparison_dict={"up": "true", "down": "false"})]
    return gnmi_list


def create_gnmi_counter_list(port_name, port_oid):
    state_xpath = "interfaces/interface[name={port_name}]/state/counters/{field}"
    gnmi_list = [create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_IN_PKTS_EXT",
                                                state_xpath.format(port_name=port_name, field="in-pkts")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_OUT_PKTS_EXT",
                                                state_xpath.format(port_name=port_name, field="out-pkts")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_PC_ERR_RCV_F",
                                                state_xpath.format(port_name=port_name, field="in-errors")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_ERR_XMTCONSTR_F",
                                                state_xpath.format(port_name=port_name, field="out-errors")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_IN_OCTETS_EXT",
                                                state_xpath.format(port_name=port_name, field="in-octets")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_OUT_OCTETS_EXT",
                                                state_xpath.format(port_name=port_name, field="out-octets")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_IN_PKTS_EXT",
                                                state_xpath.format(port_name=port_name, field="in-pkts")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_IN_PKTS_EXT",
                                                state_xpath.format(port_name=port_name, field="in-pkts")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_IF_IN_PKTS_EXT",
                                                state_xpath.format(port_name=port_name, field="in-pkts"))]
    return gnmi_list


def create_gnmi_infiniband_list(port_name, port_oid, infiniband_name):
    state_xpath = "interfaces/interface[name={port_name}]/infiniband/state/{field}"
    gnmi_list = [create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_LOGICAL_STATE",
                                                state_xpath.format(port_name=port_name, field="logical-port-state"),
                                                comparison_dict={"1": "Down",
                                                                 "2": "Initialize",
                                                                 "3": "Armed",
                                                                 "4": "Active"}),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_PHYSICAL_STATE",
                                                state_xpath.format(port_name=port_name, field="physical-port-state"),
                                                comparison_dict={"1": "Sleep",
                                                                 "2": "Polling",
                                                                 "3": "Disabled",
                                                                 "4": "PortConfigurationTraining",
                                                                 "5": "LINK_UP",
                                                                 "6": "LinkErrorRecovery",
                                                                 "7": "Phy Test",
                                                                 "8": "Disabled By Chassis Manager"}),
                 create_gnmi_and_redis_cmd_dict(6, f"IB_PORT_TABLE|{infiniband_name}", "speed_admin",
                                                state_xpath.format(port_name=port_name, field="supported-ib-speeds")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_SPEED_OPER",
                                                state_xpath.format(port_name=port_name, field="speed")),
                 create_gnmi_and_redis_cmd_dict(4, f"IB_PORT|{infiniband_name}", "auto_neg",
                                                state_xpath.format(port_name=port_name, field="speed-negotiate"),
                                                comparison_dict={'on': 'true', 'off': 'false'}),
                 create_gnmi_and_redis_cmd_dict(6, f"IB_PORT_TABLE|{infiniband_name}", "lanes_admin",
                                                state_xpath.format(port_name=port_name, field="supported-widths"),
                                                comparison_dict={"1": "1X",
                                                                 "2": "2X",
                                                                 "3": "1X_2X",
                                                                 "4": "4X",
                                                                 "5": "1X_4X",
                                                                 "6": "2X_4X",
                                                                 "7": "1X_2X_4X"}),
                 create_gnmi_and_redis_cmd_dict(6, f"IB_PORT_TABLE|{infiniband_name}", "mtu_max", state_xpath.format(port_name=port_name, field="max-supported-MTUs")),
                 create_gnmi_and_redis_cmd_dict(2, f"COUNTERS:{port_oid}", "SAI_PORT_STAT_INFINIBAND_MTU_OPER", state_xpath.format(port_name=port_name, field="mtu")),
                 create_gnmi_and_redis_cmd_dict(6, f"IB_PORT_TABLE|{infiniband_name}", "ib_subnet", state_xpath.format(port_name=port_name, field="ib-Subnet"),
                                                comparison_dict={"0": "infiniband-default", "1": "infiniband-1"}),
                 create_gnmi_and_redis_cmd_dict(6, f"IB_PORT_TABLE|{infiniband_name}", "vl_admin", state_xpath.format(port_name=port_name, field="vl-capabilities"),
                                                comparison_dict={"1": "VL0",
                                                                 "2": "VL0-VL1",
                                                                 "3": "VL0-VL2",
                                                                 "4": "VL0-VL3",
                                                                 "5": "VL0-VL4",
                                                                 "6": "VL0-VL5",
                                                                 "7": "VL0-VL6",
                                                                 "8": "VL0-VL7",
                                                                 "15": "VL0-VL14"})]
    return gnmi_list


def validate_redis_cli_and_gnmi_commands_results(engines, gnmi_list):
    sonic_mgmt_engine = engines.sonic_mgmt
    for command in gnmi_list:
        prefix_and_path = command[GnmiConsts.XPATH_KEY].rsplit("/", 1)
        cmd = f"gnmic -a {engines.dut.ip} --port {GnmiConsts.GNMI_DEFAULT_PORT} --skip-verify subscribe " \
              f"--prefix '{prefix_and_path[0]}' --path '{prefix_and_path[1]}' --target netq " \
              f"-u {DefaultConnectionValues.DEFAULT_USER} -p {DefaultConnectionValues.DEFAULT_PASSWORD} --mode once --format flat"
        logger.info(f"run on the sonic mgmt docker {sonic_mgmt_engine.ip}: {cmd}")
        gnmi_client_output = sonic_mgmt_engine.run_cmd(cmd)
        gnmi_client_output = re.sub(r'(\\["\\n]+|\s+)', '', gnmi_client_output.split(":")[-1])
        redis_output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engines.dut, asic="",
                                                            db_name=command[GnmiConsts.REDIS_CMD_DB_NAME],
                                                            db_config=f"\"{command[GnmiConsts.REDIS_CMD_TABLE_NAME]}\"",
                                                            param=command[GnmiConsts.REDIS_CMD_PARAM])
        # redis_output = engines.dut.run_cmd(command[GnmiConsts.REDIS_CMD_KEY]).replace("\"", "")
        if ',' in redis_output:
            redis_output = str(sorted(redis_output.split(',')))
            gnmi_client_output = str(sorted(gnmi_client_output.split(',')))
        if command[GnmiConsts.COMPARISON_KEY]:
            assert gnmi_client_output.lower() == command[GnmiConsts.COMPARISON_KEY][redis_output].lower()
        else:
            assert gnmi_client_output.lower() == redis_output.lower()
