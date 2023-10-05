import pytest
import logging
import time

from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.nvos_constants.constants_nvos import ApiType, MultiPlanarConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.infra.DatabaseTool import DatabaseTool
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure
# from ngts.tests_nvos.interfaces.test_ib_interface_counters import test_ib_clear_counters, test_clear_all_counters

logger = logging.getLogger()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_fae_interface_commands(engines, devices, test_api):
    """
    validate all show fae interface commands.

    Test flow:
    1. Validate show fae interface
    2. Validate show fae interface <interface-id>
    3. Validate show fae interface <interface-id> link
    4. Validate show fae interface <interface-id> link counters
    5. Validate show fae interface <interface-id> link diagnostics
    6. Validate show fae interface <interface-id> link state
    7. Validate show fae interface <interface-id> link plan-ports
    8. Validate set fae interface <interface-id> link lanes <1X/2X/4X>
    9. Validate unset fae interface <interface-id> link lanes
    """

    TestToolkit.tested_api = test_api

    try:
        with allure.step("Select a random non aggregated port"):
            port_name = RandomizationTool.select_random_value(devices.dut.NON_AGGREGATED_PORT_LIST).\
                get_returned_value()
            selected_port = MgmtPort(port_name)
            selected_fae_port = Fae(port_name=port_name)

        with allure.step("Select random aggregated port and plane port (of the aggregated port)"):
            selected_fae_aggregated_port = select_random_aggregated_port(devices)
            selected_fae_plane_port = select_random_plane_port(devices, selected_fae_aggregated_port)

        with allure.step("Select random fnm port and fnm plane port"):
            selected_fae_fnm_port = select_random_fnm_port(devices)
            selected_fae_fnm_plane_port = select_random_plane_port(devices, selected_fae_fnm_port)
        # ------------- show commands -------------------------------------------------------------

        with allure.step("Validate show interface command"):
            output_dictionary = OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
                Port.show_interface()).get_returned_value()
            output_keys = list(output_dictionary.keys())
            ValidationTool.compare_values(output_keys.sort(), devices.dut.ALL_PORT_LIST.sort()).verify_result()

        with allure.step("Validate FNM port speed"):
            output_dictionary = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                selected_fae_fnm_plane_port.port.interface.link.show()).get_returned_value()
            assert output_dictionary[IbInterfaceConsts.LINK_SPEED] == devices.dut.FNM_LINK_SPEED,\
                f"FNM port speed should be {devices.dut.FNM_LINK_SPEED} instead of" \
                f"{output_dictionary[IbInterfaceConsts.LINK_SPEED]}"

        with allure.step("Validate show fae interface command"):
            output_dictionary = OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
                Port.show_interface(fae_param='fae')).get_returned_value()
            output_keys = list(output_dictionary.keys())
            ValidationTool.compare_values(output_keys.sort(), devices.dut.ALL_FAE_PORT_LIST.sort()).\
                verify_result()

        with allure.step("Validate all multi planar fields exist in show fae interface <port>"):
            output_fae_port = OutputParsingTool.parse_show_interface_output_to_dictionary(
                selected_fae_port.port.interface.show()).get_returned_value()
            fae_port_keys = list(output_fae_port.keys())
            ValidationTool.validate_all_values_exists_in_list(MultiPlanarConsts.MULTI_PLANAR_KEYS, fae_port_keys). \
                verify_result()

        with allure.step("Validate show fae interface <port-id> command"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_show_interface_output_to_dictionary,
                                                selected_port.interface.show,
                                                selected_fae_port.port.interface.show,
                                                selected_fae_aggregated_port.port.interface.show,
                                                selected_fae_plane_port.port.interface.show)

        with allure.step("Validate show fae interface <port-id> link command"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_show_interface_link_output_to_dictionary,
                                                selected_port.interface.link.show,
                                                selected_fae_port.port.interface.link.show,
                                                selected_fae_aggregated_port.port.interface.link.show,
                                                selected_fae_plane_port.port.interface.link.show)

        with allure.step("Validate show fae interface <port-id> link counters command"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_json_str_to_dictionary,
                                                selected_port.interface.link.counters.show,
                                                selected_fae_port.port.interface.link.counters.show,
                                                selected_fae_aggregated_port.port.interface.link.counters.show,
                                                selected_fae_plane_port.port.interface.link.counters.show)

        with allure.step("Validate show fae interface <port-id> link diagnostics command"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_json_str_to_dictionary,
                                                selected_port.interface.link.diagnostics.show,
                                                selected_fae_port.port.interface.link.diagnostics.show,
                                                selected_fae_aggregated_port.port.interface.link.diagnostics.show,
                                                selected_fae_plane_port.port.interface.link.diagnostics.show)

        with allure.step("Validate show fae interface <port-id> link state command"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_json_str_to_dictionary,
                                                selected_port.interface.link.state.show,
                                                selected_fae_port.port.interface.link.state.show,
                                                selected_fae_aggregated_port.port.interface.link.state.show,
                                                selected_fae_plane_port.port.interface.link.state.show)

        with allure.step("Validate show fae interface <port-id> plan-ports command"):
            output_fae_aport = OutputParsingTool.parse_json_str_to_dictionary(
                selected_fae_aggregated_port.port.interface.plan_ports.show()).get_returned_value()
            fae_aport_plan_ports = list(output_fae_aport.keys())
            for plane in devices.dut.PLANE_PORT_LIST:
                full_plane_name = selected_fae_aggregated_port.port.name + plane
                assert full_plane_name in fae_aport_plan_ports,\
                    f"{full_plane_name} not exists in aggregated port {output_fae_aport.port.name} plan-ports"

        with allure.step("Validate show fae interface internal and external fnm commands"):
            validate_mp_show_interface_commands(OutputParsingTool.parse_show_interface_output_to_dictionary,
                                                selected_port.interface.show,
                                                selected_fae_port.port.interface.show,
                                                selected_fae_fnm_port.port.interface.show,
                                                selected_fae_fnm_plane_port.port.interface.show)

        # ------------- set/unset commands (Not in scope for upcoming release) -----------------
        # with allure.step("Validate set/unset fae interface of a non aggregated port"):
        #     validate_set_and_unset_fae_interface_link_lanes_command(selected_fae_port)
        #
        # with allure.step("Validate set/unset fae interface of fnm external port"):
        #     validate_set_and_unset_fae_interface_link_lanes_command(selected_fae_fnm_port)

        # ------------- action commands --------------------------------------------------------
        # tested on test_action_fae_clear_counters

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


