import pytest
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import *
logger = logging.getLogger()


@pytest.mark.ib
def test_ib0_interface_ipv4_address(engines):
    ib0_port = MgmtPort('ib0')
    ipv4_address = Tools.IpTool.select_random_ipv4_address().verify_result()
    ib0_port.interface.ip.address.set(value=ipv4_address, apply=True, ask_for_confirmation=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
        ib0_port.interface.ip.show()).get_returned_value()

    validate_interface_ip_address(ipv4_address, output_dictionary)

    ib0_port.interface.ip.address.unset(apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
        ib0_port.interface.ip.show()).get_returned_value()

    validate_interface_ip_address(ipv4_address, output_dictionary, False)


@pytest.mark.ib
def test_ib0_interface_ipv6_address(engines):
    ib0_port = MgmtPort('ib0')
    ipv6_address = Tools.IpTool.select_random_ipv6_address().verify_result()
    ib0_port.interface.ip.address.set(value=ipv6_address, apply=True, ask_for_confirmation=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
        ib0_port.interface.ip.show()).get_returned_value()

    validate_interface_ip_address(ipv6_address, output_dictionary)

    ib0_port.interface.ip.address.unset(apply=True).verify_result()

    output_dictionary = Tools.OutputParsingTool.parse_show_interface_pluggable_output_to_dictionary(
        ib0_port.interface.ip.show()).get_returned_value()

    validate_interface_ip_address(ipv6_address, output_dictionary, False)


def validate_interface_ip_address(address, output_dictionary, validate_in=True):
    """

    :param address: ip address (could be ipv4 or ipv6)
    :param output_dictionary: the output after running nv show interface ib0 ip
    :param validate_in: True after running set cmd, False after running unset
    """
    with allure.step('check the address field is updated as expected'):
        if validate_in:
            assert address in output_dictionary['address'].keys(), "address not found: {add}".format(add=address)
        if not validate_in:
            assert address not in output_dictionary['address'].keys(), "address found and should be deleted: {add}"\
                .format(add=address)
