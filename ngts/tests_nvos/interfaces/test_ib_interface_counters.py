import logging
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port, PortRequirements
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import SystemConsts, ApiType
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_clear_counters(engines, players, interfaces, start_sm, fae_param=""):
    """
    Clear counters test
    Commands:
        > nv action interface {port_name} link clear counters

    flow:
    1. Select a random port (which is up)
    2. Run traffic and identify which ports are connected to a traffic server
    3. Select a random traffic port
    4. Run clear counters for selected port
    5. Make sure the counters were cleared
    6. Run traffic and make sure the counters are not 0
    """
    _clear_counters_test_flow(engines, players, interfaces, False, fae_param)


@pytest.mark.ib_interfaces
def test_clear_all_counters(engines, players, interfaces, start_sm, fae_param=""):
    """
    Clear counters for all interfaces
    Commands:
        > nv action clear interface counters
    """
    _clear_counters_test_flow(engines, players, interfaces, True, fae_param)


def _clear_counters_test_flow(engines, players, interfaces, all_counters=False, fae_param=""):
    with allure.step("Get a random active port"):
        temp_selected_ports = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()

    with allure.step("Create a new user"):
        system = System(force_api=ApiType.NVUE)
        user_name, password = system.aaa.user.set_new_user(apply=True)
        user_id = system.aaa.user.get_lslogins(engine=engines.dut, username=user_name)["UID"]
        NvueGeneralCli.apply_config(engines.dut)
        file_name = "/tmp/portstat-{}".format(user_id)
        logging.info("User created: \nuser_name: {} \npassword: {} \nUID: {}".format(user_name, password, user_id))
        with allure.step("Crate an ssh connection for user {user_name} (UID {uid})".format(user_name=user_name,
                                                                                           uid=user_id)):
            ssh_connection = ConnectionTool.create_ssh_conn(engines.dut.ip,
                                                            user_name, password).get_returned_value()

    with allure.step("Clear counters for the default user"):
        temp_selected_ports[0].ib_interface.action_clear_counter_for_all_interfaces(engines.dut, fae_param).\
            verify_result()

        with allure.step('Send traffic through selected port'):
            Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

        with allure.step('Check selected port counters'):
            selected_ports = temp_selected_ports.copy()

            for port in temp_selected_ports:
                result = check_port_counters(port, False, engines.dut)
                if not result.result:
                    selected_ports.remove(port)

            assert len(selected_ports) != 0, "No traffic were detected"

            if not all_counters:
                selected_ports = [selected_ports[0]]
                check_port_counters(selected_ports[0], False, engines.dut).verify_result()
            check_port_counters(selected_ports[0], False, ssh_connection).verify_result()

    with allure.step("Clear counters for the a new user '{}'".format(user_name)):
        if all_counters:
            selected_ports[0].ib_interface.action_clear_counter_for_all_interfaces(ssh_connection, fae_param).\
                verify_result()
        else:
            clear_counters_for_user(ssh_connection, user_name, engines.dut.username, engines.dut,
                                    selected_ports[0], fae_param)

        with allure.step("Verify {} was created".format(file_name)):
            output = engines.dut.run_cmd("ls -l {}".format(file_name))
            assert "cannot access" not in output, file_name + " can't be found"

        with allure.step('Check selected port counters'):
            for port in selected_ports:
                check_port_counters(port, True, ssh_connection).verify_result()
            for port in selected_ports:
                check_port_counters(port, False, engines.dut).verify_result()

        with allure.step('Send traffic through selected port'):
            Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

        with allure.step('Check selected port counters'):
            for port in selected_ports:
                check_port_counters(port, False, ssh_connection).verify_result()
            for port in selected_ports:
                check_port_counters(port, False, engines.dut).verify_result()


def clear_counters_for_user(active_ssh_engine, active_user_name, inactive_user_name,
                            inactive_ssh_engine, selected_port, fae_param=""):
    with allure.step('Clear counter for selected port "{}" for user {}'.format(selected_port.name,
                                                                               active_ssh_engine.username)):
        selected_port.ib_interface.link.stats.clear_stats(dut_engine=active_ssh_engine, fae_param=fae_param).\
            verify_result()
        with allure.step('Check selected port counters for user ' + active_user_name):
            check_port_counters(selected_port, True, active_ssh_engine).verify_result()
        with allure.step('Check selected port counters for user ' + inactive_user_name):
            check_port_counters(selected_port, False, inactive_ssh_engine).verify_result()
        logging.info("The counters were cleared for port '{}' successfully".format(
            selected_port.name))


def check_port_counters(selected_port, should_be_zero, ssh_engine):
    logging.info("--- Counters for user: {}".format(ssh_engine.username))
    link_stats_dict = OutputParsingTool.parse_json_str_to_dictionary(
        selected_port.ib_interface.link.stats.show(dut_engine=ssh_engine)).get_returned_value()
    counters = link_stats_dict[IbInterfaceConsts.LINK_STATS_IN_BYTES]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_IN_DROPS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_IN_ERRORS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_IN_SYMBOL_ERRORS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_IN_PKTS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_OUT_BYTES]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_OUT_DROPS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_OUT_ERRORS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_OUT_PKTS]
    counters += link_stats_dict[IbInterfaceConsts.LINK_STATS_OUT_WAIT]
    return ResultObj((should_be_zero and not counters) or (counters and not should_be_zero), "")


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


# ------------ Open API tests -----------------

'''@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_clear_all_counters_openapi(engines, players, interfaces, start_sm):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_clear_all_counters(engines, players, interfaces, start_sm)


@pytest.mark.openapi
def test_ib_clear_counters_openapi(engines, players, interfaces, start_sm):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_clear_counters(engines, players, interfaces, start_sm)'''
