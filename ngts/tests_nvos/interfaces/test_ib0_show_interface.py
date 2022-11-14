import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import *


logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.simx
def test_ib0_show_interface(engines):
    """
    Run show interface ib0 command and verify the required fields are exist
    command: nv show interface ib0 link
    """
    ib0_port = MgmtPort('ib0')
    with allure.step('Run show command on ib0 port and verify that each field has an appropriate value'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
            ib0_port.show()).get_returned_value()

        validate_interface_fields(ib0_port, output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
def test_ib0_show_interface_link(engines):
    """
    Run show interface ib0 link command and verify the required fields are exist
    only show cmds
    command0: nv show interface ib0 link
    command1: nv show interface ib0 link state
    command2: nv show interface ib0 link stats
    """

    ib0_port = MgmtPort('ib0')

    with allure.step('Run show command on ib0 port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            ib0_port.interface.link.show()).get_returned_value()

        validate_link_fields(ib0_port, output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
def test_ib0_show_interface_stats(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link stats
    """
    ib0_port = MgmtPort('ib0')

    with allure.step('Run show command on ib0 port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
            ib0_port.interface.link.stats.show_interface_link_stats()).get_returned_value()

        validate_stats_fields(ib0_port, output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
def test_ib0_show_interface_ip(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link stats

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name> link stats' on selected port
    3. Verify the required fields are presented in the output
    """
    ib0_port = MgmtPort('ib0')

    with allure.step('Run show command on ib0 port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            ib0_port.interface.ip.show()).get_returned_value()

        validate_ip_fields(ib0_port, output_dictionary)


def validate_interface_fields(selected_port, output_dictionary):
    with allure.step('Check that the following fields exist in the output: type, description, link, ip, ifindex'):
        logging.info('Check that the following fields exist in the output: type, description, link, ip, ifindex')
        field_to_check = [selected_port.interface.type.label,
                          selected_port.interface.description.label,
                          selected_port.interface.link.label,
                          selected_port.interface.ifindex.label,
                          selected_port.interface.ip.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_link_fields(selected_port, output_dictionary):
    with allure.step('Check that all expected fields under link field exist in the output'):
        logging.info('Check that all expected fields under link field exist in the output')
        field_to_check = [selected_port.interface.link.mtu.label,
                          selected_port.interface.link.mac.label,
                          selected_port.interface.link.state.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_stats_fields(selected_port, output_dictionary):
    with allure.step('Check that all expected fields under link-stats field exist in the output'):
        logging.info('Check that all expected fields under link-stats field exist in the output')
        field_to_check = [selected_port.interface.link.stats.carrier_transition.label,
                          selected_port.interface.link.stats.in_bytes.label,
                          selected_port.interface.link.stats.in_drops.label,
                          selected_port.interface.link.stats.in_errors.label,
                          selected_port.interface.link.stats.in_pkts.label,
                          selected_port.interface.link.stats.out_bytes.label,
                          selected_port.interface.link.stats.out_drops.label,
                          selected_port.interface.link.stats.out_errors.label,
                          selected_port.interface.link.stats.out_pkts.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_ip_fields(selected_port, output_dictionary):
    with allure.step('Check that all expected fields under eth ip field exist in the output'):
        logging.info('Check that all expected fields under eth ip field exist in the output')
        field_to_check = [selected_port.interface.ip.address.label]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()
