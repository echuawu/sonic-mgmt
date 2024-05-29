import logging

import pytest

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts, NvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_interface_state(test_name):
    """
    Configure port interface state and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set interface <name> link state up/down
    -	nv show interface <name>

    flow:
    1. Select a random port (state of which is up)
    2. Set selected port state to ‘down’
    3. Verify the configuration applied by running “show” command
    4. Set selected port state to ‘up’
    5. Wait until the port is up
    6. Verify the configuration applied by running “show” command
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()
    TestToolkit.update_tested_ports([selected_port])
    toggle_port_state(selected_port, NvosConsts.LINK_STATE_DOWN, test_name)

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_DOWN).verify_result()

    toggle_port_state(selected_port, NvosConsts.LINK_STATE_UP, test_name)

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


def toggle_port_state(selected_port, port_state, test_name=''):
    selected_port.ib_interface.link.state.set(op_param_name=port_state, apply=True, ask_for_confirmation=True).verify_result()
    with allure.step("Wait till port {} is {}".format(selected_port, port_state)):
        res_obj, duration = OperationTime.save_duration('port goes {}'.format(port_state), '', test_name,
                                                        selected_port.ib_interface.wait_for_port_state, port_state,
                                                        sleep_time=0.2)
        res_obj.verify_result()
        OperationTime.verify_operation_time(duration, 'port goes {}'.format(port_state)).verify_result()


@pytest.mark.ib_interfaces
def test_ib_interface_state_invalid(engines):
    """
    Configure port interface state using an invalid value
    Relevant cli commands:
    -	nv set interface <name> link state up/down
    -	nv show interface <name>

    flow:
    1. Select a random port (state of which is up)
    2. Set selected port state to invalid value -> should fail
    3. Verify the new value remain original in ConfigDB
    4. Verify the new value remain original in StateDB
    5. Verify the value remain original by running “show” command
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    selected_port.ib_interface.link.state.set(op_param_name='invalid_value', apply=True,
                                              ask_for_confirmation=True).verify_result(False)

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


@pytest.mark.ib_interfaces
def test_ib_interface_state_unset(engines):
    """
    Configure port interface state using an invalid value
    Relevant cli commands:
    -	nv set interface <name> link state up/down
     -	nv unset interface <name> link state
    -	nv show interface <name>

    flow:
    1. Select a random port (state of which is up)
    2. 'Set selected port state to ‘up’
    3. Unset selected port state
    4. Wait until the port is up
    5. Verify the new value remain original in ConfigDB
    6. Verify the new value remain original in StateDB
    7. Verify the value remain original by running “show” command
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    selected_port.ib_interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                              ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.link.state.unset(apply=True, ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_ib_interface_state_openapi(test_name):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_interface_state(test_name)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_ib_interface_state_invalid_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_interface_state_invalid(engines)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_ib_interface_state_unset_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_interface_state_unset(engines)
