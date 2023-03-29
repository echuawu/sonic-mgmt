import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import *
from ngts.nvos_tools.platform.Platform import Platform

logger = logging.getLogger()

list_with_status_codes = [{'1024': {'status': 'Cable is unplugged.'}}, {'1': {'status': 'Closed by command'}},
                          {'0': {'status': 'No issue was observed'}}, {'2': {'status': 'Negotiation failure'}},
                          {'15': {'status': 'Bad signal integrity'}}, {'59': {'status': 'Other issues'}}]


@pytest.mark.ib
def test_interface_tranceiver_diagnostics_basic(engines):
    """
    The test will check default field and values for tranceiver diagnostic.

    flow:
    1. Run diagnostics for optical cable and verify fields in output
    2. Run diagnostics for link which doesn't exist and verify output
    3. Run diagnostics for link which is not DDMI and verify output
    4. Run diagnostics for not exist port/eth0/ib0/lo, wrong channel name
    5. Run diagnostics with channel-id for link and verify output
    """
    with allure.step("Create System object"):
        platform = Platform()

    with allure.step("Run diagnostics for optical cable and verify fields in output"):
        optical_output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.tranceiver.show('sw16')).get_returned_value()
        fields_to_check = ["cable-length", "cable-type", "channel", "diagnostics-status", "identifier", "temperature",
                           "vendor-date-code", "vendor-name", "vendor-pn", "vendor-rev", "vendor-sn", "voltage"]
        Tools.ValidationTool.verify_field_exist_in_json_output(optical_output_dictionary, fields_to_check).\
            verify_result()

    with allure.step("Run diagnostics for link which doesn't exist and verify output"):
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.tranceiver.show('sw32')).get_returned_value()
        fields_to_check = ["diagnostics-status"]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, fields_to_check).verify_result()
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                          field_name=PlatformConsts.
                                                          HARDWARE_TRANCEIVER_DIAGNOSTIC_STATUS,
                                                          expected_value=PlatformConsts.HARDWARE_TRANCEIVER_NOT_EXIST)\
            .verify_result()

    with allure.step("Run diagnostics for link which is not DDMI and verify output"):
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.tranceiver.show('sw10')).get_returned_value()
        fields_to_check = ["cable-length", "cable-type", "diagnostics-status", "identifier",
                           "vendor-date-code", "vendor-name", "vendor-pn", "vendor-rev", "vendor-sn"]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, fields_to_check).verify_result()
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                          field_name=PlatformConsts.
                                                          HARDWARE_TRANCEIVER_DIAGNOSTIC_STATUS,
                                                          expected_value=PlatformConsts.HARDWARE_TRANCEIVER_NOT_DDMI)\
            .verify_result()

    with allure.step('Run diagnostics for not exist port/eth0/ib0/lo, wrong channel name'):
        output_dictionary = platform.hardware.tranceiver.show('aa')
        assert output_dictionary == 'The requested item does not exist.', "Negative command aa port accepted"
        output_dictionary = platform.hardware.tranceiver.show('eth0')
        assert output_dictionary == 'The requested item does not exist.', "Negative command eth0 port accepted"
        output_dictionary = platform.hardware.tranceiver.show('ib0')
        assert output_dictionary == 'The requested item does not exist.', "Negative command ib0 port accepted"
        output_dictionary = platform.hardware.tranceiver.show('lo')
        assert output_dictionary == 'The requested item does not exist.', "Negative command lo port accepted"
        output_dictionary = platform.hardware.tranceiver.show('sw16 channel aa')
        assert output_dictionary == 'The requested item does not exist.', "Negative command accepted"

    with allure.step("Run diagnostics with channel-id for link and verify output"):
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(
            platform.hardware.tranceiver.show('sw16 channel channel-1')).get_returned_value()
        fields_to_check = ["rx-power", "tx-power", "tx-bias-current"]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, fields_to_check).verify_result()