# @pytest.mark.interface
# @pytest.mark.multiplanar
# @pytest.mark.simx
# @pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
# def test_action_fae_clear_counters(engines, players, interfaces, start_sm, test_api):
#     """
#     Validate fae action commands:
#         - nv action clear fae interface <interface-id> link counters
#         - nv action clear fae interface counters
#
#     Test flow:
#     1. run the existing "test_ib_clear_counters" with fae param.
#     2. run the existing "test_clear_all_counters" with fae param.
#     """
#
#     TestToolkit.tested_api = test_api
#
#     try:
#         with allure.step("Validate action clear fae interface <interface-id> link counters"):
#             test_ib_clear_counters(engines, players, interfaces, start_sm, fae_param="fae")
#
#         with allure.step("Validate action clear fae interface counters"):
#             test_clear_all_counters(engines, players, interfaces, start_sm, fae_param="fae")
#
#     finally:
#         with allure.step("set config to default"):
#             set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_aggregated_port_configuration(devices, test_api):
    """
    Validate all planes are configured while configuring the following Aport fields:
    ib-speed, lanes, mtu, op-vls, state.

    Test flow:
    1. Validate ib-speed field aggregation
    2. Validate lanes field aggregation
    3. Validate mtu field aggregation
    4. Validate op-vls field aggregation
    5. Validate state field aggregation
    """

    TestToolkit.tested_api = test_api

    try:
        with allure.step("Select random aggregated port and plane port"):
            selected_fae_aggregated_port = select_random_aggregated_port(devices)
            selected_fae_plane_port = select_random_plane_port(devices, selected_fae_aggregated_port)
            selected_aggregated_port = MgmtPort(selected_fae_aggregated_port.port.name)

        # Validate ib-speed field aggregation
        validate_aggregation_of_specific_link_param(selected_fae_aggregated_port, selected_fae_plane_port,
                                                    IbInterfaceConsts.LINK_IB_SPEED,
                                                    devices.dut.SUPPORTED_IB_SPEED)

        # Validate lanes field aggregation
        validate_aggregation_of_specific_link_param(selected_fae_aggregated_port, selected_fae_plane_port,
                                                    IbInterfaceConsts.LINK_LANES,
                                                    IbInterfaceConsts.SUPPORTED_LANES)

        # Validate mtu field aggregation
        validate_aggregation_of_specific_link_param(selected_fae_aggregated_port, selected_fae_plane_port,
                                                    IbInterfaceConsts.LINK_MTU,
                                                    IbInterfaceConsts.MTU_VALUES)

        # Validate op-vls field aggregation
        validate_aggregation_of_specific_link_param(selected_fae_aggregated_port, selected_fae_plane_port,
                                                    IbInterfaceConsts.LINK_OPERATIONAL_VLS,
                                                    IbInterfaceConsts.SUPPORTED_VLS)

        # Validate state field aggregation
        with allure.step("Validate state field aggregation"):
            aport_state = OutputParsingTool.parse_json_str_to_dictionary(
                selected_aggregated_port.interface.link.state.show()).get_returned_value()
            new_state = NvosConsts.LINK_STATE_UP if NvosConsts.LINK_STATE_DOWN in aport_state.keys()\
                else NvosConsts.LINK_STATE_DOWN
            selected_aggregated_port.interface.link.state.set(op_param_name=new_state, apply=True).\
                verify_result()
            aport_state = OutputParsingTool.parse_json_str_to_dictionary(
                selected_aggregated_port.interface.link.state.show()).get_returned_value()
            pport_state = OutputParsingTool.parse_json_str_to_dictionary(
                selected_fae_plane_port.port.interface.link.state.show()).get_returned_value()

            assert new_state in aport_state.keys() and aport_state == pport_state,\
                f"mismatch in {IbInterfaceConsts.LINK_STATE}: aggregated port:{aport_state}, " \
                f"plane port:{pport_state}, value set: {new_state}"

    finally:
        with allure.step("set config to default"):
            selected_aggregated_port.interface.link.state.unset(apply=True, ask_for_confirmation=True).verify_result()
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_aggregated_port_mismatch_between_planes(engines, devices, test_api):
    """
    validate correct aggregation in Aport while there is a mismatch in fields values between port’s planes.

    Test flow:
    1. Validate ib-speed field mismatch aggregation
    2. Validate lanes field mismatch aggregation
    3. Validate mtu field mismatch aggregation
    4. Validate op-vls field mismatch aggregation
    5. Validate max-supported-mtu field mismatch aggregation
    6. Validate supported-ib-speed field mismatch aggregation
    7. Validate state field mismatch aggregation
    """

    TestToolkit.tested_api = test_api

    try:
        with allure.step(f"Configure ports"):
            loop_back_name = RandomizationTool.select_random_value(devices.dut.DEFAULT_LOOPBACK_PORTS).\
                get_returned_value()
            loop_back_port = MgmtPort(loop_back_name)
            aggregated_port = MgmtPort(devices.dut.DEFAULT_AGGREGATED_PORT)
            for port in devices.dut.DEFAULT_LOOPBACK_PORTS:
                if loop_back_name == port:
                    selected_plane_port = Fae(port_name=devices.dut.LOOP_BACK_TO_PORTS[port])
                else:
                    other_plane_port = Fae(port_name=devices.dut.LOOP_BACK_TO_PORTS[port])

        with allure.step("Validate ib-speed mismatch aggregation"):
            new_value, aggregated_port_output, selected_plane_port_output, other_plane_port_output = \
                set_param_value_in_specific_plane(loop_back_port, aggregated_port, selected_plane_port,
                                                  other_plane_port, IbInterfaceConsts.LINK_IB_SPEED,
                                                  devices.dut.SUPPORTED_IB_SPEED)

            assert selected_plane_port_output[IbInterfaceConsts.LINK_IB_SPEED] == new_value,\
                f"plane port {IbInterfaceConsts.LINK_IB_SPEED} value is: " \
                f"{selected_plane_port_output[IbInterfaceConsts.LINK_IB_SPEED]}, instead of: {new_value}"

            assert aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED] == 0,\
                f"aggregated port {IbInterfaceConsts.LINK_IB_SPEED} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED]}, instead of: 0"

            assert aggregated_port_output[IbInterfaceConsts.LINK_STATE] == 'down',\
                f"aggregated port {IbInterfaceConsts.LINK_STATE} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_STATE]}, instead of: down"

        # with allure.step("Validate lanes mismatch aggregation"):
        # TODO: currently not supported by operational code - set fae interface command has not implemented yet

        with allure.step("Validate mtu mismatch aggregation"):
            new_value, aggregated_port_output, selected_plane_port_output, other_plane_port_output = \
                set_param_value_in_specific_plane(loop_back_port, aggregated_port, selected_plane_port,
                                                  other_plane_port, IbInterfaceConsts.LINK_MTU,
                                                  IbInterfaceConsts.MTU_VALUES)

            assert selected_plane_port_output[IbInterfaceConsts.LINK_MTU] == new_value,\
                f"plane port {IbInterfaceConsts.LINK_MTU} value is: " \
                f"{selected_plane_port_output[IbInterfaceConsts.LINK_MTU]}, instead of: {new_value}"

            planes_min = min(int(new_value), int(other_plane_port_output[IbInterfaceConsts.LINK_MTU]))

            assert aggregated_port_output[IbInterfaceConsts.LINK_MTU] == planes_min,\
                f"aggregated port {IbInterfaceConsts.LINK_MTU} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_MTU]}, instead of: {planes_min}"

        with allure.step("Validate op-vls mismatch aggregation"):
            new_value, aggregated_port_output, selected_plane_port_output, other_plane_port_output = \
                set_param_value_in_specific_plane(loop_back_port, aggregated_port, selected_plane_port,
                                                  other_plane_port, IbInterfaceConsts.LINK_OPERATIONAL_VLS,
                                                  IbInterfaceConsts.SUPPORTED_VLS)

            assert selected_plane_port_output[IbInterfaceConsts.LINK_OPERATIONAL_VLS] == new_value, \
                f"plane port {IbInterfaceConsts.LINK_OPERATIONAL_VLS} value is: " \
                f"{selected_plane_port_output[IbInterfaceConsts.LINK_OPERATIONAL_VLS]}, instead of: {new_value}"

            planes_min = min(int(new_value), int(other_plane_port_output[IbInterfaceConsts.LINK_OPERATIONAL_VLS]))

            assert aggregated_port_output[IbInterfaceConsts.LINK_OPERATIONAL_VLS] == planes_min, \
                f"aggregated port {IbInterfaceConsts.LINK_OPERATIONAL_VLS} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_OPERATIONAL_VLS]}, instead of: {planes_min}"

        # with allure.step("Validate max-supported-mtu mismatch aggregation"):
        # TODO: currently not supported by operational code - update STATE_DB values directly is not available

        # with allure.step("Validate supported-ib-speed mismatch aggregation"):
        # TODO: currently not supported by operational code - update STATE_DB values directly is not available

        with allure.step("Validate state mismatch aggregation"):
            loop_back_port.interface.link.unset(apply=True, ask_for_confirmation=True).verify_result()
            loop_back_port.interface.link.state.set(op_param_value='down', apply=True, ask_for_confirmation=True).\
                verify_result()
            aggregated_port_state = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                aggregated_port.interface.link.state.show()).get_returned_value()
            selected_plane_port_state = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                selected_plane_port.port.interface.link.state.show()).get_returned_value()
            other_plane_port_state = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                other_plane_port.port.interface.link.state.show()).get_returned_value()

            assert selected_plane_port_state == 'down',\
                f"selected plane port {IbInterfaceConsts.LINK_STATE} value is: " \
                f"{selected_plane_port_state}, instead of: down"

            assert other_plane_port_state == 'up',\
                f"other plane port {IbInterfaceConsts.LINK_STATE} value is: " \
                f"{other_plane_port_state}, instead of: up"

            assert aggregated_port_state == 'down',\
                f"aggregated plane port {IbInterfaceConsts.LINK_STATE} value is: " \
                f"{aggregated_port_state}, instead of: down"

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_aggregated_port_physical_and_logical_state_machines(engines, devices, test_api):
    """
    validate Aport Physical state and Logical state aggregation according to the following rule priorities:
    State Type  | Rule Priority | Logic                                                                    |APort State
    --------------------------------------------------------------------------------------------------------------
                | 0             | Any underlying plane port is disabled                                    | Disabled
    Physical    | 1             | Any underlying plane port is in Sleep state                              | Sleep
                | 2             | Any underlying plane port is in Polling state                            | Polling
                | 3             | Any underlying plane port are in LinkUp state                            | LinkUp
    --------------------------------------------------------------------------------------------------------------
                | 0             | At least on underlying plane port is in Down state                       | Down
    Logical     | 1             | Any ul plane port is in Init state AND no ul plane port is in Down state | Init
                | 2             | Any ul plane p is in Armed state AND no ul pp is in Down OR Init state   | Armed
                | 3             | All underlying plane ports are in Active state                           | Active
    --------------------------------------------------------------------------------------------------------------

    Test flow:
    1. Validate physical state in all plane port combinations:
        a.	plane1: disabled, plane2: disabled
        b.	plane1: disabled, plane2: sleep
        c.	plane1: disabled, plane2: polling
        d.	plane1: disabled, plane2: linkup
        e.	plane1: sleep   , plane2: sleep
        f.	plane1: sleep   , plane2: polling
        g.	plane1: sleep   , plane2: linkup
        h.	plane1: polling , plane2: polling
        i.	plane1: polling , plane2: linkup
        j.	plane1: linkup  , plane2: linkup

    2. Validate logical state in all plane port combinations:
        a.	plane1: down  , plane2: down
        b.	plane1: down  , plane2: init
        c.	plane1: down  , plane2: armed
        d.	plane1: down  , plane2: active
        e.	plane1: init  , plane2: init
        f.	plane1: init  , plane2: armed
        g.	plane1: init  , plane2: active
        h.	plane1: armed , plane2: armed
        i.	plane1: armed , plane2: active
        j.	plane1: active, plane2: active
    """

    TestToolkit.tested_api = test_api
    engine = engines.dut

    try:
        with allure.step("Select random aggregated port and plane port (of the aggregated port)"):
            selected_fae_aggregated_port = select_random_aggregated_port(devices)

        with allure.step("Validate physical state aggregation - all combinations"):
            for combine in MultiPlanarConsts.PHYSICAL_STATE_AGG_TABLE:
                validate_state_aggregation(engine, devices, selected_fae_aggregated_port,
                                           MultiPlanarConsts.PHYSICAL_STATE_PARAM,
                                           combine['p1'], combine['p2'], combine['exp'])

        with allure.step("Validate logical state aggregation - all combinations"):
            for combine in MultiPlanarConsts.LOGICAL_STATE_AGG_TABLE:
                validate_state_aggregation(engine, devices, selected_fae_aggregated_port,
                                           MultiPlanarConsts.LOGICAL_STATE_PARAM,
                                           combine['p1'], combine['p2'], combine['exp'])

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_symmetry_manager_performance(engines, devices, test_api):
    """
    Validate configuring an aggregated port total time is not significantly longer than
    configuring a regular (non-aggregated) port.

    Test flow:
    1. Select a random aggregated port:
    2. Measure configuring an aggregated port in Black Mamba:
    3. Compare between configuration time:
    """

    TestToolkit.tested_api = test_api

    try:
        with allure.step("Select a random aggregated port"):
            aggregated_port_name = RandomizationTool.select_random_value(devices.dut.AGGREGATED_PORT_LIST). \
                get_returned_value()
            aggregated_port = MgmtPort(aggregated_port_name)

        with allure.step("Validate aggregated port configuration time"):
            aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                aggregated_port.interface.link.show()).get_returned_value()
            param_list = devices.dut.SUPPORTED_IB_SPEED.remove(
                aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED])
            param_new_value = RandomizationTool.select_random_value(param_list).get_returned_value()

            start_time = time.time()
            aggregated_port.interface.link.set(op_param_name=IbInterfaceConsts.LINK_IB_SPEED,
                                               op_param_value=param_new_value, apply=True,
                                               ask_for_confirmation=True).verify_result()
            end_time = time.time()
            diff_time = end_time - start_time
            assert diff_time < MultiPlanarConsts.NON_AGGREGATED_PORT_CONFIG_TIME,\
                "set and apply configuration for an aggregated port time is higher than expected"

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_symmetry_manager_resiliency(engines, devices, test_api):
    """
    validate:
    -	Configuration of the aggregated port persists through reboot
    -	The system recovers automatically after killing the symmetry manager docker.
    -	No unexpected behavior (access violation, leak etc.) when processing malformed input
        (e.g. malformed/missing config in DB)
    -	System is still stable after causing an exception in Counter manager

    Test flow:
    1. Validate aggregated port configuration persists through reboot
    2. Validate system recovery after docker kill
    3. Remove sampled data from DB
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)

    try:
        with allure.step("Select a random aggregated port"):
            aggregated_port_name = RandomizationTool.select_random_value(devices.dut.AGGREGATED_PORT_LIST). \
                get_returned_value()
            aggregated_port = MgmtPort(aggregated_port_name)

        with allure.step("Update aggregated port configuration"):
            aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                aggregated_port.interface.link.show()).get_returned_value()

            # Update link ib_speed
            param_list = devices.dut.SUPPORTED_IB_SPEED.remove(
                aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED])
            ib_speed_new_value = RandomizationTool.select_random_value(param_list).get_returned_value()
            aggregated_port.interface.link.set(op_param_name=IbInterfaceConsts.LINK_IB_SPEED,
                                               op_param_value=ib_speed_new_value).verify_result()
            # Update link lanes
            param_list = IbInterfaceConsts.SUPPORTED_LANES.remove(
                aggregated_port_output[IbInterfaceConsts.LINK_LANES])
            lanes_new_value = RandomizationTool.select_random_value(param_list).get_returned_value()
            aggregated_port.interface.link.set(op_param_name=IbInterfaceConsts.LINK_LANES,
                                               op_param_value=lanes_new_value).verify_result()
            # Update link mtu
            param_list = IbInterfaceConsts.MTU_VALUES.remove(
                aggregated_port_output[IbInterfaceConsts.LINK_MTU])
            mtu_new_value = RandomizationTool.select_random_value(param_list).get_returned_value()
            aggregated_port.interface.link.set(op_param_name=IbInterfaceConsts.LINK_MTU,
                                               op_param_value=mtu_new_value, apply=True,
                                               ask_for_confirmation=True).verify_result()

        with allure.step("Perform system reboot"):
            system.reboot.action_reboot(params='force').verify_result()

        with allure.step("Validate configured aggregated port parameters after reboot"):
            aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                aggregated_port.interface.link.show()).get_returned_value()

            assert aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED] == ib_speed_new_value, \
                f"aggregated {IbInterfaceConsts.LINK_IB_SPEED} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_IB_SPEED]}, instead of: {ib_speed_new_value}"
            assert aggregated_port_output[IbInterfaceConsts.LINK_LANES] == ib_speed_new_value, \
                f"aggregated {IbInterfaceConsts.LINK_LANES} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_LANES]}, instead of: {lanes_new_value}"
            assert aggregated_port_output[IbInterfaceConsts.LINK_MTU] == ib_speed_new_value, \
                f"aggregated {IbInterfaceConsts.LINK_MTU} value is: " \
                f"{aggregated_port_output[IbInterfaceConsts.LINK_MTU]}, instead of: {mtu_new_value}"

        with allure.step(f"stop {MultiPlanarConsts.CONFIG_MANAGER_SERVICE} daemon"):
            GeneralCliCommon(TestToolkit.engines.dut).systemctl_stop(MultiPlanarConsts.CONFIG_MANAGER_SERVICE)

        with allure.step(f"wait for  {MultiPlanarConsts.SERVICE_RECOVERY_MAX_TIME} seconds..."):
            time.sleep(MultiPlanarConsts.SERVICE_RECOVERY_MAX_TIME)

        with allure.step(f"verify {MultiPlanarConsts.CONFIG_MANAGER_SERVICE} daemon automatic recovery"):
            if not GeneralCliCommon(TestToolkit.engines.dut).systemctl_is_service_active(
                    MultiPlanarConsts.CONFIG_MANAGER_SERVICE):
                GeneralCliCommon(TestToolkit.engines.dut).systemctl_start(MultiPlanarConsts.CONFIG_MANAGER_SERVICE)
                assert False, f"{MultiPlanarConsts.CONFIG_MANAGER_SERVICE} service automatic recovery failed"

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_symmetry_manager_log_and_tech_support(engines, devices, test_api):
    """
    validate:
    - Configuring commands are logged to system log
    - Aport and port’s planes data based are stored in tech support

    Test flow:
    1. Validate symmetry manager log in system log
    2. Validate Aport and planes db exist in debug dump
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)

    try:
        with allure.step("Select random aggregated port and plane port"):
            selected_fae_aggregated_port = select_random_aggregated_port(devices)
            selected_fae_plane_port = select_random_plane_port(devices, selected_fae_aggregated_port)

        with allure.step("Set fae interface link state and check log file"):
            system.log.rotate_logs()
            selected_fae_plane_port.port.interface.link.state.set(op_param_value='down', apply=True,
                                                                  ask_for_confirmation=True).verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, MultiPlanarConsts.LOG_MSG_SET_FAE_INTERFACE).\
                verify_result()

        with allure.step("Unset fae interface link state and check log file"):
            system.log.rotate_logs()
            selected_fae_plane_port.port.interface.link.state.unset(apply=True, ask_for_confirmation=True).\
                verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, MultiPlanarConsts.LOG_MSG_UNSET_FAE_INTERFACE).\
                verify_result()

        with allure.step("Run action clear fae interface and check log file"):
            system.log.rotate_logs()
            selected_fae_plane_port.port.interface.link.stats.clear_stats(fae_param="fae").verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, MultiPlanarConsts.LOG_MSG_ACTION_CLEAR_FAE_INTERFACE).\
                verify_result()

        with allure.step("Validate all asics database files exist in tech support file"):
            validate_mp_database_files_exist_in_techsupport(system, engines.dut)

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_fae_invalid_commands(engines, devices, test_api):
    """
    validate fae interface commands with invalid param values.

    Test flow:
    1. nv show fae interface <unknown interface-id>
    2. nv show fae interface <unknown interface-id> link
    3. nv show fae interface <unknown interface-id> link counters
    4. nv show fae interface <unknown interface-id> link diagnostics
    5. nv show fae interface <unknown interface-id> link state
    6. nv show fae interface <unknown interface-id> plan-ports
    7. nv action clear fae interface <unknown interface-id> link counters
    8. nv set fae interface <unknown interface-id> link lanes <1X/2X/4X>
    9. nv set fae interface <interface-id> link lanes <invalid lane>
    10. nv unset fae interface <unknown interface-id> link lanes
    11. nv show interface <internal-fnm-id>
    """

    TestToolkit.tested_api = test_api

    try:
        with allure.step("Validate show fae interface with unknown interface-id"):
            Fae(port_name='unknown').port.interface.show(should_succeed=False)

        with allure.step("Validate show fae interface link with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.show(should_succeed=False)

        with allure.step("Validate show fae interface link counters with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.counters.show(should_succeed=False)

        with allure.step("Validate show fae interface link diagnostics with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.diagnostics.show(should_succeed=False)

        with allure.step("Validate show fae interface link state with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.state.show(should_succeed=False)

        with allure.step("Validate show fae interface link plan-ports with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.plan_ports.show(should_succeed=False)

        with allure.step("Validate action clear fae interface link counters command with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.stats.clear_stats(dut_engine=engines.dut, fae_param="fae").\
                verify_result(should_succeed=False)

        with allure.step("Validate set fae interface link lanes with unknown interface-id"):
            new_ib_speed = RandomizationTool.select_random_value(list(IbInterfaceConsts.SPEED_LIST.keys())).\
                get_returned_value()
            Fae(port_name='unknown').port.interface.link.set(op_param_name='lanes', op_param_value=new_ib_speed,
                                                             apply=True).verify_result(should_succeed=False)

        with allure.step("Validate set fae interface link lanes with invalid lanes"):
            port_name = RandomizationTool.select_random_value(devices.dut.ALL_PORT_LIST).get_returned_value()
            Fae(port_name=port_name).port.interface.link.set(op_param_name='lanes', op_param_value='invalid_lanes',
                                                             apply=True).verify_result(should_succeed=False)

        with allure.step("Validate unset fae interface link lanes with unknown interface-id"):
            Fae(port_name='unknown').port.interface.link.unset(op_param='lanes', apply=True).\
                verify_result(should_succeed=False)

        with allure.step("Validate show interface with internal fnm id"):
            port_name = RandomizationTool.select_random_value(devices.dut.FNM_PORT_LIST).get_returned_value()
            plane_name = RandomizationTool.select_random_value(devices.dut.PLANE_PORT_LIST).get_returned_value()
            fnm_internal_name = port_name + plane_name
            Fae(port_name=fnm_internal_name).port.interface.show(should_succeed=False)

    finally:
        with allure.step("set config to default"):
            set_mp_config_to_default()


# ---------------------------------------------

def validate_mp_show_interface_commands(parse_func, port_cmd, port_fae_cmd, aport_fae_cmd, pport_fae_cmd):
    with allure.step("Show interface of a non aggregated port"):
        output_port = parse_func(port_cmd()).get_returned_value()
        port_keys = list(output_port.keys())

    with allure.step("Show fae interface of a non aggregated port"):
        output_fae_port = parse_func(port_fae_cmd()).get_returned_value()
        fae_port_keys = list(output_fae_port.keys())

    with allure.step("Show fae interface of an aggregated port"):
        output_fae_aport = parse_func(aport_fae_cmd()).get_returned_value()
        fae_aport_keys = list(output_fae_aport.keys())

    with allure.step("Show fae interface of a plane port"):
        output_fae_plane_port = parse_func(pport_fae_cmd()).get_returned_value()
        fae_plane_port_keys = list(output_fae_plane_port.keys())

    with allure.step("Validate all show interface <port> fields exist in show fae interface <port>"):
        ValidationTool.validate_all_values_exists_in_list(port_keys, fae_port_keys).verify_result()

    with allure.step("Compare between non-aggregated and aggregated port show interface"):
        fae_port_keys = list(set(fae_port_keys) - set(MultiPlanarConsts.MULTI_PLANAR_KEYS))
        ValidationTool.compare_values(fae_port_keys.sort(), fae_aport_keys.sort()).verify_result()

    with allure.step("Compare between aggregated port and plane port show interface"):
        fae_plane_port_keys = list(set(fae_plane_port_keys) - set(MultiPlanarConsts.MULTI_PLANAR_KEYS))
        ValidationTool.compare_values(fae_aport_keys.sort(), fae_plane_port_keys.sort()).verify_result()


def select_random_aggregated_port(devices):
    with allure.step("Select a random aggregated port"):
        aggregated_port_name = RandomizationTool.select_random_value(devices.dut.AGGREGATED_PORT_LIST). \
            get_returned_value()
        selected_fae_aggregated_port = Fae(port_name=aggregated_port_name)
        return selected_fae_aggregated_port


def select_random_fnm_port(devices):
    with allure.step("Select a random fnm port"):
        fnm_port_name = RandomizationTool.select_random_value(devices.dut.FNM_PORT_LIST). \
            get_returned_value()
        selected_fae_fnm_port = Fae(port_name=fnm_port_name)
        return selected_fae_fnm_port


def select_random_plane_port(devices, fae_aggregated_port):
    with allure.step("Choose a random plane port (of the aggregated port)"):
        plane_name = RandomizationTool.select_random_value(devices.dut.PLANE_PORT_LIST).get_returned_value()
        plane_port_name = fae_aggregated_port.port.name + plane_name
        selected_fae_plane_port = Fae(port_name=plane_port_name)
        return selected_fae_plane_port


def validate_aggregation_of_specific_link_param(aggregated_port, plane_port, link_param, link_param_list):
    with allure.step(f"Validate {link_param} field aggregation"):
        aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            aggregated_port.port.interface.link.show()).get_returned_value()
        link_param_list.remove(aggregated_port_output[link_param])
        param_new_value = RandomizationTool.select_random_value(link_param_list).get_returned_value()
        aggregated_port.port.interface.link.set(op_param_name=link_param,
                                                op_param_value=param_new_value, apply=True).verify_result()
        aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            aggregated_port.port.interface.link.show()).get_returned_value()
        plane_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            plane_port.port.interface.link.show()).get_returned_value()

        assert aggregated_port_output[link_param] == \
            plane_port_output[link_param] == param_new_value, \
            f"mismatch in {link_param}:" \
            f"aggregated port:{aggregated_port_output[link_param]}, " \
            f"plane port:{aggregated_port_output[link_param]}, value set: {param_new_value}"


def set_param_value_in_specific_plane(loop_back_port, aggregated_port, selected_plane_port,
                                      other_plane_port, param, param_list):
    with allure.step(f"Change {param} field value in {loop_back_port.name} port"):
        loop_back_port.interface.link.unset(apply=True, ask_for_confirmation=True).verify_result()
        loop_back_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            loop_back_port.interface.link.show()).get_returned_value()
        param_list.remove(loop_back_port_output[param])
        param_new_value = RandomizationTool.select_random_value(param_list).get_returned_value()
        loop_back_port.interface.link.set(op_param_name=param, op_param_value=param_new_value, apply=True,
                                          ask_for_confirmation=True).verify_result()
        aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            aggregated_port.interface.link.show()).get_returned_value()
        selected_plane_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            selected_plane_port.port.interface.link.show()).get_returned_value()
        other_plane_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            other_plane_port.port.interface.link.show()).get_returned_value()

        return param_new_value, aggregated_port_output, selected_plane_port_output, other_plane_port_output


