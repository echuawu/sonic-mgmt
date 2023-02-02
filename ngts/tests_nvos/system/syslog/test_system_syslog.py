import logging
import pytest
import random
import allure
import string
import time
import re
import socket
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import SyslogConsts, SyslogSeverityLevels, NvosConst
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SonicMgmtContainer import SonicMgmtContainer
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_constants.constants_nvos import SystemConsts


logger = logging.getLogger()
INCOMPLETE_COMMAND = "Incomplete Command"
ERROR = "Error"
INVALID_COMMAND = "Invalid Command"


@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_positive_minimal_flow_by_hostname(engines):
    """
    Will validate the minimal positive flow:
        set server and send UDP msg , verify the server get the msg and show commands

    Test flow:
    1. Configure remote syslog server by hostname
    2. Validate show commands
    3. Print msg that the server should catch, validate it gets the msg
    4. Print msg that the server should not catch, validate it doesnt get the msg
    5. Cleanup
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_hostname = get_hostname_from_ip(remote_server_engine.ip)
    positive_minimal_flow(remote_server_engine, remote_server_hostname)


@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_positive_minimal_flow_by_ipv4(engines):
    """
    Will validate the minimal positive flow:
        set server and send UDP msg , verify the server get the msg and show commands

    Test flow:
    1. Configure remote syslog server by ipv4
    2. Validate show commands
    3. Print msg that the server should catch, validate it gets the msg
    4. Print msg that the server should not catch, validate it doesnt get the msg
    5. Cleanup
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    positive_minimal_flow(remote_server_engine, remote_server_engine.ip)


