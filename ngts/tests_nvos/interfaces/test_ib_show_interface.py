import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts

logger = logging.getLogger()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
def test_ib_show_interface_name(engines):
    """
    Run show interface command and verify the required fields are exist
    command: nv show interface <name>

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name>' on selected port
    3. Verify the required fields are presented in the output
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        selected_port.update_output_dictionary()
        validate_one_port_show_output(selected_port)


@pytest.mark.ib_interfaces
def test_ib_show_interface_all_state_up(engines):
    """
    Run show interface command and verify the required fields are exist
    command: nv show interface

    flow:
    1. Run 'nv show interface'
    2. Select a random port from the output
    3. Verify the required fields are presented in the output
    """
    output_dictionary = Tools.OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
        Port.show_interface()).get_returned_value()

    result = Tools.RandomizationTool.select_random_port(requested_ports_state="up",
                                                        requested_ports_logical_state=NvosConsts.LINK_LOG_STATE_ACTIVE,
                                                        requested_ports_type="ib")
    if not result.result:
        return

    selected_port = result.returned_value

    TestToolkit.update_tested_ports([selected_port])

    assert selected_port.name in output_dictionary.keys(), "selected port can't be found in the output"

    selected_port.update_output_dictionary()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        validate_one_port_in_show_all_ports(selected_port, selected_port.show_output_dictionary)

    try:
        with allure.step('Set the state of selected port to "down"'):
            selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN, apply=True,
                                                      ask_for_confirmation=True).verify_result()
            selected_port.ib_interface.wait_for_port_state(state=NvosConsts.LINK_STATE_DOWN).verify_result()

            selected_port.update_output_dictionary()

            with allure.step('Run show command on selected port and verify that each field has an appropriate '
                             'value according to the state of the port'):
                validate_one_port_in_show_all_ports(selected_port, selected_port.show_output_dictionary, False)

            with allure.step('Set the state of selected port to "up"'):
                selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_UP, apply=True,
                                                          ask_for_confirmation=True).verify_result()
                selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP,
                                                               logical_state='Active').verify_result()

            selected_port.update_output_dictionary()

            with allure.step('Run show command on selected port and verify that each field has an appropriate '
                             'value according to the state of the port'):
                validate_one_port_in_show_all_ports(selected_port, selected_port.show_output_dictionary, True)
    finally:
        with allure.step('Set the state of selected port to "up"'):
            selected_port.ib_interface.link.state.set(value=NvosConsts.LINK_STATE_UP, apply=True,
                                                      ask_for_confirmation=True).verify_result()
            selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP,
                                                           logical_state='Active').verify_result()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.simx
def test_ib_show_interface_all_state_down(engines):
    """
    Run show interface command and verify the required fields are exist
    command: nv show interface

    flow:
    1. Run 'nv show interface'
    2. Select a random port from the output
    3. Verify the required fields are presented in the output
    """
    output_dictionary = Tools.OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
        Port.show_interface()).get_returned_value()

    selected_port = Tools.RandomizationTool.select_random_port(requested_ports_state="down",
                                                               requested_ports_logical_state=None,
                                                               requested_ports_type="ib").get_returned_value()
    TestToolkit.update_tested_ports([selected_port])

    assert selected_port.name in output_dictionary.keys(), "selected port can't be found in the output"

    selected_port.update_output_dictionary()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        validate_one_port_in_show_all_ports(selected_port, selected_port.show_output_dictionary, False)


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
def test_ib_show_interface_name_link(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name> link' on selected port
    3. Verify the required fields are presented in the output
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            selected_port.ib_interface.link.show_interface_link()).get_returned_value()

        validate_link_fields(selected_port, output_dictionary)


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
def test_ib_show_interface_name_pluggable(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> pluggable

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name> pluggable' on selected port
    3. Verify the required fields are presented in the output
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            selected_port.ib_interface.pluggable.show_interface_pluggable()).get_returned_value()

        validate_pluggable_fields(selected_port, output_dictionary)


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
def test_ib_show_interface_name_stats(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link stats

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name> link stats' on selected port
    3. Verify the required fields are presented in the output
    """
    selected_port = Tools.RandomizationTool.select_random_port().get_returned_value()

    TestToolkit.update_tested_ports([selected_port])

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
            selected_port.ib_interface.link.stats.show_interface_link_stats()).get_returned_value()

        validate_stats_fields(selected_port, output_dictionary)


