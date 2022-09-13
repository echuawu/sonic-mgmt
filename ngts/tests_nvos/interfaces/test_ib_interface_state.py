import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
def test_ib_interface_state(engines):
    """
    Configure port interface state and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set interface <name> link state up/down
    -	nv show interface <name>

    flow:
    1. Select a random port (state of which is up)
    2. Set selected port state to ‘down’
    3. Verify the new value is updated in ConfigDB
    4. Verify the new value is updated in StateDB
    5. Verify the configuration applied by running “show” command
    6. Send traffic through selected port -> should fail
    7. Set selected port state to ‘up’
    8. Wait until the port is up
    9. Verify the new value is updated in ConfigDB
    10. Verify the new value is updated in StateDB
    11. Verify the configuration applied by running “show” command
    12. Send traffic through selected port
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN, apply=True,
                                              ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_DOWN).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show_interface_link()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=selected_port.ib_interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_DOWN).verify_result()

    selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_UP, apply=True,
                                              ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show_interface_link()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=selected_port.ib_interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
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

    selected_port.ib_interface.link.state.set(value='invalid_value', apply=True,
                                              ask_for_confirmation=True).verify_result(False)

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show_interface_link()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=selected_port.ib_interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
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

    selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN, apply=True,
                                              ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.link.state.unset(apply=True, ask_for_confirmation=True).verify_result()

    selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        selected_port.ib_interface.link.show_interface_link()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=selected_port.ib_interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()