def validate_state_aggregation(engine, devices, aggregated_port, param, value0, value1, expected_value):
    with allure.step(f"Update asic0 {param} state to: {value0} and asic1 {param} state to: {value1}"):
        DatabaseTool.sonic_db_cli_hset(engine, devices.dut.ASIC0, devices.dut.COUNTERS_DB_NAME,
                                       devices.dut.OBJECT_NUMBERS[aggregated_port.port.name]['plane1'],
                                       param, value0)
        DatabaseTool.sonic_db_cli_hset(engine, devices.dut.ASIC1, devices.dut.COUNTERS_DB_NAME,
                                       devices.dut.OBJECT_NUMBERS[aggregated_port.port.name]['plane2'],
                                       param, value1)

    with allure.step(f"wait {MultiPlanarConsts.SYNC_TIME} secs for sync"):
        time.sleep(MultiPlanarConsts.SYNC_TIME)

    with allure.step(f"Validate {param} field aggregation"):
        aggregated_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            aggregated_port.port.interface.link.show()).get_returned_value()
        assert aggregated_port_output[param] == expected_value,\
            f"aggregated port {param} is {aggregated_port_output[param]}, instead of {expected_value}"


def validate_mp_database_files_exist_in_techsupport(system, engine):
    """
    generate techsupport and validate all asics database files exist in the dump dir
    """
    tech_support_folder = system.techsupport.action_generate(engine=engine)
    logger.info("The techsupport file name is : " + tech_support_folder)
    techsupport_files_list = system.techsupport.get_techsupport_files_list(engine, tech_support_folder, 'dump')
    for db_table in MultiPlanarConsts.DATABASE_TABLES:
        assert "{}.json".format(db_table) in techsupport_files_list, \
            "Expect to have {}.json file, in the tech support dump files {}".format(db_table, techsupport_files_list)
        assert "{}.json.0".format(db_table) in techsupport_files_list, \
            "Expect to have {}.json file, in the tech support dump files {}".format(db_table, techsupport_files_list)