def validate_interface_fields(selected_port, output_dictionary):
    with allure.step('Check that the following fields exist in the output: type, description, link, pluggable'):
        logging.info('Check that the following fields exist in the output: type, description, link, pluggable')
        field_to_check = [selected_port.ib_interface.type.label,
                          selected_port.ib_interface.description.label,
                          selected_port.ib_interface.link.label,
                          selected_port.ib_interface.pluggable.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_link_fields(selected_port, output_dictionary, port_up=True):
    with allure.step('Check that all expected fields under link field exist in the output'):
        logging.info('Check that all expected fields under link field exist in the output')
        field_to_check = [selected_port.ib_interface.link.state.label,
                          selected_port.ib_interface.link.ib_subnet.label,
                          selected_port.ib_interface.link.supported_lanes.label,
                          selected_port.ib_interface.link.max_supported_mtu.label,
                          selected_port.ib_interface.link.supported_ib_speeds.label,
                          # selected_port.ib_interface.link.supported_speeds.label,
                          selected_port.ib_interface.link.logical_port_state.label,
                          selected_port.ib_interface.link.physical_port_state.label,
                          selected_port.ib_interface.link.vl_admin_capabilities.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()

        field_to_check = [selected_port.ib_interface.link.mtu.label,
                          selected_port.ib_interface.link.speed.label,
                          selected_port.ib_interface.link.ib_speed.label,
                          selected_port.ib_interface.link.operational_vls.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                               field_to_check, port_up).verify_result()
        # Will be changed
        field_to_check = [selected_port.ib_interface.link.lanes.label]
        res = Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check, port_up)
        logging.warning(res.info)


def validate_pluggable_fields(selected_port, output_dictionary):
    with allure.step('Check that all expected fields under pluggable field exist in the output'):
        logging.info('Check that all expected fields under pluggable field exist in the output')
        field_to_check = [selected_port.ib_interface.pluggable.identifier.label,
                          selected_port.ib_interface.pluggable.vendor_name.label,
                          selected_port.ib_interface.pluggable.vendor_pn.label,
                          selected_port.ib_interface.pluggable.vendor_rev.label,
                          selected_port.ib_interface.pluggable.vendor_sn.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_stats_fields(selected_port, output_dictionary):
    with allure.step('Check that all expected fields under link-stats field exist in the output'):
        logging.info('Check that all expected fields under link-stats field exist in the output')
        field_to_check = [selected_port.ib_interface.link.stats.in_bytes.label,
                          selected_port.ib_interface.link.stats.in_drops.label,
                          selected_port.ib_interface.link.stats.in_errors.label,
                          selected_port.ib_interface.link.stats.in_symbol_errors.label,
                          selected_port.ib_interface.link.stats.in_pkts.label,
                          selected_port.ib_interface.link.stats.out_bytes.label,
                          selected_port.ib_interface.link.stats.out_drops.label,
                          selected_port.ib_interface.link.stats.out_errors.label,
                          selected_port.ib_interface.link.stats.out_pkts.label,
                          selected_port.ib_interface.link.stats.out_wait.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_one_port_show_output(selected_port):
    validate_interface_fields(selected_port, selected_port.show_output_dictionary)

    validate_link_fields(selected_port,
                         selected_port.show_output_dictionary[selected_port.ib_interface.link.label])

    validate_pluggable_fields(selected_port,
                              selected_port.show_output_dictionary[selected_port.ib_interface.pluggable.label])

    validate_stats_fields(selected_port,
                          selected_port.show_output_dictionary[
                              selected_port.ib_interface.link.label][
                              selected_port.ib_interface.link.stats.label])


def validate_one_port_in_show_all_ports(selected_port, output_dictionary, port_up=True):
    field_to_check = [selected_port.ib_interface.type.label,
                      selected_port.ib_interface.description.label,
                      selected_port.ib_interface.link.label,
                      selected_port.ib_interface.pluggable.label]
    Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()

    validate_link_fields(selected_port, output_dictionary[selected_port.ib_interface.link.label], port_up)
