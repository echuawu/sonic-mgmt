import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_interface_mtu(engines, players, interfaces):
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
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current MTU value"):
        current_mtu_value = selected_port.ib_interface.link.mtu.get_operational()
        logging.info("Current mtu value of port '{}' is: {}".format(selected_port.name, current_mtu_value))

    with allure.step("Get the max supported MTU value"):
        max_supported_mtu = selected_port.ib_interface.link.max_supported_mtu.get_operational(
            renew_show_cmd_output=False)
        logging.info("Max supported mtu: {}".format(max_supported_mtu))

    with allure.step("Select a random MTU value for port {}".format(selected_port.name)):
        mtu_values = [value for value in IbInterfaceConsts.MTU_VALUES if value <= max_supported_mtu]
        selected_mtu_value = Tools.RandomizationTool.select_random_value(mtu_values, current_mtu_value)

    with allure.step("Set mtu '{}' for port '{}".format(selected_mtu_value, selected_port.name)):
        selected_port.ib_interface.link.mtu.set(value=selected_mtu_value, apply=True).verify_result()

        with allure.step("Verify the mtu value updated to: {}".format(selected_mtu_value)):
            new_mtu_value = selected_port.ib_interface.link.mtu.get_operational()
            Tools.ValidationTool.compare_values(new_mtu_value, selected_mtu_value, True).verify_result()

        with allure.step("Verify the traffic passes successfully"):
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)

    with allure.step("Unset MTU for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.mtu.unset(apply=True).verify_result()

        with allure.step("Verify the MTU is updated to default: {}".format(IbInterfaceConsts.DEFAULT_MTU)):
            new_mtu_value = selected_port.ib_interface.link.mtu.get_operational()
            Tools.ValidationTool.compare_values(new_mtu_value, IbInterfaceConsts.DEFAULT_MTU, True).verify_result()

    if current_mtu_value != IbInterfaceConsts.DEFAULT_MTU:
        with allure.step("Restore original mtu value ({})".format(current_mtu_value)):
            selected_port.ib_interface.link.mtu.set(value=current_mtu_value, apply=True).verify_result()

            with allure.step("Verify the mtu value was restored to: {}".format(current_mtu_value)):
                new_mtu_value = selected_port.ib_interface.link.mtu.get_operational()
                Tools.ValidationTool.compare_values(new_mtu_value, current_mtu_value, True).verify_result()

    with allure.step("Verify the traffic passes successfully"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)


@pytest.mark.ib_interfaces
def test_ib_interface_speed(engines, players, interfaces):
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
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current speed value"):
        current_speed_value = selected_port.ib_interface.link.speed.get_operational()
        current_ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational()
        logging.info("Current speed value of port '{}' is: {}".format(selected_port.name, current_speed_value))
        logging.info("Current ib-speed value of port '{}' is: {}".format(selected_port.name, current_ib_speed_value))

    with allure.step("Get the supported link speeds"):
        supported_speeds = selected_port.ib_interface.link.supported_speeds.get_operational(renew_show_cmd_output=False)
        logging.info("Supported speeds: {}".format(supported_speeds))
        supported_speeds = supported_speeds.split()

    with allure.step("Get the supported link ib-speeds"):
        supported_ib_speeds = selected_port.ib_interface.link.supported_speeds.get_operational(
            renew_show_cmd_output=False)
        logging.info("Supported ib-speeds: {}".format(supported_ib_speeds))
        supported_ib_speeds = supported_speeds.split()

    with allure.step("Select a random speed value for port {}".format(selected_port.name)):
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
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)

    with allure.step("Select a random ib-speed value for port {}".format(selected_port.name)):
        selected_ib_speed_value = Tools.RandomizationTool.select_random_value(supported_ib_speeds,
                                                                              current_ib_speed_value)
        logging.info("Selected ib-speed: " + selected_ib_speed_value)

    with allure.step("Set ib-speed '{}' for port '{}".format(selected_ib_speed_value, selected_port.name)):
        selected_port.ib_interface.link.ib_speed.set(value=selected_ib_speed_value, apply=True).verify_result()

        with allure.step("Verify the ib-speed value updated to: {}".format(selected_speed_value)):
            ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational()
            Tools.ValidationTool.compare_values(ib_speed_value, selected_speed_value, True).verify_result()

        with allure.step('Verify the speed value is equal to ib-speed value'):
            speed_value = selected_port.ib_interface.link.speed.get_operational(False)
            Tools.ValidationTool.compare_values(speed_value, IbInterfaceConsts.SPEED_LIST[ib_speed_value],
                                                True).verify_result()

    with allure.step("Unset speed for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.speed.unset(apply=True).verify_result()

    with allure.step("Unset ib_speed for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.ib_speed.unset(apply=True).verify_result()

    with allure.step("Restore original speed fot port {}".format(selected_port.name)):
        selected_port.ib_interface.link.ib_speed.unset(apply=True).verify_result()

        with allure.step("Verify the ib-speed value updated to: {}".format(selected_ib_speed_value)):
            ib_speed_value = selected_port.ib_interface.link.ib_speed.get_operational()
            Tools.ValidationTool.compare_values(ib_speed_value, selected_speed_value, True).verify_result()

        with allure.step("Verify the traffic passes successfully"):
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)


@pytest.mark.ib_interfaces
def test_ib_interface_lanes(engines, players, interfaces):
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
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current supported lanes"):
        current_supported_lanes = selected_port.ib_interface.link.lanes.get_operational()
        logging.info("Current lanes value of port '{}' is: {}".format(selected_port.name, current_supported_lanes))

    with allure.step("Select a random lanes for port {}".format(selected_port.name)):
        selected_lanes = Tools.RandomizationTool.select_random_value(IbInterfaceConsts.SUPPORTED_LANES,
                                                                     current_supported_lanes)

    with allure.step("Set lanes to '{}' for port '{}".format(selected_lanes, selected_port.name)):
        selected_port.ib_interface.link.lanes.set(value=selected_lanes, apply=True).verify_result()

        with allure.step("Verify the lanes value updated to: {}".format(selected_lanes)):
            new_mtu_value = selected_port.ib_interface.link.lanes.get_operational()
            Tools.ValidationTool.compare_values(new_mtu_value, selected_lanes, True).verify_result()

        with allure.step("Verify the traffic passes successfully"):
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)

    with allure.step("Unset lanes for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.lanes.unset(apply=True).verify_result()

        with allure.step("Verify the lanes is updated to default: {}".format(IbInterfaceConsts.DEFAULT_LANES)):
            new_lanes_value = selected_port.ib_interface.lanes.mtu.get_operational()
            Tools.ValidationTool.compare_values(new_lanes_value, IbInterfaceConsts.DEFAULT_LANES, True).verify_result()

    if current_supported_lanes != IbInterfaceConsts.DEFAULT_LANES:
        with allure.step("Restore original lanes value ({})".format(current_supported_lanes)):
            selected_port.ib_interface.link.lanes.set(value=current_supported_lanes, apply=True).verify_result()

            with allure.step("Verify the lanes value was restored to: {}".format(current_supported_lanes)):
                new_lanes_value = selected_port.ib_interface.link.mtu.get_operational()
                Tools.ValidationTool.compare_values(new_lanes_value, current_supported_lanes, True).verify_result()

    with allure.step("Verify the traffic passes successfully"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)


@pytest.mark.ib_interfaces
def test_ib_interface_vls(engines, players, interfaces):
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
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step("Read current supported op-vls"):
        current_supported_op_vls = selected_port.ib_interface.link.operational_vls.get_operational()
        logging.info("Current op_vls value of port '{}' is: {}".format(selected_port.name, current_supported_op_vls))

    with allure.step("Select a random op_vls for port {}".format(selected_port.name)):
        selected_op_vls = Tools.RandomizationTool.select_random_value(IbInterfaceConsts.SUPPORTED_VLS,
                                                                      current_supported_op_vls)

    with allure.step("Set op_vls to '{}' for port '{}".format(selected_op_vls, selected_port.name)):
        selected_port.ib_interface.link.operational_vls.set(value=selected_op_vls, apply=True).verify_result()

        with allure.step("Verify the op_vls value updated to: {}".format(selected_op_vls)):
            new_op_vls_value = selected_port.ib_interface.link.operational_vls.get_operational()
            Tools.ValidationTool.compare_values(new_op_vls_value, selected_op_vls, True).verify_result()

        with allure.step("Verify the traffic passes successfully"):
            Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)

    with allure.step("Unset op_vls for port {}".format(selected_port.name)):
        selected_port.ib_interface.link.operational_vls.unset(apply=True).verify_result()

        with allure.step("Verify the op_vls is updated to default: {}".format(IbInterfaceConsts.DEFAULT_VLS)):
            new_lanes_value = selected_port.ib_interface.operational_vls.mtu.get_operational()
            Tools.ValidationTool.compare_values(new_lanes_value, IbInterfaceConsts.DEFAULT_VLS, True).verify_result()

    if current_supported_op_vls != IbInterfaceConsts.DEFAULT_VLS:
        with allure.step("Restore original op_vls value ({})".format(current_supported_op_vls)):
            selected_port.ib_interface.link.operational_vls.set(value=current_supported_op_vls,
                                                                apply=True).verify_result()

            with allure.step("Verify the op_vls value was restored to: {}".format(current_supported_op_vls)):
                new_lanes_value = selected_port.ib_interface.link.operational_vls.get_operational()
                Tools.ValidationTool.compare_values(new_lanes_value, current_supported_op_vls, True).verify_result()

    with allure.step("Verify the traffic passes successfully"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players=players, interfaces=interfaces)
