import logging
import allure
import pytest
from retry import retry

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port, PortRequirements

logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_interface_mtu(engines, players, interfaces, traffic_ports):
    """
    Configure port mtu and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set/unset interface <name> link mtu
    -	nv show interface <name> link

    flow:
    1. Select a random port (state of which is up)
    2. Select a random mtu value
    3. Set the mtu value to selected one
    4. Verify the mtu value is updated to selected value
    5. Send traffic -> Verify the traffic passes successfully
    6. Unset the mtu value -> should changed to default
    7. If the default mtu value is not equal to the original:
        7.1 Restore the original mtu value
        7.2 Verify the mtu restored to original
    8. Send traffic -> Verify the traffic passes successfully
    """
    with allure.step("Get a random functional port"):
        selected_port_name = Tools.RandomizationTool.select_random_value(traffic_ports).get_returned_value()
        selected_port = get_port_obj(selected_port_name)

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current MTU value"):
        current_mtu_value = selected_port.ib_interface.link.mtu.get_operational()
        logging.info("Current mtu value of port '{}' is: {}".format(selected_port.name, current_mtu_value))

    with allure.step("Get the max supported MTU value"):
        max_supported_mtu = selected_port.ib_interface.link.max_supported_mtu.get_operational(
            renew_show_cmd_output=False)
        logging.info("Max supported mtu: {}".format(max_supported_mtu))

    with allure.step("Select a random MTU value for port {}".format(selected_port.name)):
        mtu_values = [str(value) for value in IbInterfaceConsts.MTU_VALUES if value <= int(max_supported_mtu)]
        selected_mtu_value = Tools.RandomizationTool.select_random_value(mtu_values,
                                                                         [str(current_mtu_value)]).get_returned_value()

    with allure.step("Set mtu '{}' for port '{}".format(selected_mtu_value, selected_port.name)):
        selected_port.ib_interface.link.mtu.set(value=selected_mtu_value, apply=True,
                                                ask_for_confirmation=True).verify_result()

        with allure.step("Verify the mtu value updated to: {}".format(selected_mtu_value)):
            wait_for_port_to_become_active(selected_port)
            verify_value_updated_correctly(selected_port.ib_interface.link.mtu, selected_mtu_value)

    with allure.step("Unset MTU for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.mtu.unset(apply=True, ask_for_confirmation=True).verify_result()

        with allure.step("Verify the MTU is updated to default: {}".format(IbInterfaceConsts.DEFAULT_MTU)):
            wait_for_port_to_become_active(selected_port)
            verify_value_updated_correctly(selected_port.ib_interface.link.mtu, str(IbInterfaceConsts.DEFAULT_MTU))

    if current_mtu_value != IbInterfaceConsts.DEFAULT_MTU:
        with allure.step("Restore original mtu value ({})".format(current_mtu_value)):
            selected_port.ib_interface.link.mtu.set(value=current_mtu_value, apply=True,
                                                    ask_for_confirmation=True).verify_result()

            with allure.step("Verify the mtu value was restored to: {}".format(current_mtu_value)):
                wait_for_port_to_become_active(selected_port)
                verify_value_updated_correctly(selected_port.ib_interface.link.mtu, str(current_mtu_value))


@pytest.mark.ib_interfaces
def test_ib_interface_speed(engines, players, interfaces, devices, traffic_ports):
    """
    Configure interface speed and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set/unset interface <name> link speed/ib_speed
    -	nv show interface <name> link

    flow:
    1. Select a random port (state of which is up)
    2. Select a random speed value
    3. Set the speed to selected one
    4. Verify the speed value is updated to selected value (speed and ib_speed)
    5. Send traffic -> Verify the traffic passes successfully
    6. Select a random ib_speed value
    7. Set the ib_speed to selected one
    8. Verify the speed is updated to selected value (speed and ib_speed)
    9. Unset the speed value -> should changed to default
    9. Unset the ib-speed value -> should changed to default
    10.Send traffic -> Verify the traffic passes successfully
    """
    with allure.step("Get a random functional port"):
        selected_port_name = Tools.RandomizationTool.select_random_value(traffic_ports).get_returned_value()
        selected_port = get_port_obj(selected_port_name)

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current speed value"):
        current_speed_value = selected_port.ib_interface.link.speed.get_operational()
        current_ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational()
        logging.info("Current speed value of port '{}' is: {}".format(selected_port.name, current_speed_value))
        logging.info("Current ib-speed value of port '{}' is: {}".format(selected_port.name, current_ib_speed_value))
        assert IbInterfaceConsts.SPEED_LIST[current_ib_speed_value] == str(current_speed_value), \
            "ib-speed {} value is not equal to speed value {}".format(current_ib_speed_value, current_speed_value)

    with allure.step("Get the supported link ib-speeds"):
        supported_ib_speeds = selected_port.ib_interface.link.supported_ib_speeds.get_operational(
            renew_show_cmd_output=False)
        logging.info("Supported ib-speeds: {}".format(supported_ib_speeds))
        supported_ib_speeds = supported_ib_speeds.split(',')

        with allure.step("Verify max supported speed is correct"):
            check_for_max_supported_speeds(devices, supported_ib_speeds, current_speed_value)

    '''with allure.step("Select a random speed value for port {}".format(selected_port.name)):
        selected_speed_value = Tools.RandomizationTool.select_random_value(supported_speeds, current_speed_value)
        logging.info("Selected speed: " + selected_speed_value)

    with allure.step("Set speed '{}' for port '{}".format(selected_speed_value, selected_port.name)):
        selected_port.ib_interface.link.speed.set(value=selected_speed_value, apply=True).verify_result()

        with allure.step("Verify the speed value updated to: {}".format(selected_speed_value)):
            speed_value = selected_port.ib_interface.link.speed.get_operational()
            Tools.ValidationTool.compare_values(speed_value, selected_speed_value, True).verify_result()

        with allure.step('Verify the speed value is equal to ib-speed value'):
            ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational(False)
            Tools.ValidationTool.compare_values(speed_value, IbInterfaceConsts.SPEED_LIST[ib_speed_value],
                                                True).verify_result()

        with allure.step("Verify the traffic passes successfully"):
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces, should_success=True'''

    with allure.step("Select a random ib-speed value for port {}".format(selected_port.name)):
        selected_ib_speed_value = Tools.RandomizationTool.select_random_value(list(devices.dut.supported_ib_speeds.keys()),
                                                                              [current_ib_speed_value]).get_returned_value()
        logging.info("Selected ib-speed: " + selected_ib_speed_value)

    with allure.step("Set ib-speed '{}' for port '{}".format(selected_ib_speed_value, selected_port.name)):
        selected_port.ib_interface.link.ib_speed.set(value=selected_ib_speed_value, apply=True,
                                                     ask_for_confirmation=True).verify_result()

        with allure.step("Verify the ib-speed value updated to: {}".format(selected_ib_speed_value)):
            wait_for_port_to_become_active(selected_port)
            verify_value_updated_correctly(selected_port.ib_interface.link.ib_speed, str(selected_ib_speed_value))

        with allure.step("Get the supported link ib-speeds"):
            supported_ib_speeds = selected_port.ib_interface.link.supported_ib_speeds.get_operational(
                renew_show_cmd_output=False)
            logging.info("Supported ib-speeds: {}".format(supported_ib_speeds))
            supported_ib_speeds = supported_ib_speeds.split(',')

            with allure.step("Verify max supported speed is correct"):
                check_for_max_supported_speeds(devices, supported_ib_speeds,
                                               IbInterfaceConsts.SPEED_LIST[selected_ib_speed_value])

        with allure.step('Verify the speed value is equal to ib-speed value'):
            speed_value = selected_port.ib_interface.link.speed.get_operational(False)
            ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational(False)
            Tools.ValidationTool.compare_values(speed_value, IbInterfaceConsts.SPEED_LIST[ib_speed_value],
                                                True).verify_result()
            assert IbInterfaceConsts.SPEED_LIST[ib_speed_value] == str(speed_value), \
                "ib-speed {} value is not equal to speed value {}".format(ib_speed_value, speed_value)

        with allure.step('Verify traffic'):
            Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

    '''with allure.step("Unset speed for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.speed.unset(apply=True).verify_result()'''

    with allure.step("Unset ib_speed for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.ib_speed.unset(apply=True, ask_for_confirmation=True).verify_result()

    with allure.step("Restore {} speed to {}".format(selected_port.name, current_ib_speed_value)):
        selected_port.ib_interface.link.ib_speed.set(value=current_ib_speed_value, apply=True,
                                                     ask_for_confirmation=True).verify_result()

        with allure.step("Verify the ib-speed value updated to: {}".format(current_ib_speed_value)):
            wait_for_port_to_become_active(selected_port)
            verify_value_updated_correctly(selected_port.ib_interface.link.ib_speed, str(current_ib_speed_value))


@pytest.mark.ib_interfaces
def test_ib_interface_speed_invalid(engines, traffic_ports, devices):
    """
    Try to set an invalid speed and make sure the config apply fails
    """
    with allure.step("Get a random functional port"):
        selected_port_name = Tools.RandomizationTool.select_random_value(traffic_ports).get_returned_value()
        selected_port = get_port_obj(selected_port_name)

    TestToolkit.update_tested_ports([selected_port])

    invalid_speed = "invalid_speed"
    with allure.step("Set an invalid ib-speed '{}' for port '{}".format(invalid_speed, selected_port.name)):
        selected_port.ib_interface.link.ib_speed.set(value=invalid_speed, apply=False).verify_result(False)

    invalid_speeds = devices.dut.invalid_ib_speeds
    if invalid_speeds:
        invalid_speed = Tools.RandomizationTool.select_random_value(list(invalid_speeds.keys())).get_returned_value()
        with allure.step("Set an invalid ib-speed '{}' for port '{}".format(invalid_speed, selected_port.name)):
            selected_port.ib_interface.link.ib_speed.set(value=invalid_speed, apply=False).verify_result()

            with allure.step("Try to apply invalid configuration and expect failure"):
                Tools.SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config,
                                                      engines.dut, False).verify_result(False)


@pytest.mark.ib_interfaces
def test_ib_interface_lanes(engines, players, interfaces, traffic_ports):
    """
    Configure port lanes and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set/unset interface <name> link lanes
    -	nv show interface <name> link

    flow:
    1. Select a random port (state of which is up)
    2. Select a random lane value
    3. Set the lane value to selected one
    4. Verify the lane value is updated to selected value
    5. Send traffic -> Verify the traffic passes successfully
    6. Unset the lanes value -> should changed to default
    7. If the default lanes value is not equal to the original:
        7.1 Restore the original lanes value
        7.2 Verify the lanes restored to original
    8. Send traffic -> Verify the traffic passes successfully
    """
    with allure.step("Get a random functional port"):
        selected_port_name = Tools.RandomizationTool.select_random_value(traffic_ports).get_returned_value()
        selected_port = get_port_obj(selected_port_name)

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current supported lanes"):
        current_supported_lanes = selected_port.ib_interface.link.supported_lanes.get_operational()
        current_lanes = selected_port.ib_interface.link.lanes.get_operational()
        logging.info("Current lanes value of port '{}' is: {}".format(selected_port.name, current_lanes))
        logging.info("Current supported-lanes value of port '{}' is: {}".format(selected_port.name,
                                                                                current_supported_lanes))

    with allure.step("Select a random lanes for port {}".format(selected_port.name)):
        selected_lanes = Tools.RandomizationTool.select_random_value(IbInterfaceConsts.SUPPORTED_LANES,
                                                                     [current_supported_lanes]).get_returned_value()

    with allure.step("Set lanes to '{}' for port '{}".format(selected_lanes, selected_port.name)):
        selected_port.ib_interface.link.lanes.set(value=selected_lanes, apply=True,
                                                  ask_for_confirmation=True).verify_result()

        with allure.step("Verify the lanes value updated to: {}".format(selected_lanes)):
            wait_for_port_to_become_active(selected_port)
            verify_value_is_contained_in_output(selected_port.ib_interface.link.lanes, str(selected_lanes))

        with allure.step('Verify traffic'):
            Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

    with allure.step("Unset lanes for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.lanes.unset(apply=True, ask_for_confirmation=True).verify_result()

        with allure.step("Verify the lanes is updated to default: {}".format(IbInterfaceConsts.DEFAULT_LANES)):
            wait_for_port_to_become_active(selected_port)
            verify_value_is_contained_in_output(selected_port.ib_interface.link.lanes,
                                                str(IbInterfaceConsts.DEFAULT_LANES))

    if current_supported_lanes != IbInterfaceConsts.DEFAULT_LANES:
        with allure.step("Restore original lanes value ({})".format(current_supported_lanes)):
            selected_port.ib_interface.link.lanes.set(value=current_supported_lanes, apply=True,
                                                      ask_for_confirmation=True).verify_result()

            with allure.step("Verify the lanes value was restored to: {}".format(current_supported_lanes)):
                wait_for_port_to_become_active(selected_port)
                verify_value_updated_correctly(selected_port.ib_interface.link.supported_lanes,
                                               IbInterfaceConsts.DEFAULT_LANES)
                verify_value_is_contained_in_output(selected_port.ib_interface.link.lanes,
                                                    str(IbInterfaceConsts.DEFAULT_LANES))


@pytest.mark.ib_interfaces
def test_ib_interface_vls(engines, players, interfaces, traffic_ports):
    """
    Configure port vls and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set/unset interface <name> link op-vls
    -	nv show interface <name> link

    flow:
    1. Select a random port (state of which is up)
    2. Select a random op-vls value
    3. Set the op-vls value to selected one
    4. Verify the op-vls value is updated to selected value
    5. Send traffic -> Verify the traffic passes successfully
    6. Unset the op-vls value -> should changed to default
    7. If the default op-vls value is not equal to the original:
        7.1 Restore the original op-vls value
        7.2 Verify the op-vls restored to original
    8. Send traffic -> Verify the traffic passes successfully
    """
    with allure.step("Get a random functional port"):
        selected_port_name = Tools.RandomizationTool.select_random_value(traffic_ports).get_returned_value()
        selected_port = get_port_obj(selected_port_name)

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current supported op-vls"):
        current_supported_op_vls = selected_port.ib_interface.link.operational_vls.get_operational()
        logging.info("Current op_vls value of port '{}' is: {}".format(selected_port.name, current_supported_op_vls))
        current_vl_capabilities = selected_port.ib_interface.link.vl_admin_capabilities.get_operational()
        logging.info("Current vl capabilities value of port '{}' is: {}".format(selected_port.name,
                                                                                current_vl_capabilities))

    with allure.step("Select a random op_vls for port {}".format(selected_port.name)):
        selected_op_vls = Tools.RandomizationTool.select_random_value(IbInterfaceConsts.SUPPORTED_VLS,
                                                                      [current_vl_capabilities]).get_returned_value()

    with allure.step("Set op_vls to '{}' for port '{}".format(selected_op_vls, selected_port.name)):
        selected_port.ib_interface.link.operational_vls.set(value=selected_op_vls, apply=True,
                                                            ask_for_confirmation=True).verify_result()

        with allure.step("Verify vl-capabilities value updated to: {}".format(selected_op_vls)):
            wait_for_port_to_become_active(selected_port)
            verify_value_is_contained_in_output(selected_port.ib_interface.link.vl_admin_capabilities,
                                                str(selected_op_vls))

    with allure.step("Unset op_vls for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.operational_vls.unset(apply=True, ask_for_confirmation=True).verify_result()

        with allure.step("Verify the op_vls is updated to default: {}".format(IbInterfaceConsts.DEFAULT_VLS)):
            wait_for_port_to_become_active(selected_port)
            verify_value_is_contained_in_output(selected_port.ib_interface.link.vl_admin_capabilities,
                                                str(IbInterfaceConsts.DEFAULT_VLS))

    if current_vl_capabilities != IbInterfaceConsts.DEFAULT_VLS:
        with allure.step("Restore original op_vls value ({})".format(current_supported_op_vls)):
            selected_port.ib_interface.link.operational_vls.set(value=current_supported_op_vls,
                                                                apply=True,
                                                                ask_for_confirmation=True).verify_result()

            with allure.step("Verify the op_vls value was restored to: {}".format(current_vl_capabilities)):
                wait_for_port_to_become_active(selected_port)
                verify_value_is_contained_in_output(selected_port.ib_interface.link.vl_admin_capabilities,
                                                    str(current_vl_capabilities))


def check_for_max_supported_speeds(devices, supported_ib_speeds, current_speed):
    max_supported_speed = max(int(devices.dut.supported_ib_speeds[ib_speed].replace("G", "")) for ib_speed in supported_ib_speeds)
    assert max_supported_speed <= int(current_speed.replace("G", "")), "The list of supported speeds is incorrect"


@retry(Exception, tries=10, delay=10)
def wait_for_port_to_become_active(port_obj):
    with allure.step("Waiting for port {} to become active".format(port_obj.name)):
        logical_state = port_obj.ib_interface.link.logical_port_state.get_operational()
        state = port_obj.ib_interface.link.state.get_operational()
        assert logical_state == "Active" and state == "up", \
            "The logical state of interface {} is not 'Active'".format(port_obj.name)


def verify_value_updated_correctly(selected_port_obj, selected_value):
    new_value = selected_port_obj.get_operational()
    Tools.ValidationTool.compare_values(str(new_value), selected_value, True).verify_result()


def verify_value_is_contained_in_output(selected_port_obj, selected_value):
    new_value = selected_port_obj.get_operational()
    assert new_value in selected_value, "Invalid value for {}".format(selected_port_obj.label)


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
