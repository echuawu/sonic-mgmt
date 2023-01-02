import logging
import pytest
import random
import allure
import string
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import SyslogConsts, SyslogSeverityLevels, NvosConst
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SonicMgmtContainer import SonicMgmtContainer


logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.syslog
def test_rsyslog_positive_minimal_flow(engines):
    """
    Will validate the minimal positive flow:
        set server and send UDP msg , verify the server get the msg and show commands

    Test flow:
    1. Configure remote syslog server
    2. Validate show commands
    3. Print msg that the server should catch, validate it gets the msg
    4. Print msg that the server should not catch, validate it doesnt get the msg
    5. Cleanup
    """
    remote_server_engine = engines[NvosConst.SONIC_MGMT]
    remote_server_ip = remote_server_engine.ip
    system = System()

    with allure.step("Configure remote syslog server {}".format(remote_server_ip)):
        logging.info("Configure remote syslog server {}".format(remote_server_ip))
        system.syslog.set_server(remote_server_ip, apply=True)

    try:
        with allure.step("Validate show commands"):
            logging.info("Validate show commands")
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            expected_syslog_dictionary = create_syslog_output_dictionary(server_dict={SyslogConsts.SERVER: expected_server_dictionary})
            system.syslog.verify_show_syslog_output(expected_syslog_dictionary)
            system.syslog.verify_show_servers_list([remote_server_ip])
            system.syslog.servers[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])

        random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
        send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)
    finally:
        with allure.step("Cleanup syslog configurations"):
            logging.info("Cleanup syslog configurations")
            system.syslog.unset_server(apply=True)


@pytest.mark.system
@pytest.mark.syslog
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
        server = system.syslog.set_server(remote_server_ip, apply=True)

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
    tmp_port = '500'    # in the system ports range

    with allure.step("Configure remote syslog server {}".format(remote_server_ip)):
        logging.info("Configure remote syslog server {}".format(remote_server_ip))
        system.syslog.set_server(remote_server_ip, apply=True)

    try:
        with allure.step("Validate show commands and send msg"):
            logging.info("Validate show commands and send msg")
            expected_server_dictionary = create_remote_server_dictionary(remote_server_ip)
            system.syslog.servers[remote_server_ip].verify_show_server_output(expected_server_dictionary[remote_server_ip])
            random_msg = RandomizationTool.get_random_string(30, ascii_letters=string.ascii_letters + string.digits)
            send_msg_to_server(random_msg, remote_server_ip, remote_server_engine, verify_msg_received=True)

        with allure.step("Change rsyslog port to non default port"):
            logging.info("Change rsyslog port to non default port")
            config_and_verify_rsyslog_port(system.syslog.servers[remote_server_ip], remote_server_engine,
                                           remote_server_ip, SyslogConsts.DEFAULT_PORT, tmp_port)
            config_and_verify_rsyslog_port(system.syslog.servers[remote_server_ip], remote_server_engine,
                                           remote_server_ip, tmp_port, '1500')
            tmp_port = '1500'   # out of system port range

        with allure.step("Change back rsyslog port to default port, just on switch"):
            logging.info("Change back rsyslog port to default port, just on switch")
            system.syslog.servers[remote_server_ip].set_port(SyslogConsts.DEFAULT_PORT, apply=True)
            system.syslog.servers[remote_server_ip].verify_show_server_output({SyslogConsts.PORT: SyslogConsts.DEFAULT_PORT})
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


def config_and_verify_rsyslog_port(server, remote_server_engine, remote_server_ip, old_port, new_port):
    with allure.step("Change rsyslog port to {}".format(new_port)):
        logging.info("Change rsyslog port to {}".format(new_port))
        server.set_port(new_port, apply=True)
        server.verify_show_server_output({SyslogConsts.PORT: new_port})
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
        server.verify_trap_severity_level(severity_level)

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
        priority_flag = ' --priority {}'.format(priority) if priority else ''
        port_flag = ' --port {}'.format(port) if port else ''
        extra_flags = protocol_flag + priority_flag + port_flag
        logger_cmd = 'logger {flags} \"{msg}\" '.format(flags=extra_flags, msg=msg)
        TestToolkit.engines.dut.run_cmd(logger_cmd)

        if verify_msg_received:
            with allure.step("Verify server {} received the msg".format(server_name)):
                logging.info("Verify server {} received the msg".format(server_name))
                verify_msg_in_syslog_file(server_engine, msg, should_find=True)
        elif verify_msg_didnt_received:
            with allure.step("Verify server {} did not receive the msg".format(server_name)):
                logging.info("Verify server {} did not receive the msg".format(server_name))
                verify_msg_in_syslog_file(server_engine, msg, should_find=False)


def verify_msg_in_syslog_file(engine, msg_to_find, syslog_file='/var/log/syslog', should_find=True):
    cmd = f'cat {syslog_file}|grep {msg_to_find}'
    output = engine.run_cmd(cmd)

    if output and not should_find:
        raise Exception("Found the message, but expected not to find it")
    elif not output and should_find:
        raise Exception("Didn't find the message, but expected to find it")

    logging.info("{} find the msg as expected".format('' if should_find else 'Did not'))


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
            SyslogConsts.PORT: port,
            SyslogConsts.PROTOCOL: protocol,
            SyslogConsts.VRF: vrf
        }
    }
    return dictionary
