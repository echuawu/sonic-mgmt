import logging
from ngts.tools.test_utils import allure_utils as allure
import pytest

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.ib.InterfaceConfiguration.Interface import Interface
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts, IbInterfaceConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.ValidationTool import ValidationTool

logger = logging.getLogger()


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.ib
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

        output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
            selected_port.ib_interface.show()).get_returned_value()

        validate_one_port_show_output(output_dictionary)


@pytest.mark.ib_interfaces
def test_ib_show_interface_all_state_up(engines, start_sm):
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

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        selected_port.ib_interface.show()).get_returned_value()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        validate_one_port_in_show_all_ports(output_dictionary)

    try:
        with allure.step('Set the state of selected port to "down"'):
            selected_port.ib_interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                                      ask_for_confirmation=True).verify_result()
            selected_port.ib_interface.wait_for_port_state(state=NvosConsts.LINK_STATE_DOWN).verify_result()

            output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
                selected_port.ib_interface.show()).get_returned_value()

            with allure.step('Run show command on selected port and verify that each field has an appropriate '
                             'value according to the state of the port'):
                validate_one_port_in_show_all_ports(output_dictionary, False)

            with allure.step('Set the state of selected port to "up"'):
                selected_port.ib_interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True,
                                                          ask_for_confirmation=True).verify_result()
                selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP,
                                                               logical_state='Active').verify_result()

            output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
                selected_port.ib_interface.show()).get_returned_value()

            with allure.step('Run show command on selected port and verify that each field has an appropriate '
                             'value according to the state of the port'):
                validate_one_port_in_show_all_ports(output_dictionary, True)
    finally:
        with allure.step('Set the state of selected port to "up"'):
            selected_port.ib_interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True,
                                                      ask_for_confirmation=True).verify_result()
            selected_port.ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP,
                                                           logical_state='Active').verify_result()


@pytest.mark.ib_interfaces
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
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

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        selected_port.ib_interface.show()).get_returned_value()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        validate_one_port_in_show_all_ports(output_dictionary, False)


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.ib
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
            selected_port.ib_interface.link.show()).get_returned_value()

        validate_link_fields(output_dictionary)

    with allure.step("Verify output of link state"):
        with allure.step("Verify json output"):
            json_output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
                selected_port.ib_interface.link.state.show()).get_returned_value()
            assert "up" in json_output.keys() or "down" in json_output.keys(), "up/down state was not found"
        '''with allure.step("Verify string output"):
            str_output = selected_port.ib_interface.link.state.show_interface_link_state(
                output_format=OutputFormat.auto)
            req_fields = ["operational", "applied", "description"]
            Tools.ValidationTool.verify_sub_strings_in_str_output(str_output, req_fields).verify_result()
            assert "up" in str_output or "down" in str_output, "up/down state was not found"'''


@pytest.mark.ib_interfaces
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
            selected_port.ib_interface.link.stats.show()).get_returned_value()

        validate_stats_fields(output_dictionary)


@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.ib
def test_show_interface_filter(engines):
    """
    Run show interface command with filter flag and verify the required fields are exist
    command: nv show interface -- filter "<filter>=<value>"

    flow:
    1. Run show interface without filter
    2. Select filter type and value from existing output
    3. Create expected dictionary according to the selected filter
    4. Run show interface with the selected filter
    5. Compare between filtered output dictionary to expected dictionary (at least one should be found)
    6. Run show interface with an empty filter (returns all data)
    7. Compare between filtered output dictionary to the full dictionary
    8. Run show interface with existing filter but value not exist
    9. Run show interface with a filter that does not exist
    """
    interface = Interface()

    with allure.step('Run show interface without filter'):
        output_dict = Tools.OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
            interface.show()).get_returned_value()

    with allure.step('Select filter type and value from existing output'):
        random_key = RandomizationTool.select_random_value(list(output_dict.keys())).get_returned_value()
        filter_name = RandomizationTool.select_random_value(list(output_dict[random_key].keys())).get_returned_value()
        value = output_dict[random_key][filter_name]

    with allure.step('Create expected dictionary according to the selected filter'):
        filtered_expected = {}
        for key in output_dict.keys():
            if filter_name in output_dict[key].keys():
                if value == output_dict[key][filter_name]:
                    filtered_expected.update({key: output_dict[key]})

    with allure.step('Run show interface with the selected filter'):
        output_dict_filtered = Tools.OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
            interface.show(f'--filter "{filter_name}={value}"')).get_returned_value()

    with allure.step('Compare between filtered output dictionary to expected dictionary'
                     '(at least one should be found)'):
        ValidationTool.compare_nested_dictionary_content(output_dict_filtered, filtered_expected).verify_result()

    with allure.step('Run show interface with an empty filter (returns all data)'):
        output_dict_filtered = Tools.OutputParsingTool.parse_show_all_interfaces_output_to_dictionary(
            interface.show('--filter ""')).get_returned_value()

    with allure.step('Compare between filtered output dictionary to the full dictionary'):
        ValidationTool.compare_nested_dictionary_content(output_dict_filtered, output_dict).verify_result()

    with allure.step('Run show interface with existing filter but value not exist'):
        value = 'value_not_exists'
        output_dict_filtered = interface.show(f'--filter "{filter_name}={value}"', output_format='auto')
        assert output_dict_filtered == 'No Data'

    with allure.step('Run show interface with a filter that does not exist'):
        filter_name = 'filter_not_exist'
        output_dict_filtered = interface.show(f'--filter "{filter_name}={value}"',
                                              output_format='auto', should_succeed=False)
        assert 'Error: No match found for filter depth of 4.' in output_dict_filtered