def validate_set_and_unset_fae_interface_link_lanes_command(selected_fae_port):
    with allure.step(f"Validate set fae interface {selected_fae_port.port.name} link lanes command"):
        output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            selected_fae_port.port.interface.link.show()).get_returned_value()
        lanes_list = IbInterfaceConsts.SUPPORTED_LANES - output[IbInterfaceConsts.LINK_LANES]
        new_lanes = RandomizationTool.select_random_value(lanes_list).get_returned_value()
        selected_fae_port.port.interface.link.set(op_param_name=IbInterfaceConsts.LINK_LANES,
                                                  op_param_value=new_lanes, apply=True).verify_result()
        output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            selected_fae_port.port.interface.link.show()).get_returned_value()
        assert output[IbInterfaceConsts.LINK_LANES] == new_lanes, \
            f"{IbInterfaceConsts.LINK_LANES} value is {output[IbInterfaceConsts.LINK_LANES]}," \
            f"instead of {new_lanes}"

    with allure.step(f"Validate unset fae interface {selected_fae_port.port.name} link lanes command"):
        selected_fae_port.port.interface.link.unset(op_param_name=IbInterfaceConsts.LINK_LANES,
                                                    apply=True).verify_result()
        output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            selected_fae_port.port.interface.link.show()).get_returned_value()
        assert output[IbInterfaceConsts.LINK_LANES] == IbInterfaceConsts.DEFAULT_LANES, \
            f"{IbInterfaceConsts.LINK_LANES} value is {output[IbInterfaceConsts.LINK_LANES]}," \
            f"instead of {IbInterfaceConsts.DEFAULT_LANES}"


def set_mp_config_to_default():
    logger.info("TBD")
