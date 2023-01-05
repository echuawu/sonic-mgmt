import logging
import pytest
import os
import allure
import string
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import SyslogConsts, SyslogSeverityLevels
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from infra.tools.redmine.redmine_api import *


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
    remote_server_engine = engines['sonic_mgmt']
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


def send_msg_to_server(msg, server_name, server_engine, protocol=None, priority=None, port=None, verify_msg_received=False,
                       verify_msg_didnt_received=False):
    with allure.step("Send msg to server {}".format(server_name)):
        logging.info("Send msg to server {}".format(server_name))
        protocol_flag = ' --{}'.format(protocol) if priority else ''  # must be tcp or udp
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
