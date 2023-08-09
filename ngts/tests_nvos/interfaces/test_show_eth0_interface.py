import pytest

from ngts.nvos_constants.constants_nvos import SystemConsts, IpConsts
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import *
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.ib_interfaces
@pytest.mark.nvos_chipsim_ci
def test_mgmt_show_interface(engines):
    """
    Run show interface eth0 command and verify the required fields are exist
    command: nv show interface eth0 link
    """

    mgmt_port = MgmtPort()
    with allure.step('Run show command on mgmt port and verify that each field has an appropriate value'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
            mgmt_port.interface.show()).get_returned_value()

        validate_interface_fields(output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_mgmt_show_interface_link(engines):
    """
    Run show interface eth0 link command and verify the required fields are exist
    only show cmds
    command0: nv show interface eth0 link
    command1: nv show interface eth0 link state
    command2: nv show interface eth0 link stats
    """

    mgmt_port = MgmtPort()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            mgmt_port.interface.link.show()).get_returned_value()

        validate_link_fields(output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_ib_show_interface_stats(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link stats
    """
    mgmt_port = MgmtPort()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
            mgmt_port.interface.link.stats.show()).get_returned_value()

        validate_stats_fields(output_dictionary)


@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_ib_show_interface_ip(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface <name> link stats

    flow:
    1. Select a random port (status of which is up)
    2. Run 'nv show interface <name> link stats' on selected port
    3. Verify the required fields are presented in the output
    """
    mgmt_port = MgmtPort()

    with allure.step('Run show command on selected port and verify that each field has an appropriate '
                     'value according to the state of the port'):
        output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
            mgmt_port.interface.ip.show()).get_returned_value()

        validate_ip_fields(output_dictionary)


def check_dhcp(mgmt_port, ipv4=True):
    # Run the desired show command (ipv4 / ipv6)
    if ipv4:
        with allure.step('Run show command on dhcp-client (ipv4) of eth0 mgmt port'):
            output_json = mgmt_port.interface.ip.dhcp_client.show()
    else:   # ipv6
        with allure.step('Run show command on dhcp-client (ipv6) of eth0 mgmt port'):
            output_json = mgmt_port.interface.ip.dhcp_client6.show()

    output_dict = Tools.OutputParsingTool.parse_json_str_to_dictionary(output_json).get_returned_value()

    # Verify the result
    with allure.step('Verify required fields exist in the show output, and set to default value'):
        Tools.ValidationTool.validate_fields_values_in_output(
            expected_fields=SystemConsts.DHCP_SHOW_FIELDS, expected_values=SystemConsts.DHCP_SHOW_DEFAULT_VALUES,
            output_dict=output_dict).verify_result()


@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.interfaces
@pytest.mark.nvos_chipsim_ci
def test_show_interface_ip_dhcp(engines):
    """
    Run show interface command and verify the required fields exist
    Command: nv show interface eth ip dhcp_client (and dhcp_client6)

    flow:
    1. Select eth0 port (status of which is up)
    2. Run 'nv show interface eth0 ip dhcp_client'
    3. Verify the required fields are presented in the output and set to default
    4. Run 'nv show interface eth0 ip dhcp_client6'
    5. Verify the required fields are presented in the output and set to default
    """
    mgmt_port = MgmtPort('eth0')

    check_dhcp(mgmt_port=mgmt_port, ipv4=True)      # test ipv4
    check_dhcp(mgmt_port=mgmt_port, ipv4=False)     # same test on ipv6


def validate_interface_fields(output_dictionary):
    with allure.step('Check that the following fields exist in the output: type, link, ip, ifindex'):
        logging.info('Check that the following fields exist in the output: type, link, ip, ifindex')
        field_to_check = [IbInterfaceConsts.TYPE,
                          IbInterfaceConsts.LINK,
                          IbInterfaceConsts.IFINDEX,
                          IbInterfaceConsts.IP]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_link_fields(output_dictionary):
    with allure.step('Check that all expected fields under link field exist in the output'):
        logging.info('Check that all expected fields under link field exist in the output')
        field_to_check = [IbInterfaceConsts.LINK_MTU,
                          IbInterfaceConsts.LINK_SPEED,
                          IbInterfaceConsts.LINK_MAC,
                          IbInterfaceConsts.LINK_DUPLEX,
                          IbInterfaceConsts.LINK_STATE]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_stats_fields(output_dictionary):
    with allure.step('Check that all expected fields under link-stats field exist in the output'):
        logging.info('Check that all expected fields under link-stats field exist in the output')
        field_to_check = [IbInterfaceConsts.LINK_STATS_CARRIER_TRANSITION,
                          IbInterfaceConsts.LINK_STATS_IN_BYTES,
                          IbInterfaceConsts.LINK_STATS_IN_DROPS,
                          IbInterfaceConsts.LINK_STATS_IN_ERRORS,
                          IbInterfaceConsts.LINK_STATS_IN_PKTS,
                          IbInterfaceConsts.LINK_STATS_OUT_BYTES,
                          IbInterfaceConsts.LINK_STATS_OUT_DROPS,
                          IbInterfaceConsts.LINK_STATS_OUT_ERRORS,
                          IbInterfaceConsts.LINK_STATS_OUT_PKTS]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


def validate_ip_fields(output_dictionary):
    with allure.step('Check that all expected fields under eth ip field exist in the output'):
        logging.info('Check that all expected fields under eth ip field exist in the output')
        field_to_check = [IbInterfaceConsts.IP_VRF,
                          IbInterfaceConsts.IP_ADDRESS,
                          IbInterfaceConsts.IP_DHCP,
                          IbInterfaceConsts.IP_DHCP6,
                          IpConsts.ARP_TIMEOUT,
                          IpConsts.AUTOCONF]
        Tools.ValidationTool.verify_field_exist_in_json_output(output_dictionary, field_to_check).verify_result()


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_ci
@pytest.mark.ib_interfaces
@pytest.mark.nvos_chipsim_ci
def test_mgmt_show_interface_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_mgmt_show_interface(engines)


@pytest.mark.openapi
@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_mgmt_show_interface_link_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_mgmt_show_interface_link(engines)


@pytest.mark.openapi
@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_ib_show_interface_stats_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_stats(engines)


@pytest.mark.openapi
@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
def test_ib_show_interface_ip_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_ib_show_interface_ip(engines)


@pytest.mark.openapi
@pytest.mark.ib
@pytest.mark.simx
@pytest.mark.interfaces
@pytest.mark.nvos_chipsim_ci
def test_show_interface_ip_dhcp_openapi(engines):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_show_interface_ip_dhcp(engines)