def validate_interface_fields(output_dictionary):
    with allure.step('Check that the following fields exist in the output: type, link'):
        logging.info('Check that the following fields exist in the output: type, link')
        field_to_check = [IbInterfaceConsts.TYPE, IbInterfaceConsts.LINK]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_link_fields(output_dictionary, port_up=True):
    with allure.step('Check that all expected fields under link field exist in the output'):
        logging.info('Check that all expected fields under link field exist in the output')
        field_to_check = [IbInterfaceConsts.LINK_STATE,
                          IbInterfaceConsts.LINK_IB_SUBNET,
                          IbInterfaceConsts.LINK_SUPPORTED_LANES,
                          IbInterfaceConsts.LINK_MAX_SUPPORTED_MTU,
                          IbInterfaceConsts.LINK_SUPPORTED_IB_SPEEDS,
                          # IbInterfaceConsts.LINK_SUPPORTED_SPEEDS,
                          IbInterfaceConsts.LINK_LOGICAL_PORT_STATE,
                          IbInterfaceConsts.LINK_PHYSICAL_PORT_STATE,
                          IbInterfaceConsts.LINK_VL_ADMIN_CAPABILITIES]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()

        field_to_check = [IbInterfaceConsts.LINK_MTU,
                          IbInterfaceConsts.LINK_SPEED,
                          IbInterfaceConsts.LINK_IB_SPEED,
                          IbInterfaceConsts.LINK_OPERATIONAL_VLS]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                               field_to_check, port_up).verify_result()
        # Will be changed
        field_to_check = [IbInterfaceConsts.LINK_LANES]
        res = Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check, port_up)
        logging.warning(res.info)


def validate_stats_fields(output_dictionary):
    with allure.step('Check that all expected fields under link-stats field exist in the output'):
        logging.info('Check that all expected fields under link-stats field exist in the output')
        field_to_check = [IbInterfaceConsts.LINK_STATS_IN_BYTES,
                          IbInterfaceConsts.LINK_STATS_IN_DROPS,
                          IbInterfaceConsts.LINK_STATS_IN_ERRORS,
                          IbInterfaceConsts.LINK_STATS_IN_SYMBOL_ERRORS,
                          IbInterfaceConsts.LINK_STATS_IN_PKTS,
                          IbInterfaceConsts.LINK_STATS_OUT_BYTES,
                          IbInterfaceConsts.LINK_STATS_OUT_DROPS,
                          IbInterfaceConsts.LINK_STATS_OUT_ERRORS,
                          IbInterfaceConsts.LINK_STATS_OUT_PKTS,
                          IbInterfaceConsts.LINK_STATS_OUT_WAIT]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_one_port_show_output(output_dictionary):
    validate_interface_fields(output_dictionary)

    validate_link_fields(output_dictionary[IbInterfaceConsts.LINK])

    validate_stats_fields(output_dictionary[IbInterfaceConsts.LINK][IbInterfaceConsts.LINK_STATS])


def validate_one_port_in_show_all_ports(output_dictionary, port_up=True):
    field_to_check = [IbInterfaceConsts.TYPE, IbInterfaceConsts.LINK]
    Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()

    validate_link_fields(output_dictionary[IbInterfaceConsts.LINK], port_up)


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.ib
def test_ib_show_interface_name_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_name(engines)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_ib_show_interface_all_state_up_openapi(engines, start_sm):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_all_state_up(engines, start_sm)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_ib_show_interface_all_state_down_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_all_state_down(engines)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
@pytest.mark.nvos_ci
@pytest.mark.ib
def test_ib_show_interface_name_link_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_name_link(engines)


@pytest.mark.openapi
@pytest.mark.ib_interfaces
def test_ib_show_interface_name_stats_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_name_stats(engines)