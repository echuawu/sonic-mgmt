import logging
import pytest
import re
import random

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port, PortRequirements
from ngts.nvos_tools.ib.InterfaceConfiguration.Interface import Interface
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import SystemConsts, ApiType, IbConsts
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


@pytest.mark.ib_interfaces
def test_range_clear_counters_negative(engines, players, interfaces, start_sm, fae_param=""):
    """
    verify all these commands fail with the right error message.
        1. nv action clear interface sw5-7p1-2 counters - out of range
        2. nv action clear interface sw5-1000p1-2 counters - out of range
        3. nv action clear interface sw7-5p1-2 counters - reversed range
        4. nv action clear interface sw5-7p2-1 counters - undefined p2-1
    """
    with allure.step("Get a random active port"):
        selected_ports = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()

    out_of_range_p, out_of_range_sw, reversed_range, undefined_range = create_invalid_ranges(selected_ports.name)
    error_msg1 = 'does not exist'
    error_msg2 = "is not a 'interface name'. Valid interface types are"

    with allure.step("Create Interface"):
        interface = Interface(parent_obj=None)

    with allure.step("check out of range {}".format(out_of_range_p)):
        interface.action_clear_counter_for_interface(interface_name=out_of_range_p)
        err_msg = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()
        assert error_msg1 not in err_msg, "action should fail with this error message: {}".format(error_msg1)

    with allure.step("check out of range {}".format(out_of_range_sw)):
        interface.action_clear_counter_for_interface(interface_name=out_of_range_sw)
        err_msg = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()
        assert error_msg1 not in err_msg, "action should fail with this error message: {}".format(error_msg1)

    with allure.step("check reversed range"):
        interface.action_clear_counter_for_interface(interface_name=reversed_range)
        err_msg = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()
        assert error_msg2 not in err_msg, "action should fail with this error message: {}".format(error_msg2)

    with allure.step("check undefined range"):
        interface.action_clear_counter_for_interface(interface_name=undefined_range)
        err_msg = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()
        assert error_msg2 not in err_msg, "action should fail with this error message: {}".format(error_msg2)


@pytest.mark.ib_interfaces
def test_range_clear_counters_positive(engines, players, interfaces, start_sm, fae_param=""):
    """
    verify all these commands fail with the right error message.
        0. get linked ports
        1. create new user
        2. run traffic
        3. pick random range - pick 4 points out of all interfaces list -
        4. nv action clear interface <point2>-<point3>p(1-1 or 2-2) link counters
        5. verify all clear counter files have been created under
        6. verify show counters command for traffic port != 0
        7. nv action clear interface <traffic port>-<point1>p1-2, <point 4> link counters
        8. verify files under user path
        9. verify show counters command for traffic port == 0
    """
    with allure.step("Create Interface"):
        interface = Interface(parent_obj=None)

    with allure.step("Get a random active port"):
        selected_ports = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()

    with allure.step("Get all IB ports sorted list"):
        sorted_list = interface.get_sorted_interfaces_list()

    file_name, user_name, ssh_connection = create_new_user(engines.dut)

    with allure.step('Send traffic through selected port'):
        Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

    with allure.step("Get 4 random numbers - to define ranges"):
        randoms = list(random.sample(range(2, len(sorted_list) - 1), 4))
        random.shuffle(randoms)
        with allure.step("define ranges"):
            reg = IbConsts.IB_INTERFACE_NAME_REGEX
            first_range_last_point = re.match(reg, sorted_list[randoms[0]]).group(2)
            second_range_first_point = re.match(reg, sorted_list[randoms[1]]).group(1) + re.match(reg, sorted_list[
                randoms[1]]).group(2)
            second_range_last_point = re.match(reg, sorted_list[randoms[2]]).group(2)
            random_port = sorted_list[randoms[3]]

    with allure.step("Run clear counters using range for p1 or p2 only"):
        with allure.step('Run clear counter command'):
            p_number = random.randint(1, 2)
            interface.action_clear_counter_for_interface(engine=ssh_connection,
                                                         interface_name='{first}-{last}p{p_number}-{p_number}, {random_port}'.format(
                                                             p_number=p_number, first=second_range_first_point,
                                                             last=second_range_last_point, random_port=random_port))

        with allure.step('verify that a clear file is added to each port'):
            all_files = ssh_connection.run_cmd('ls {}'.format(file_name)).split()
            missing_ports = [port for port in sorted_list[randoms[1]:randoms[2]] if port not in all_files]
            msg = "\n".join("{} is missing".format(port) for port in missing_ports)
            assert msg != "", msg

        with allure.step('verify show command output'):
            with allure.step('Check selected port counters'):
                for port in selected_ports:
                    check_port_counters(port, False, ssh_connection).verify_result()
                for port in selected_ports:
                    check_port_counters(port, False, engines.dut).verify_result()

    with allure.step("Run clear counters using range and multiple ports and verify results"):

        with allure.step('Run clear counter command'):
            interface.action_clear_counter_for_interface(engine=ssh_connection,
                                                         interface_name='{first}-{last}p1-2, {random_port}'.format(
                                                             first=selected_ports[0].name, last=first_range_last_point,
                                                             random_port=random_port))

        with allure.step('verify that a clear file is added to each port'):
            all_files = ssh_connection.run_cmd('ls {}'.format(file_name)).split()
            missing_ports = [port for port in sorted_list[:randoms[0]] if port not in all_files]
            msg = "\n".join("{} is missing".format(port) for port in missing_ports)
            assert msg != "", msg

        with allure.step('verify show command output'):
            with allure.step('Check selected port counters'):
                for port in selected_ports:
                    check_port_counters(port, True, ssh_connection).verify_result()
                for port in selected_ports:
                    check_port_counters(port, False, engines.dut).verify_result()


