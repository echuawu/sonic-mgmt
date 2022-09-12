import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import *
logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.nvos_ci
def test_ib0_interface_description(engines):
    """
    Configure ib0 interface description and verify the configuration applied successfully
    Relevant cli commands:
    -	nv set interface ib0 description 'ib0 description'
    -	nv show interface ib0

    flow:
    1. Set ib0 port description to ‘ib0 description’
    2. Verify the configuration applied by running “show” command
    3. UnSet ib0 port description
    4. Verify the configuration applied by running “show” command
    """
    with allure.step("test_ib0_interface_description using full interface unset"):
        _test_ib0_interface_description(False)
    with allure.step("test_ib0_interface_description using interface description unset"):
        _test_ib0_interface_description(True)


def _test_ib0_interface_description(full_unset):
    ib0_port = MgmtPort('ib0')

    ib0_port.interface.description.set(value='"ib0 description"', apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        ib0_port.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.description.label,
                                                      expected_value='ib0 description').verify_result()

    if full_unset:
        ib0_port.interface.unset(apply=True).verify_result()
    else:
        ib0_port.interface.description.unset(apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        ib0_port.show()).get_returned_value()

    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=ib0_port.interface.description.label,
                                                      expected_value='').verify_result()
