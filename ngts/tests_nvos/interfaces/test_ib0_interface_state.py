import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts
from ngts.cli_wrappers.nvue.nvue_opensm_clis import NvueOpenSmCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import *
logger = logging.getLogger()


@pytest.mark.ib
def test_ib0_interface_state(engines):
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
    NvueOpenSmCli.enable(engines.dut)
    ib0_port.interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN, apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_DOWN).verify_result()

    ib0_port.interface.link.state.set(value=NvosConsts.LINK_STATE_UP, apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.link.state.label,
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
    ib0_port = MgmtPort('ib0')

    ib0_port.interface.link.state.set(value='invalid_value', apply=False).verify_result(False)

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()


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

    ib0_port.interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN, apply=True).verify_result()

    ib0_port.interface.link.state.unset(apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
        ib0_port.interface.link.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.link.state.label,
                                                      expected_value=NvosConsts.LINK_STATE_UP).verify_result()