@pytest.mark.ib
def test_interface_link_diagnostics_basic(engines):
    """
    The test will check default field and values for link diagnostic.

    flow:
    1. Check all fields exist in output command
    2. Validate code to message
    3. Run link diagnostics for port in up state
    4. Run link diagnostics for unplugged port
    5. Run link diagnostics for not exist port/eth0/ib0/lo
    """
    selected_down_ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=NvosConsts.LINK_STATE_DOWN,
                                                                      num_of_ports_to_select=0).get_returned_value()
    selected_up_ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=NvosConsts.LINK_STATE_UP,
                                                                    num_of_ports_to_select=0).get_returned_value()
    all_switch_ports = selected_up_ports + selected_down_ports
    count_of_all_ports = len(all_switch_ports)
    with allure.step('Run nv show interface --view link-diagnostics to check fields, codes'):
        any_port = selected_up_ports[0]
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            any_port.show_interface(port_names='--view link-diagnostics')).get_returned_value()
        assert count_of_all_ports == len(output_dictionary), 'Not fully interface list in --view link-diagnostics'
        field_to_check = ['link', 'diagnostics', 'status']
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()

        with allure.step('Validate code to message'):
            for port in all_switch_ports:
                diagnostics_per_port = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
                    port.ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
                status_dict = output_dictionary[port.name]['link']['diagnostics']
                logging.info("Check each port status in all ports status")
                assert status_dict in list_with_status_codes, "Code doesn't exist in status code list"
                assert diagnostics_per_port == status_dict, \
                    "Tranc diagn for all ports not equal to tranc diagn per port"

    with allure.step('Run nv show interface for port in up state'):
        up_port_output = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            any_port.ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
        assert up_port_output == IbInterfaceConsts.LINK_DIAGNOSTICS_WITHOUT_ISSUE_PORT, "Status code isn't 0"

    with allure.step('Run nv show interface for unplugged port'):
        for port in selected_down_ports:
            if port.name == 'sw32p1':
                unplugged_port_output = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
                    port.ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
                assert unplugged_port_output == IbInterfaceConsts.LINK_DIAGNOSTICS_UNPLUGGED_PORT, \
                    "Status code isn't 1024"

    with allure.step('Run nv show interface for not exist port/eth0/ib0/lo'):
        output_dictionary = any_port.show_interface(port_names='aa link diagnostics')
        assert output_dictionary == 'The requested item does not exist.', "Can run command for aa tranceiver"
        output_dictionary = any_port.show_interface(port_names='eth0 link diagnostics')
        assert output_dictionary == 'The requested item does not exist.', "Can run command for eth0 tranceiver"
        output_dictionary = any_port.show_interface(port_names='ib0 link diagnostics')
        assert output_dictionary == 'The requested item does not exist.', "Can run command for ib0 tranceiver"
        output_dictionary = any_port.show_interface(port_names='lo link diagnostics')
        assert output_dictionary == 'The requested item does not exist.', "Can run command for lo tranceiver"


@pytest.mark.ib
def test_interface_link_diagnostics_functional(engines):
    """
    The test will check functionality of link diagnostics in different scenarios.

    flow:
    1. Get connected to each other ports
    2. Shutdown first one, check code and status for both of them, unset interface
    3. Get redic alias for port
    4. Rewrite tranceiver opcode for port to negative value, check output, should be empty
    5. Rewrite tranceiver opcode for port to 0, check output, system should return correct code and status
    """
    selected_up_ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=NvosConsts.LINK_STATE_UP,
                                                                    num_of_ports_to_select=0).get_returned_value()
    ports_connected = []
    with allure.step('Get ports connected to each others'):
        for port in selected_up_ports:
            if port.name == 'sw15p1' or port.name == 'sw16p1':
                ports_connected.append(port)

    with allure.step('Check default code and status, should be the same'):
        first_port_status = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            ports_connected[0].ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
        second_port_status = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            ports_connected[-1].ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
        assert first_port_status == second_port_status, "Status code isn't 1"

    with allure.step('Shutdown first port and check code and status on both'):
        ports_connected[0].ib_interface.link.state.set(value=NvosConsts.LINK_STATE_DOWN).verify_result()
        first_port_status = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            ports_connected[0].ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
        second_port_status = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            ports_connected[-1].ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
        assert first_port_status == IbInterfaceConsts.LINK_DIAGNOSTICS_CLOSED_BY_COMMAND_PORT, \
            "Status code isn't 1"
        assert second_port_status == IbInterfaceConsts.LINK_DIAGNOSTICS_NEGOTIATION_FAILURE_PORT, \
            "Status code isn't 2"
        ports_connected[0].ib_interface.link.state.unset().verify_result()

    with allure.step("Get Alias for port from Redis cli"):
        cmd = "redis-cli -n 0 HGET ALIAS_PORT_MAP:{0} name".format(ports_connected[0].name)
        with allure.step('Write value to snmp community via redis cli'):
            redis_port_alias = engines.dut.run_cmd(cmd)
            assert redis_port_alias != 0, "Redis command failed"

    with allure.step("Rewrite value of link diagnostics opcode to negative one and check output"):
        cmd = "redis-cli -n 6 HSET 'IB_PORT_TABLE|{0}' 'link_diagnostics_opcode' aa".format(redis_port_alias[1:-1])
        with allure.step('Write value to snmp community via redis cli'):
            redis_cli_output = engines.dut.run_cmd(cmd)
            assert redis_cli_output != 0, "Redis command failed"

        with allure.step('Check output'):
            first_port_status = ports_connected[0].ib_interface.link.diagnostics.show_interface_link_diagnostics()
            assert first_port_status == '{}', "Tranceiver diagn isn't empty"

    with allure.step("Rewrite redis link diagnostics opcode back to 0 and check output, system is stable"):
        cmd = "redis-cli -n 6 HSET 'IB_PORT_TABLE|{0}' 'link_diagnostics_opcode' 0".format(redis_port_alias[1:-1])
        with allure.step('Write value to snmp community via redis cli'):
            redis_cli_output = engines.dut.run_cmd(cmd)
            assert redis_cli_output != 0, "Redis command failed"

        with allure.step('Check output'):
            first_port_status = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
                ports_connected[0].ib_interface.link.diagnostics.show_interface_link_diagnostics()).get_returned_value()
            assert first_port_status == IbInterfaceConsts.LINK_DIAGNOSTICS_WITHOUT_ISSUE_PORT, "Status code isn't 0"