def _clear_counters_test_flow(engines, players, interfaces, all_counters=False, fae_param=""):
    with allure.step("Get a random active port"):
        temp_selected_ports = Tools.RandomizationTool.get_random_traffic_port().get_returned_value()

        file_name, user_name, ssh_connection = create_new_user(engines.dut)

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
            if not check_port_counters(selected_port, True, active_ssh_engine).result:
                raise Exception(f"The counters were not cleared for user: {active_user_name}")
        with allure.step('Check selected port counters for user ' + inactive_user_name):
            if not check_port_counters(selected_port, False, inactive_ssh_engine).result:
                raise Exception(f"The counters were cleared for user {inactive_user_name} "
                                f"while they shouldn't have been")
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
    return ResultObj((should_be_zero and counters < IbInterfaceConsts.MAX_COUNTERS_AFTER_CLEAR) or
                     (counters > IbInterfaceConsts.MAX_COUNTERS_AFTER_CLEAR and not should_be_zero), "")


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


def create_invalid_ranges(port_name):
    with allure.step('Create invalid interface ranges'):
        match = re.match(IbConsts.IB_INTERFACE_NAME_REGEX, port_name)
        assert match, "Invalid port name {}".format(port_name)
        prefix = match.group(1)
        numeric_part = int(match.group(2))

        out_of_range_p = prefix + str(numeric_part) + '-' + str(numeric_part + 2) + match.group(3)[0] + '3-5'
        out_of_range_sw = prefix + str(numeric_part) + '-' + str(numeric_part + 2000) + match.group(3)[0] + '1-2'
        reversed_range = prefix + str(numeric_part + 2) + '-' + str(numeric_part) + match.group(3)[0] + '1-2'
        undefined_range = prefix + str(numeric_part) + '-' + str(numeric_part + 2) + match.group(3)[0] + '2-1'

        return out_of_range_p, out_of_range_sw, reversed_range, undefined_range


def create_new_user(engine):
    with allure.step("Create a new user"):
        system = System(force_api=ApiType.NVUE)
        user_name, password = system.aaa.user.set_new_user(apply=True)
        user_id = system.aaa.user.get_lslogins(engine=engine, username=user_name)["UID"]
        file_name = "/tmp/portstat-{}".format(user_id)
        logging.info("User created: \nuser_name: {} \npassword: {} \nUID: {}".format(user_name, password, user_id))
        with allure.step("Crate an ssh connection for user {user_name} (UID {uid})".format(user_name=user_name,
                                                                                           uid=user_id)):
            ssh_connection = ConnectionTool.create_ssh_conn(engine.ip,
                                                            user_name, password).get_returned_value()
    return file_name, user_name, ssh_connection


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
