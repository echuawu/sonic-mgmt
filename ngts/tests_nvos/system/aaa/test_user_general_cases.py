import logging
import random
import allure
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool

logger = logging.getLogger()


def test_delete_user_with_multiple_terminals(engines):
    """
    Test flow:
            1. create new user random [viewer, configurator]
            2. connect multiple times using the new user
            3. delete new user
            5. verify the user name is not exist if delete.
                all the terminals are not connected if disconnect, disable
            6. same steps for a  user
    """
    connections_number = 5
    system = System(None)
    connections = []
    engine = system.create_new_connected_user(engine=engines.dut)
    connections.append(engine)
    for i in range(0, connections_number - 1):
        connections.append(ConnectionTool.create_ssh_conn(engine.ip, engine.username, engine.password).verify_result())

    with allure.step('delete {username} with {conn} connection'.format(username=engine.username, conn=connections_number)):
        system.aaa.user.set_username(engine.username)
        system.aaa.user.unset()
        NvueGeneralCli.apply_config(engines.dut)
        verify_after_delete(system, engine.username, engines.dut)


def test_disconnect_user_with_multiple_terminals(engines):
    """
    Test flow:
            1. create new user random [viewer, configurator]
            2. connect multiple times using the new user
            3. disconnect new user
            5. verify the user name is not exist if delete.
                all the terminals are not connected if disconnect, disable
            6. same steps for a  user
    """
    connections_number = 3
    system = System(None)
    connections = []
    engine = system.create_new_connected_user(engine=engines.dut)
    connections.append(engine)
    for i in range(0, connections_number - 1):
        connections.append(ConnectionTool.create_ssh_conn(engine.ip, engine.username, engine.password).verify_result())

    with allure.step('disconnect {username} with {conn} connection'.format(username=engine.username, conn=connections_number)):
        output = system.aaa.user.action_disconnect(engine.username)
        verify_after_disconnect(engines.dut, system, output, engine.username, engine.password, connections_number)


def test_disable_user_with_multiple_terminals(engines):
    """
    Test flow:
            1. create new user random [viewer, configurator]
            2. connect multiple times using the new user
            3. disable new user
            5. verify the user name is not exist if delete.
                all the terminals are not connected if disconnect, disable
            6. same steps for a  user
    """
    connections_number = 3
    system = System(None)
    connections = []
    engine = system.create_new_connected_user(engine=engines.dut)
    connections.append(engine)
    for i in range(0, connections_number - 1):
        connections.append(ConnectionTool.create_ssh_conn(engine.ip, engine.username, engine.password).verify_result())

    with allure.step('disconnect {username} with {conn} connection'.format(username=engine.username, conn=connections_number)):
        system.aaa.user.set_username(engine.username)
        system.aaa.user.set(SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED)
        NvueGeneralCli.apply_config(engines.dut)
        verify_after_disable(engines.dut, system, engine.username, engine.password, connections_number)


def test_disconnect_nonuser(engines):
    """
    Test flow:
            1. generate username
            2. run nv action disconnect system aaa user <username>
            3. verify output message includes "No such user"

    """
    system = System(None)
    username = system.aaa.user.generate_username()
    system.aaa.user.set_username(username)
    output = NvueSystemCli.action_disconnect(engines.dut, system.aaa.user.get_resource_path().replace('/', ' '))
    assert 'does not exist' in output, "{username} is not a user!".format(username=username)


def verify_after_disconnect(dut_engine, system, action_output, username, password, connections_count):
    """

    :param action_output: the output after running nv action disconnect
    :param dut_engine: dut engine
    :param system: system obj
    :param username: username
    :param password: user password
    :param connections_count: connections count
    :return:
    """
    with allure.step('verify after disconnecting username: {user}'.format(user=username)):
        with allure.step('verify disconnect action succeeded'.format(user=username)):
            assert 'Action succeeded' in action_output, "could not disconnect {user}".format(user=username)

        with allure.step('verify {user} state still enabled'.format(user=username)):
            outpout = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(outpout, SystemConsts.USER_STATE,
                                                        SystemConsts.USER_STATE_ENABLED).verify_result()
        with allure.step('verify {user} running processes count'.format(user=username)):
            running_processes = system.aaa.user.get_lslogins(dut_engine, username)[
                SystemConsts.PASSWORD_HARDENING_RUNNING_PROCESSES]
            assert int(running_processes) is connections_count, "connections count is {run_proc} not as expected {expected}".format(
                run_proc=running_processes, expected=connections_count)

        ConnectionTool.create_ssh_conn(dut_engine.ip, username, password).verify_result()
        with allure.step('verify {user} running processes count after the new connection'.format(user=username)):
            running_processes = system.aaa.user.get_lslogins(dut_engine, username)[
                SystemConsts.PASSWORD_HARDENING_RUNNING_PROCESSES]
            assert int(running_processes) is connections_count + 2, "connections count is {run_proc} not as expected {expected}".format(
                run_proc=running_processes, expected=connections_count + 2)


def verify_after_disable(dut_engine, system, username, password, connections_count):
    """

    :param dut_engine: dut engine
    :param system: system obj
    :param username: username
    :param password: user password
    :param connections_count: connections count
    :return:
    """
    with allure.step('verify after disabling username: {user}'.format(user=username)):
        with allure.step('verify {user} state is disabled'.format(user=username)):
            show_output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(show_output, SystemConsts.USER_STATE, SystemConsts.USER_STATE_DISABLED).verify_result()

        with allure.step('verify running processes count is 5'.format(user=username)):
            running_processes = system.aaa.user.get_lslogins(dut_engine, username)[
                SystemConsts.PASSWORD_HARDENING_RUNNING_PROCESSES]
            assert int(running_processes) is connections_count, "connections count is {run_proc} not as expected {expected}".format(
                run_proc=running_processes, expected=connections_count)

        with allure.step('verify we can not connect with {user}'.format(user=username)):
            try:
                ConnectionTool.create_ssh_conn(dut_engine.ip, username, password)
            except Exception:
                running_processes = system.aaa.user.get_lslogins(dut_engine, username)[SystemConsts.PASSWORD_HARDENING_RUNNING_PROCESSES]
                assert int(running_processes) is connections_count, "connections count is {run_proc} not as expected {expected}".format(run_proc=running_processes, expected=connections_count)


def verify_after_delete(system, username, dut_engine):
    """

    :param system: system obj
    :param username: username
    :param dut_engine: dut engine
    :return:
    """
    with allure.step('verify after delete username: {user}'.format(user=username)):
        with allure.step('check {user} show command'.format(user=username)):
            system.aaa.user.set_username('')
            show_output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
            assert username not in show_output.keys(), "the show output is: {out} not as expected".format(
                out=show_output)

        with allure.step('check if {user} in config_DB'.format(user=username)):
            redis_outpt = dut_engine.run_cmd('sudo redis-cli -n 4 keys * | grep {user}'.format(user=username))
            assert not redis_outpt, "a deleted user key still in the config db"

        with allure.step('check if {user} in all users list'.format(user=username)):
            show_output = system.aaa.user.get_lslogins(engine=dut_engine, username=username)
            assert "lslogins: cannot found '{username}'".format(username=username) in show_output, "a deleted username still users list".format(out=show_output)
