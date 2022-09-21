
import logging
import allure
import pytest
import os

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port, PortRequirements
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_clear_counters(engines, players, interfaces):
    """
    Clear counters test
    Commands:
        > nv action interface {port_name} link clear stats

    flow:
    1. Select a random port (which is up)
    2. Run traffic and identify which ports are connected to a traffic server
    3. Select a random traffic port
    4. Run clear counters for selected port
    5. Make sure the counters were cleared
    6. Run traffic and make sure the counters are not 0
    """
    with allure.step("Get a random active port"):
        selected_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]
    user_name, password, user_id, file_name = "", "", "", ""
    system = None
    try:
        with allure.step("Create a new user"):
            system = System(None)
            user_name, password = system.create_new_user(engine=engines.dut)
            user_id = system.aaa.user.get_lslogins(engine=engines.dut, username=user_name)["UID"]
            system.aaa.user.set_username(user_name)
            system.aaa.user.set('role', SystemConsts.ROLE_CONFIGURATOR)
            NvueGeneralCli.apply_config(engines.dut)
            file_name = "/tmp/portstat-{}".format(user_id)
            logging.info("User created: \nuser_name: {} \npassword: {} \nUID: {}".format(user_name, password, user_id))
            with allure.step("Crate an ssh connection for user {user_name} (UID {uid})".format(user_name=user_name,
                                                                                               uid=user_id)):
                ssh_connection = ConnectionTool.create_ssh_conn(engines.dut.ip,
                                                                user_name, password).get_returned_value()

        with allure.step("Clear counters for the default user"):
            clear_counters_for_user(engines.dut, engines.dut.username, user_name, ssh_connection, selected_port)

            with allure.step('Send traffic through selected port'):
                Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

            with allure.step('Check selected port counters'):
                check_port_counters(selected_port, False, engines.dut).verify_result()
                check_port_counters(selected_port, False, ssh_connection).verify_result()

        with allure.step("Clear counters for the a new user '{}'".format(user_name)):
            clear_counters_for_user(ssh_connection, user_name, engines.dut.username, engines.dut, selected_port)
            with allure.step("Verify {} was created".format(file_name)):
                output = engines.dut.run_cmd("ls -l {}".format(file_name))
                assert "cannot access" not in output, file_name + " can't be found"

            with allure.step('Send traffic through selected port'):
                Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

            with allure.step('Check selected port counters'):
                check_port_counters(selected_port, False, ssh_connection).verify_result()
                check_port_counters(selected_port, False, engines.dut).verify_result()
    finally:
        with allure.step("Delete created user {}".format(user_name)):
            if system and system.aaa and system.aaa.user:
                system.aaa.user.unset()
                NvueGeneralCli.apply_config(engines.dut)
            if file_name:
                with allure.step("Verify {} was deleted".format(file_name)):
                    output = engines.dut.run_cmd("ls -l {}".format(file_name))
                    assert "cannot access" in output, file_name + " was not deleted"


def clear_counters_for_user(active_ssh_engine, active_user_name, inactive_user_name, inactive_ssh_engine, selected_port):
    with allure.step('Clear counter for selected port "{}" for user {}'.format(selected_port.name,
                                                                               active_ssh_engine.username)):
        selected_port.ib_interface.link.stats.clear_stats(dut_engine=active_ssh_engine).verify_result()
        with allure.step('Check selected port counters for user ' + active_user_name):
            check_port_counters(selected_port, True, active_ssh_engine).verify_result()
        with allure.step('Check selected port counters for user ' + inactive_user_name):
            check_port_counters(selected_port, False, inactive_ssh_engine).verify_result()
        logging.info("The counters were cleared for port '{}' successfully".format(selected_port.name))


def check_port_counters(selected_port, should_be_zero, ssh_engine):
    logging.info("--- Counters for user: {}".format(ssh_engine.username))
    counters = selected_port.ib_interface.link.stats.in_bytes.get_operational(engine=ssh_engine)
    counters += selected_port.ib_interface.link.stats.in_drops.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.in_errors.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.in_symbol_errors.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.in_pkts.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.out_bytes.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.out_drops.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.out_errors.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.out_pkts.get_operational(renew_show_cmd_output=False)
    counters += selected_port.ib_interface.link.stats.out_wait.get_operational(renew_show_cmd_output=False)
    return ResultObj((should_be_zero and not counters) or {counters and not should_be_zero}, "")


def get_port_obj(port_name):
    port_requirements_object = PortRequirements()
    port_requirements_object.set_port_name(port_name)
    port_requirements_object.set_port_state(NvosConsts.LINK_STATE_UP)
    port_requirements_object.set_port_type(IbInterfaceConsts.IB_PORT_TYPE)

    port_list = Port.get_list_of_ports(port_requirements_object=port_requirements_object)
    assert port_list and len(port_list) > 0, "Failed to create Port object for {}. " \
                                             "Make sure the name of the port is accurate and the state of " \
                                             "this port is UP".format(port_name)
    return port_list[0]