@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_multiple_servers_configuration(engines):
    """
    Validates the following:
    - Time to configure 1 and 10 servers should be similar (<< 1sec of difference)
    - No degradation in time to "nv show system syslog" when a lot servers are configured (10 for example)
    - Normal system resources utilization when a lot servers configured (10 for example)

    Test flow:
    1. configuring 1 single server and measuring its time.
    2. Measure "nv show system syslog" command time with 1 server configured.
    3. Check system resources utilization with 1 server.
    4. configuring 11 servers and measuring its time.
    5. Measure "nv show system syslog" command time with 11 server configured.
    6. Verify all configured servers displayed in show command
    7. Check system resources utilization with 11 servers.
    8. Compare between server configuration times.
    9. Compare between "nv show system syslog" command times.
    10. Compare between system resources utilization percentages.
    11. Cleanup
    """
    system = System()
    server_name = 'server_0'

    try:
        with allure.step("Configure 1 remote syslog server {}".format(server_name)):
            logging.info("Configure 1 remote syslog server {}".format(server_name))
            start_time = time.time()
            system.syslog.servers.set_server(server_name, apply=True)
            end_time = time.time()
            config_single_duration = end_time - start_time

        with allure.step("Calculate a single server show time"):
            logging.info("Calculate a single server show time")
            start_time = time.time()
            system.syslog.servers.show()
            end_time = time.time()
            show_single_duration = end_time - start_time

        with allure.step("Check system resources utilization"):
            logging.info("Check system resources utilization")
            output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("cpu")).get_returned_value()
            single_utilization = output_dictionary[SystemConsts.CPU_UTILIZATION_KEY]

        with allure.step("Configure 10 remote syslog servers"):
            logging.info("Configure 10 remote syslog servers")
            for x in range(1, SyslogConsts.MULTIPLE_SERVERS_NUMBER):
                server_name = 'server_' + str(x)
                system.syslog.servers.set_server(server_name, apply=False)
            server_name = 'server_10'
            start_time = time.time()
            system.syslog.servers.set_server(server_name, apply=True)
            end_time = time.time()
            config_multiple_duration = end_time - start_time

        with allure.step("Calculate 10 server configuration time"):
            logging.info("Calculate 10 server configuration time")
            start_time = time.time()
            system.syslog.servers.show()
            end_time = time.time()
            show_multiple_duration = end_time - start_time

        with allure.step("Verify all configured servers displayed in show command"):
            logging.info("Verify all configured servers displayed in show command")
            server_list = OutputParsingTool.parse_json_str_to_dictionary(
                system.syslog.servers.show()).get_returned_value()
            server_len = len(server_list)
            assert server_len == (SyslogConsts.MULTIPLE_SERVERS_NUMBER + 1), \
                "Number of servers configured is different than expected"

        with allure.step("Check system resources utilization"):
            logging.info("Check system resources utilization")
            output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.show("cpu")).get_returned_value()
            multiple_utilization = output_dictionary[SystemConsts.CPU_UTILIZATION_KEY]

        with allure.step("Verify configuration diff time"):
            logging.info("Verify configuration diff time")
            config_duration_diff = config_multiple_duration - config_single_duration
            assert config_duration_diff < SyslogConsts.CONFIG_TIME_DIFF_THRESHOLD, \
                "Configuration diff time: {actual} is higher than expected time: {expected}" \
                "".format(actual=config_duration_diff, expected=SyslogConsts.CONFIG_TIME_DIFF_THRESHOLD)

        with allure.step("Verify show diff time"):
            logging.info("Verify show diff time")
            show_duration_diff = show_multiple_duration - show_single_duration
            assert show_duration_diff < SyslogConsts.SHOW_TIME_DIFF_THRESHOLD, \
                "Show diff time: {actual} is higher than expected time: {expected}" \
                "".format(actual=show_duration_diff, expected=SyslogConsts.SHOW_TIME_DIFF_THRESHOLD)

        with allure.step("Verify system resources utilization diff percentages"):
            logging.info("Verify system resources utilization diff percentages")
            utilization_diff = multiple_utilization - single_utilization
            assert utilization_diff < SyslogConsts.CPU_UTILIZATION_DIFF_THRESHOLD, \
                "CPU utilization diff time: {actual} is higher than expected time: {expected}" \
                "".format(actual=utilization_diff, expected=SyslogConsts.CPU_UTILIZATION_DIFF_THRESHOLD)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_configurations():
    """
    will check rsyslog configurations

    Test flow:
    1. configure remote syslog servers : server_a, server_b
    2. validate show commands
    3. change global trap
    4. unset server_a
    5. validate show commands
    6. unset server
    7. validate show commands
    """
    system = System()
    server_a = 'server_a'
    server_b = 'server_b'

    with allure.step("Configure remote syslog servers"):
        logging.info("Configure remote syslog servers")
        system.syslog.servers.set_server(server_a, apply=True)
        system.syslog.servers.set_server(server_b, apply=True)

    try:
        with allure.step("Validate show commands"):
            logging.info("Validate show commands")
            expected_server_dictionary = create_remote_server_dictionary(server_a)
            expected_server_dictionary.update(create_remote_server_dictionary(server_b))
            expected_syslog_dictionary = create_syslog_output_dictionary(
                server_dict={SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.verify_show_servers_list([server_a, server_b])
            system.syslog.servers.servers_dict[server_a].verify_show_server_output(expected_server_dictionary[server_a])

        with allure.step("set server vrf and Validate"):
            logging.info("set server vrf and Validate")
            system.syslog.servers.servers_dict[server_a].set_vrf("mgmt", apply=True)
            expected_syslog_dictionary[SyslogConsts.SERVER][server_a].update({SyslogConsts.VRF: "mgmt"})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.servers_dict[server_a].verify_show_server_output(expected_server_dictionary[server_a])

        with allure.step("unset server vrf and Validate"):
            logging.info("unset server vrf and Validate")
            system.syslog.servers.servers_dict[server_a].unset_vrf(apply=True)
            expected_syslog_dictionary[SyslogConsts.SERVER][server_a].update({SyslogConsts.VRF: "default"})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.servers_dict[server_a].verify_show_server_output(expected_server_dictionary[server_a])

        with allure.step("Set global trap and Validate"):
            logging.info("Set global trap and Validate")
            severity_level = SyslogSeverityLevels.ERROR
            system.syslog.set_trap(severity_level, apply=True)
            expected_syslog_dictionary.update({SyslogConsts.TRAP: severity_level})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.servers_dict[server_a].verify_show_server_output(expected_server_dictionary[server_a])

        with allure.step("Unset {} and Validate".format(server_a)):
            logging.info("Unset {} and Validate".format(server_a))
            system.syslog.servers.unset_server(server_a, apply=True)
            expected_syslog_dictionary[SyslogConsts.SERVER].pop(server_a)
            system.syslog.servers.verify_show_servers_list([server_b])
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            server_list = OutputParsingTool.parse_json_str_to_dictionary(system.syslog.servers.show()).get_returned_value()
            assert server_a not in server_list, "Did not expect to see {} in the list of servers".format(server_a)

        with allure.step("Unset server and Validate"):
            logging.info("Unset server and Validate")
            system.syslog.servers.unset(apply=True)
            expected_syslog_dictionary[SyslogConsts.SERVER].pop(server_b)
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            server_list = OutputParsingTool.parse_json_str_to_dictionary(system.syslog.servers.show()).get_returned_value()
            assert server_b not in server_list, "Did not expect to see {} in the list of servers".format(server_b)

        with allure.step("Configure remote syslog server and validate unset syslog"):
            logging.info("Configure remote syslog server and validate unset syslog")
            system.syslog.servers.set_server(server_a, apply=True)
            expected_server_dictionary = create_remote_server_dictionary(server_a)
            expected_syslog_dictionary.update({SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.verify_show_servers_list([server_a])
            system.syslog.unset(apply=True)
            expected_syslog_dictionary[SyslogConsts.SERVER].pop(server_a)
            expected_syslog_dictionary.update({SyslogConsts.TRAP: SyslogSeverityLevels.NOTICE})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            server_list = OutputParsingTool.parse_json_str_to_dictionary(
                system.syslog.servers.show()).get_returned_value()
            assert server_a not in server_list, "Did not expect to see {} in the list of servers".format(server_a)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_server_severity_levels(engines):
    """
    Will validate all the severity options:  debug, info, notice, warning, error, critical, alert, emerg, none.
    Will configure the severity level, validate it in the show command and validate that the server catch the relevant
    msgs only.

    Test flow:
    * Configure remote syslog server
    To each severity level:
         * Set severity level
         * Validate with show command
         * Print msg that the server should catch, validate
         * Print msg that the server should not catch, validate
    * Unset server trap
    * Cleanup
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()

    with allure.step("Configure remote syslog server {}".format(remote_server_ip)):
        logging.info("Configure remote syslog server {}".format(remote_server_ip))
        server = system.syslog.servers.set_server(remote_server_ip, apply=True)

    try:
        with allure.step("Validate show commands"):
            logging.info("Validate show commands")
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            expected_syslog_dictionary = create_syslog_output_dictionary(
                server_dict={SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)

        with allure.step("Validate all severity levels"):
            logging.info("Validate all severity levels")
            for severity_level in SyslogSeverityLevels.SEVERITY_LEVEL_LIST:
                config_and_verify_trap(system.syslog, server, remote_server_ip, remote_server_engine, severity_level,
                                       global_severity_level=SyslogSeverityLevels.NOTICE)

            with allure.step("Validate none as severity level"):
                logging.info("Validate none as severity level")
                server.set_trap(SyslogSeverityLevels.NONE, apply=True)
                system.syslog.verify_global_severity_level(SyslogSeverityLevels.NOTICE)
                server.verify_trap_severity_level(SyslogSeverityLevels.NONE)
                random_msg = RandomizationTool.get_random_string(40, ascii_letters=string.ascii_letters + string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_didnt_received=True)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_server_and_global_severity_levels():
    """
    Will validate all the severity options:  debug, info, notice, warning, error, critical, alert, emerg, none.
    Will configure the severity level, validate it in the show command and validate that the server catch the relevant
    msgs only.

    Test flow:
    * Configure remote syslog server
    To each severity level:
         * Set severity level
         * Validate with show command
         * Print msg that the server should catch, validate
         * Print msg that the server should not catch, validate
    * Unset server trap
    * Cleanup
    """
    system = System()
    server_a_name = 'server_a'

    try:
        with allure.step("Configure remote syslog server and Validate"):
            logging.info("Configure remote syslog server and Validate")
            server_a = system.syslog.servers.set_server(server_a_name, apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.NOTICE])
            server_a.verify_trap_severity_level(None)

        with allure.step("Set global trap and Validate"):
            logging.info("Set global trap and Validate")
            system.syslog.set_trap(SyslogSeverityLevels.ERROR, apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
            server_a.verify_trap_severity_level(None)

        with allure.step("Unset server trap and Validate nothing change"):
            logging.info("Unset server trap and Validate nothing change")
            server_a.unset_trap(apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
            server_a.verify_trap_severity_level(None)

        with allure.step("set server trap and Validate"):
            logging.info("set server trap and Validate")
            server_a.set_trap(SyslogSeverityLevels.DEBUG, apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
            server_a.verify_trap_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.DEBUG])

        with allure.step("Unset server trap and Validate"):
            logging.info("Unset server trap and Validate")
            server_a.unset_trap(apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
            server_a.verify_trap_severity_level(None)

        with allure.step("Unset global trap and Validate"):
            logging.info("Unset global trap and Validate")
            system.syslog.unset_trap(apply=True)
            system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.NOTICE])
            server_a.verify_trap_severity_level(None)

        with allure.step("Validate unset global trap override server trap"):
            logging.info("Validate unset global trap override server trap")

            with allure.step("set global and server trap and Validate"):
                logging.info("set global and server trap and Validate")
                system.syslog.set_trap(SyslogSeverityLevels.ERROR, apply=True)
                server_a.set_trap(SyslogSeverityLevels.DEBUG, apply=True)
                system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
                server_a.verify_trap_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.DEBUG])

            with allure.step("Unset global trap and Validate"):
                logging.info("Unset global trap and Validate")
                system.syslog.unset_trap(apply=True)
                system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.NOTICE])
                server_a.verify_trap_severity_level(None)

        with allure.step("Validate set global trap override server trap"):
            logging.info("Validate global trap override server trap")

            with allure.step("set server trap and Validate"):
                logging.info("set server trap and Validate")
                server_a.set_trap(SyslogSeverityLevels.DEBUG, apply=True)
                system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.NOTICE])
                server_a.verify_trap_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.DEBUG])

            with allure.step("Set global trap and Validate"):
                logging.info("Set global trap and Validate")
                system.syslog.set_trap(SyslogSeverityLevels.ERROR, apply=True)
                system.syslog.verify_global_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[SyslogSeverityLevels.ERROR])
                server_a.verify_trap_severity_level(None)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_port(engines):
    """
    Will check the syslog with non default port
    we will check it with 2 ports number, one in the system ports range (0-1023) and the other out of this range.
    steps:
    1. configure remote server syslog
    2. change rsyslog port on switch and remote server
    3. validate with show command
    4. send msg , validate remote server get the msg
    5. Change back rsyslog port to default port, just on switch
    6. send msg , validate remote server didnt get the msg!
    7. Change back rsyslog port to default port on remote server
    8. send msg , validate remote server get the msg
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()
    tmp_port = 500    # in the system ports range

    with allure.step("Configure remote syslog server {}".format(remote_server_ip)):
        logging.info("Configure remote syslog server {}".format(remote_server_ip))
        system.syslog.servers.set_server(remote_server_ip, apply=True)

    try:
        with allure.step("Validate show commands and send msg"):
            logging.info("Validate show commands and send msg")
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])
            random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

        with allure.step("Change rsyslog port to non default port"):
            logging.info("Change rsyslog port to non default port")
            config_and_verify_rsyslog_port(system.syslog.servers.servers_dict[remote_server_ip], remote_server_engine,
                                           remote_server_ip, SyslogConsts.DEFAULT_PORT, tmp_port)
            config_and_verify_rsyslog_port(system.syslog.servers.servers_dict[remote_server_ip], remote_server_engine,
                                           remote_server_ip, tmp_port, 1500)
            tmp_port = 1500   # out of system port range

        with allure.step("Change back rsyslog port to default port, just on switch"):
            logging.info("Change back rsyslog port to default port, just on switch")
            system.syslog.servers.servers_dict[remote_server_ip].unset_port(apply=True)
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output({SyslogConsts.PORT: str(SyslogConsts.DEFAULT_PORT)})
            random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_didnt_received=True)

        with allure.step("Change back rsyslog port to default port on remote server"):
            logging.info("Change back rsyslog port to default port on remote server")
            SonicMgmtContainer.change_rsyslog_port(remote_server_engine, tmp_port, SyslogConsts.DEFAULT_PORT, 'udp',
                                                   restart_rsyslog=True)
            random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)
            SonicMgmtContainer.change_rsyslog_port(remote_server_engine, tmp_port, SyslogConsts.DEFAULT_PORT, 'udp',
                                                   restart_rsyslog=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_protocol(engines):
    """
    Will check the syslog protocol options: TCP and UDP
    Steps:
        1. configure a remote syslog server
        2. config syslog protocol to udp
        3. validate with show commands
        4. send a msg and validate server recieved it
        5. config syslog protocol to tcp
        6. validate with show commands
        7. send a msg and validate server recieved it
        8. simulate a disconnection, by stop the rsyslog process
        9. send a msg and validate server did not recieve it
        10. reconnect , restart the rsyslog process
        11. send a msg and validate server recieved it
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()

    with allure.step("Configure remote syslog server {}".format(remote_server_ip)):
        logging.info("Configure remote syslog server {}".format(remote_server_ip))
        system.syslog.servers.set_server(remote_server_ip, apply=True)

    try:
        with allure.step("Validate show commands"):
            logging.info("Validate show commands")
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])

        config_and_verify_rsyslog_protocol(system.syslog.servers.servers_dict[remote_server_ip], remote_server_engine,
                                           remote_server_ip, 'udp')
        config_and_verify_rsyslog_protocol(system.syslog.servers.servers_dict[remote_server_ip], remote_server_engine,
                                           remote_server_ip, 'tcp')

        with allure.step("Disconnect and Reconnect to server"):
            logging.info("Disconnect and Reconnect to server")

            with allure.step("Simulate disconnection to the server"):
                logging.info("Simulate disconnection to the server")
                remote_server_engine.run_cmd('/etc/init.d/rsyslog stop')
                random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_didnt_received=True)

            with allure.step("Reconnect to the server"):
                logging.info("Reconnect to the server")
                remote_server_engine.run_cmd('rm -f /var/run/rsyslogd.pid')
                remote_server_engine.run_cmd('rsyslogd')
                time.sleep(30)
                random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

            with allure.step("Unset syslog server protocol"):
                logging.info("Unset syslog server protocol")
                system.syslog.servers.servers_dict[remote_server_ip].unset_protocol(apply=True)
                system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output({SyslogConsts.PROTOCOL: 'udp'})

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_filter(engines):
    """
    Will check the rsyslog filter options: exclude and include.
    Validate that the server will get only the relevant messages.
    Test flow:
    1. configure remote syslog server with exclude filter
    2. validate with show commands and send msgs
    3. configure remote syslog server with include filter
    4. validate with show commands and send msgs
    5. unset filter
    6. validate with show commands and send msgs
    """

    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()

    try:
        with allure.step("Configure remote syslog server {} with exclude filter and validate".format(remote_server_ip)):
            logging.info("Configure remote syslog server {} with exclude filter and validate".format(remote_server_ip))
            system.syslog.servers.set_server(remote_server_ip, apply=True)
            exclude_regex = "a+"
            system.syslog.servers.servers_dict[remote_server_ip].set_filter(SyslogConsts.EXCLUDE, exclude_regex, apply=True)
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            expected_server_dictionary[remote_server_ip].update({SyslogConsts.FILTER: {SyslogConsts.EXCLUDE: exclude_regex}})
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])

            with allure.step("Send message with the exclude filter regex,\n"
                             "expect message not to be recieved over the remote server"):
                logging.info("Send message with the exclude filter regex,\n"
                             "expect message not to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(exclude_regex + random_msg, remote_server_ip, remote_server_engine,
                                   verify_msg_didnt_received=True)

            with allure.step("Send message without the exclude filter regex but with lower trap level,\n"
                             "expect message not to be recieved over the remote server"):
                logging.info("Send message without the exclude filter regex but with lower trap level,\n"
                             "expect message not to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, priority=SyslogSeverityLevels.DEBUG,
                                   verify_msg_didnt_received=True)

            with allure.step("Send message without the exclude filter regex,\n"
                             "expect message to be recieved over the remote server"):
                logging.info("Send message without the exclude filter regex,\n"
                             "expect message to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

            with allure.step("Configure long regex for the exclude filter and validate"):
                logging.info("Configure long regex for the exclude filter and validate")
                long_exclude_regex = RandomizationTool.get_random_string(200, ascii_letters=string.digits + string.ascii_letters)
                system.syslog.servers.servers_dict[remote_server_ip].set_filter(SyslogConsts.EXCLUDE, long_exclude_regex, apply=True)
                expected_server_dictionary[remote_server_ip].update(
                    {SyslogConsts.FILTER: {SyslogConsts.EXCLUDE: long_exclude_regex}})
                system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(
                    expected_server_dictionary[remote_server_ip])
                with allure.step("Send message without the exclude filter regex,\n"
                                 "expect message to be recieved over the remote server"):
                    logging.info("Send message without the exclude filter regex,\n"
                                 "expect message to be recieved over the remote server")
                    random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                    send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

        with allure.step("Configure remote syslog server {} with include filter and validate".format(remote_server_ip)):
            logging.info("Configure remote syslog server {} with include filter and validate".format(remote_server_ip))
            include_regex = "b+"
            system.syslog.servers.servers_dict[remote_server_ip].set_filter(SyslogConsts.INCLUDE, include_regex, apply=True)
            expected_server_dictionary[remote_server_ip].update({SyslogConsts.FILTER: {SyslogConsts.INCLUDE: include_regex}})
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])

            with allure.step("Send message without the include filter regex,\n"
                             "expect message not to be recieved over the remote server"):
                logging.info("Send message without the include filter regex,\n"
                             "expect message not to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_didnt_received=True)

            with allure.step("Send message with the include filter regex but with lower trap level,\n"
                             "expect message not to be recieved over the remote server"):
                logging.info("Send message with the include filter regex but with lower trap level,\n"
                             "expect message not to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(include_regex + random_msg, remote_server_ip, remote_server_engine,
                                   priority=SyslogSeverityLevels.DEBUG, verify_msg_didnt_received=True)

            with allure.step("Send message with the include filter regex,\n"
                             "expect message to be recieved over the remote server"):
                logging.info("Send message with the include filter regex,\n"
                             "expect message to be recieved over the remote server")
                random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
                send_msg_to_server(include_regex + random_msg, remote_server_ip, remote_server_engine,
                                   verify_msg_received=True)

            with allure.step("Configure long regex for the include filter and validate"):
                logging.info("Configure long regex for the include filter and validate")
                long_include_regex = RandomizationTool.get_random_string(200, ascii_letters=string.digits + string.ascii_letters)
                system.syslog.servers.servers_dict[remote_server_ip].set_filter(SyslogConsts.INCLUDE, long_include_regex, apply=True)
                expected_server_dictionary[remote_server_ip].update(
                    {SyslogConsts.FILTER: {SyslogConsts.INCLUDE: long_include_regex}})
                system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(
                    expected_server_dictionary[remote_server_ip])
                with allure.step("Send message with the include filter regex,\n"
                                 "expect message to be recieved over the remote server"):
                    logging.info("Send message with the include filter regex,\n"
                                 "expect message to be recieved over the remote server")
                    send_msg_to_server(long_include_regex, remote_server_ip, remote_server_engine,
                                       verify_msg_received=True)

        with allure.step("Unset filter and validate"):
            logging.info("Unset filter and validate")
            system.syslog.servers.servers_dict[remote_server_ip].unset_filter(apply=True)
            expected_server_dictionary[remote_server_ip].pop(SyslogConsts.FILTER)
            system.syslog.servers.servers_dict[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])
            random_msg = RandomizationTool.get_random_string(20, ascii_letters=string.digits)
            send_msg_to_server(exclude_regex + random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_format(engines):
    """
    Will validate all the format options:  standard, welf.
    Will configure the syslog format, validate it in the show command and in the syslog file.
    Test flow:
    1. configure remote syslog server
    2. validate with show commands
    3. send a msg and validate server recieved it and its not in welf format
    4. configure welf format
    5. validate with show command and on the remote syslog server
    6. configure welf firewall-nme
    7. validate with show command and on the remote syslog server
    8. unset welf firewall-nme
    9.  validate with show command and on the remote syslog server
    """

    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()

    try:
        with allure.step("Configure remote syslog server {} and validate".format(remote_server_ip)):
            logging.info("Configure remote syslog server {} and validate".format(remote_server_ip))
            system.syslog.servers.set_server(remote_server_ip, apply=True)
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            expected_syslog_dictionary = create_syslog_output_dictionary(
                server_dict={SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.verify_show_syslog_format_output({SyslogConsts.FORMAT: {SyslogConsts.STANDARD: {}}})
            send_random_msg_and_validate_format(remote_server_ip, remote_server_engine, expect_welf_format=False)

        with allure.step("Set welf format and validate"):
            logging.info("Set welf format and validate")
            system.syslog.format.set(SyslogConsts.WELF, apply=True)
            expected_syslog_dictionary[SyslogConsts.FORMAT] = {SyslogConsts.WELF: {}}
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.verify_show_syslog_format_output({SyslogConsts.FORMAT: {SyslogConsts.WELF: {}}})
            send_random_msg_and_validate_format(remote_server_ip, remote_server_engine, expect_welf_format=True)

        with allure.step("Set firewall name and validate"):
            logging.info("Set firewall name and validate")
            firewall_name = RandomizationTool.get_random_string(6, ascii_letters=string.ascii_letters)
            system.syslog.format.welf.set_firewall_name(firewall_name, apply=True)
            expected_syslog_dictionary[SyslogConsts.FORMAT] = expected_syslog_dictionary[SyslogConsts.FORMAT] \
                if TestToolkit.tested_api == ApiType.NVUE else {SyslogConsts.WELF:
                                                                {SyslogConsts.FIREWAL_NAME: firewall_name}}
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.verify_show_syslog_format_output({SyslogConsts.FORMAT: {SyslogConsts.WELF:
                                                                                  {SyslogConsts.FIREWAL_NAME:
                                                                                   firewall_name}}})
            send_random_msg_and_validate_format(remote_server_ip, remote_server_engine, expect_welf_format=True,
                                                firewall_name=firewall_name)

        with allure.step("Unset firewall name and validate"):
            logging.info("Unset firewall name and validate")
            system.syslog.format.welf.unset_firewall_name(apply=True)
            expected_syslog_dictionary[SyslogConsts.FORMAT] = {SyslogConsts.WELF: {}}
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.verify_show_syslog_format_output({SyslogConsts.FORMAT: {SyslogConsts.WELF: {}}})
            send_random_msg_and_validate_format(remote_server_ip, remote_server_engine, expect_welf_format=True)

    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset(apply=True)


@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_bad_params():
    """
    Will check all the commands that get params, with bad params- empty or random
    """

    system = System()
    rand_str = RandomizationTool.get_random_string(10)
    server_name = RandomizationTool.get_random_string(5)

    with allure.step("Global syslog commands"):
        logging.info("Global syslog commands")

        with allure.step("Configure and validate trap"):
            logging.info("Configure and validate trap")
            system.syslog.set_trap("", expected_str=INCOMPLETE_COMMAND)
            system.syslog.set_trap(rand_str, expected_str=ERROR)

        # TODO change when bug 3317235 will be fixed
        # with allure.step("Configure and validate format"):
            # logging.info("Configure and validate format")
            # system.syslog.format.set("",expected_str=INCOMPLETE_COMMAND)
            # system.syslog.format.set(rand_str, expected_str=ERROR)

    with allure.step("Specific syslog server commands"):
        logging.info("Specific syslog server commands")
        system.syslog.servers.set_server(server_name, apply=False)

        with allure.step("Configure and validate port"):
            logging.info("Configure and validate port")
            system.syslog.servers.servers_dict[server_name].set_port("", expected_str=INCOMPLETE_COMMAND)
            system.syslog.servers.servers_dict[server_name].set_port(rand_str, expected_str=INVALID_COMMAND)

        with allure.step("Configure and validate protocol"):
            logging.info("Configure and validate protocol")
            system.syslog.servers.servers_dict[server_name].set_protocol("", expected_str=INCOMPLETE_COMMAND)
            system.syslog.servers.servers_dict[server_name].set_protocol(rand_str, expected_str=ERROR)

        with allure.step("Configure and validate trap"):
            logging.info("Configure and validate trap")
            system.syslog.servers.servers_dict[server_name].set_trap("", expected_str=INCOMPLETE_COMMAND)
            system.syslog.servers.servers_dict[server_name].set_trap(rand_str, expected_str=ERROR)

        with allure.step("Configure and validate vrf"):
            logging.info("Configure and validate vrf")
            system.syslog.servers.servers_dict[server_name].set_vrf("", expected_str=INCOMPLETE_COMMAND)
            system.syslog.servers.servers_dict[server_name].set_vrf(rand_str, expected_str=ERROR)

        with allure.step("Configure and validate filter"):
            logging.info("Configure and validate filter")
            # system.syslog.servers.servers_dict[server_name].set_filter("", "", expected_str=INCOMPLETE_COMMAND)  # bug #3325876
            system.syslog.servers.servers_dict[server_name].set_filter(rand_str, rand_str, expected_str=INVALID_COMMAND)

        with allure.step("Configure and validate filter include"):
            logging.info("Configure and validate filter include")
            system.syslog.servers.servers_dict[server_name].set_filter(SyslogConsts.INCLUDE, "", expected_str=INCOMPLETE_COMMAND)
            # system.syslog.servers.servers_dict[server_name].filter.unset_include_filter("", expected_str=INVALID_COMMAND) # bug #3325876

        with allure.step("Configure and validate filter exclude"):
            logging.info("Configure and validate filter exclude")
            system.syslog.servers.servers_dict[server_name].set_filter(SyslogConsts.EXCLUDE, "", expected_str=INCOMPLETE_COMMAND)
            # system.syslog.servers.servers_dict[server_name].filter.unset_exclude_filter("", expected_str=INVALID_COMMAND) # bug #3325876

    with allure.step("Cleanup syslog configurations"):
        logging.info("Cleanup syslog configurations")
        system.syslog.unset(apply=True)


def verify_welf_format(line_to_check, firewall_name=".*", expect_welf_format=True):
    welf_format_regex = "id=firewall time=\".*\" fw=\"{}\" pri=\\d msg=\".*\"".format(firewall_name)
    result = re.findall(welf_format_regex, line_to_check)
    with allure.step("Verify msg format"):
        logging.info("Verify msg format")
        logger.info("This line : \n {}\n is {} in welf format".format(line_to_check, "" if result else "not"))
        logger.info("result : {}".format(result))
        if expect_welf_format:
            assert result, "Expect the line to be in welf format, but it was not"
        else:
            assert not result, "Expect the line not to be in welf format, but it was"


def send_random_msg_and_validate_format(remote_server_ip, remote_server_engine, expect_welf_format, firewall_name=".*"):
    random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
    output = send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)
    verify_welf_format(output, expect_welf_format=expect_welf_format, firewall_name=firewall_name)


def config_and_verify_rsyslog_protocol(server, remote_server_engine, remote_server_ip, protocol):
    with allure.step("Change rsyslog protocol to {}".format(protocol)):
        logging.info("Change rsyslog protocol to {}".format(protocol))
        server.set_protocol(protocol, apply=True)
        server.verify_show_server_output({SyslogConsts.PROTOCOL: protocol})
        random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
        send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)


def config_and_verify_rsyslog_port(server, remote_server_engine, remote_server_ip, old_port, new_port):
    with allure.step("Change rsyslog port to {}".format(new_port)):
        logging.info("Change rsyslog port to {}".format(new_port))
        server.set_port(new_port, apply=True)
        server.verify_show_server_output({SyslogConsts.PORT: str(new_port)})
        try:
            SonicMgmtContainer.change_rsyslog_port(remote_server_engine, old_port, new_port, 'udp', restart_rsyslog=True)
            random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)
        except Exception as err:
            SonicMgmtContainer.change_rsyslog_port(remote_server_engine, old_port, new_port, 'udp', restart_rsyslog=True)
            raise err


def config_and_verify_trap(syslog, server, server_name, server_engine, severity_level,
                           global_severity_level=SyslogSeverityLevels.NOTICE):
    with allure.step("Configure and verify severity level: {}".format(severity_level)):
        logging.info("Validate severity level: {}".format(severity_level))
        server.set_trap(severity_level, apply=True)
        syslog.verify_global_severity_level(global_severity_level)
        server.verify_trap_severity_level(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[severity_level])

        random_msg = RandomizationTool.get_random_string(40, ascii_letters=string.ascii_letters + string.digits)
        severity_level_index = SyslogSeverityLevels.SEVERITY_LEVEL_LIST.index(severity_level)
        send_msg_to_server(random_msg, server_name, server_engine, priority=severity_level,
                           verify_msg_received=True,
                           verify_msg_didnt_received=False)

        if severity_level_index + 1 < len(SyslogSeverityLevels.SEVERITY_LEVEL_LIST):
            random_msg = RandomizationTool.get_random_string(40, ascii_letters=string.ascii_letters + string.digits)
            rand_recieved_level = random.choice(SyslogSeverityLevels.SEVERITY_LEVEL_LIST[severity_level_index + 1:])
            send_msg_to_server(random_msg, server_name, server_engine, priority=rand_recieved_level,
                               verify_msg_received=True,
                               verify_msg_didnt_received=False)
        if severity_level_index > 0:
            rand_not_recieved_level = random.choice(SyslogSeverityLevels.SEVERITY_LEVEL_LIST[:severity_level_index])
            random_msg = RandomizationTool.get_random_string(35, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, server_name, server_engine, priority=rand_not_recieved_level,
                               verify_msg_received=False,
                               verify_msg_didnt_received=True)


def send_msg_to_server(msg, server_name, server_engine, protocol=None, priority=None, port=None, verify_msg_received=False,
                       verify_msg_didnt_received=False):
    with allure.step("Send msg to server {}".format(server_name)):
        logging.info("Send msg to server {}".format(server_name))
        protocol_flag = ' --{}'.format(protocol) if protocol else ''  # must be tcp or udp
        priority_flag = ' --priority {}'.format(SyslogSeverityLevels.SEVERITY_LEVEL_DICT[priority]) if priority else ''
        port_flag = ' --port {}'.format(port) if port else ''
        extra_flags = protocol_flag + priority_flag + port_flag
        logger_cmd = 'logger {flags} \"{msg}\" '.format(flags=extra_flags, msg=msg)
        TestToolkit.engines.dut.run_cmd(logger_cmd)
        output = ''

        if verify_msg_received:
            with allure.step("Verify server {} received the msg".format(server_name)):
                logging.info("Verify server {} received the msg".format(server_name))
                output = verify_msg_in_syslog_file(server_engine, msg, should_find=True)
        elif verify_msg_didnt_received:
            with allure.step("Verify server {} did not receive the msg".format(server_name)):
                logging.info("Verify server {} did not receive the msg".format(server_name))
                verify_msg_in_syslog_file(server_engine, msg, should_find=False)
        return output


def verify_msg_in_syslog_file(engine, msg_to_find, syslog_file='/var/log/syslog', should_find=True):
    cmd = f'cat {syslog_file}|grep {msg_to_find}'
    output = engine.run_cmd(cmd)

    if output and not should_find:
        raise Exception("Found the message, but expected not to find it")
    elif not output and should_find:
        raise Exception("Didn't find the message, but expected to find it")

    logging.info("{} find the msg as expected".format('' if should_find else 'Did not'))
    return output


def create_syslog_output_dictionary(format=SyslogConsts.STANDARD, format_dict={}, trap=SyslogSeverityLevels.NOTICE,
                                    server_dict=None):
    dictionary = {
        SyslogConsts.FORMAT: {format: format_dict},
        SyslogConsts.TRAP: trap
    }
    if server_dict:
        dictionary.update(server_dict)
    return dictionary


def create_remote_server_dictionary(server_name, port=SyslogConsts.DEFAULT_PORT, protocol='udp', vrf='default'):
    dictionary = {
        server_name: {
            SyslogConsts.PORT: str(port),
            SyslogConsts.PROTOCOL: protocol,
            SyslogConsts.VRF: vrf
        }
    }
    return dictionary


def positive_minimal_flow(remote_server_engine, remote_server):
    system = System()

    with allure.step("Configure remote syslog server: {}".format(remote_server)):
        logging.info("Configure remote syslog server: {}".format(remote_server))
        system.syslog.servers.set_server(remote_server, apply=True)

    try:
        with allure.step("Validate show commands"):
            logging.info("Validate show commands")
            expected_server_dictionary = create_remote_server_dictionary(remote_server)
            expected_syslog_dictionary = create_syslog_output_dictionary(server_dict={SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.servers.verify_show_servers_list([remote_server])
            system.syslog.servers.servers_dict[remote_server].verify_show_server_output(expected_server_dictionary[remote_server])

        random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
        send_msg_to_server(random_msg, remote_server, remote_server_engine, verify_msg_received=True)
    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.servers.unset(apply=True)


def get_hostname_from_ip(ip):
    host_name_index = 0
    hostname_str = socket.gethostbyaddr(ip)[host_name_index]
    return remove_mlnx_lab_suffix(hostname_str)


def remove_mlnx_lab_suffix(hostname_string):
    """
    Returns switch hostname without mlnx lab prefix
    :param hostname_string: 'arc-switch1030.mtr.labs.mlnx'
    :return: arc-switch1030
    """
    host_name_index = 0
    return hostname_string.split('.')[host_name_index]


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_bad_params_openapi():
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_bad_params()


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_format_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_format(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_filter_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_filter(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_protocol_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_protocol(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_port_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_port(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_server_and_global_severity_levels_openapi():
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_server_and_global_severity_levels()


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_server_severity_levels_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_server_severity_levels(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
@pytest.mark.simx
def test_rsyslog_configurations_openapi():
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_configurations()


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_positive_minimal_flow_openapi_by_hostname(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_positive_minimal_flow_by_hostname(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_positive_minimal_flow_openapi_by_ipv4(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_rsyslog_positive_minimal_flow_by_ipv4(engines)
