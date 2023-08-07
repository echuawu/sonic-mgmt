import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import *
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.ib
def test_ib0_interface_state(engines, start_sm):
    """
    Configure ib0 interface state and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set interface ib0 link state up/down
    -	nv show interface ib0

    flow:
    1. Set ib0 port state to ‘down’
    2. Verify the configuration applied by running “show” command
    3. Set ib0 port state to ‘up’
    4. Verify the configuration applied by running “show” command
    """
    ib0_port = MgmtPort('ib0')
    ib0_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True, ask_for_confirmation=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_DOWN).verify_result()

    ib0_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True, ask_for_confirmation=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


@pytest.mark.ib
def test_ib0_interface_state_invalid(engines):
    """
    Configure port interface state using an invalid value
    Relevant cli commands:
    -	nv set interface ib0 link state up/down
    -	nv show interface ib0

    flow:
    1. Set ib0 port state to invalid value -> should fail
    2. Verify the value remain original by running “show” command
    """
    with allure.step("Create MgmtPort class and check current ib0 state"):
        ib0_port = MgmtPort('ib0')
        current_state = ib0_port.interface.link.state.show()
        current_state = NvosConsts.LINK_STATE_UP if NvosConsts.LINK_STATE_UP in current_state else NvosConsts.LINK_STATE_DOWN
        logging.info(f"ib0 current state: {current_state}")

    with allure.step("Set invalid state for ib0"):
        ib0_port.interface.link.state.set(op_param_name='invalid_value', apply=True,
                                          ask_for_confirmation=True).verify_result(False)

    with allure.step("Verify the state remained unchanged"):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            ib0_port.interface.link.show()).get_returned_value()

        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                          field_name=IbInterfaceConsts.LINK_STATE,
                                                          expected_value=current_state).verify_result()


@pytest.mark.ib
def test_ib0_interface_state_unset(engines):
    """
    Configure port interface state using an invalid value
    Relevant cli commands:
    -	nv set interface ib0 link state up/down
     -	nv unset interface ib0 link state
    -	nv show interface ib0

    flow:
    1. Set ib0 port state to ‘up’
    2. Unset ib0 port state
    3. Verify the value remain original by running “show” command
    """
    ib0_port = MgmtPort('ib0')
    NvueOpenSmCli.enable(engines.dut)
    ib0_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                      ask_for_confirmation=True).verify_result()

    ib0_port.interface.link.state.unset(apply=True, ask_for_confirmation=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=IbInterfaceConsts.LINK_STATE,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.ib
def test_ib0_interface_state_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib0_interface_state(engines)


@pytest.mark.openapi
@pytest.mark.ib
def test_ib0_interface_state_invalid_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib0_interface_state_invalid(engines)


@pytest.mark.openapi
@pytest.mark.ib
def test_ib0_interface_state_unset_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib0_interface_state_unset(engines)
