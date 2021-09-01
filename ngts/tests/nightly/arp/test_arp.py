import allure
import logging
import pytest
import re
import copy


from retry.api import retry_call
from ngts.helpers.arp_helper import verify_arp_entry_in_arp_table,\
    verify_arp_entry_not_in_arp_table, arp_request_traffic_validation, INTERFACE_TYPE_LIST, \
    clear_dynamic_arp_table_and_check_the_specified_arp_entry_deleted, \
    send_arp_request_and_check_update_corresponding_entry_into_arp_table
from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon
from ngts.cli_wrappers.sonic.sonic_arp_clis import SonicArpCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.helpers.network import gen_new_mac_based_old_mac
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli

logger = logging.getLogger()


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('Test corresponding arp is clean after dut shutdown the specified interface')
def test_corresponding_dynamic_arp_is_cleaned_after_dut_interface_down(engines, players, pre_test_interface_data, interface_type):
    """
    Verify that a dynamic arp entry is removed after shutting down the link on which it was learnt.
    1. Host A sends ARP request for broadcast
    2. Verify DUT add the Host A's IP and MAC into the ARP table
    2. DUT shutdown the specified interface
    3. Verify the arp entry related to the interface will be cleaned
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """
    try:

        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Send broadcast arp request and check update the corresponding arp entry into arp table'):
            send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data)

        with allure.step("Shutdown DUT interface:".format(interface_data["dut_interface"])):
            if interface_type is "vlan":
                SonicVlanCli.shutdown_vlan(engines.dut, interface_data["dut_vlan_id"])
            else:
                SonicInterfaceCli.disable_interface(engines.dut, interface_data["dut_interface"])

        with allure.step("Check the corresponding arp related to {}  has been cleaned".format(interface_data["dut_interface"])):
            retry_call(verify_arp_entry_not_in_arp_table, fargs=[engines.dut, interface_data["host_ip"]], tries=3, delay=10, logger=logger)

        with allure.step("DUT sartup interface:".format(interface_data["dut_interface"])):
            SonicInterfaceCli.enable_interface(engines.dut, interface_data["dut_interface"])

    except Exception as err:
        raise AssertionError(err)
    finally:
        if interface_type is "vlan":
            SonicVlanCli.startup_vlan(engines.dut, interface_data["dut_vlan_id"])
        else:
            SonicInterfaceCli.enable_interface(engines.dut, interface_data["dut_interface"])


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('Test arp entry update by changing mac and ip')
def test_change_mac_ip_lead_arp_entry_update(engines, players, pre_test_interface_data, interface_type):
    """
    Verify arp entry update by changing mac and ip
    1. Host sends ARP request for broadcast
    2. Verify DUT add the Host's IP and MAC into the ARP table
    3. Host sends ARP request with new mac
    4. Verify DUT Update the old entry with new mac
    5. Host sends ARP request with new ip
    6. Verify the arp entry related new ip is added into the arp table, the old one related the old ip still exist.
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """
    try:
        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Send arp request and check update the corresponding arp entry into arp table'):
            send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data)

        with allure.step("Host sends ARP request with new mac and check new mac is updated into arp table"):
            new_mac = gen_new_mac_based_old_mac(interface_data["host_mac"])
            interface_data["host_mac"] = new_mac
            send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data)

        with allure.step('Host sends ARP request to DUT with new ip'):
            old_ip = interface_data["host_ip"]
            new_ip = re.sub(".2", ".8", old_ip)
            interface_data["host_ip"] = new_ip
            arp_request_traffic_validation(players=players, interface_data=interface_data,
                                           dst_mac="FF:FF:FF:FF:FF:FF", receive_packet_count=1)
            with allure.step("Verify DUT add the new Host's IP and MAC into the ARP table"):
                retry_call(verify_arp_entry_in_arp_table,
                           fargs=[engines.dut, interface_data["host_ip"],
                                  interface_data["host_mac"], interface_data["dut_interface"],
                                  interface_data["dut_vlan_id"]],
                           tries=3, delay=10, logger=logger)
            with allure.step("Verify DUT old Host's IP and MAC into the ARP table"):
                retry_call(verify_arp_entry_in_arp_table,
                           fargs=[engines.dut, old_ip,
                                  interface_data["host_mac"], interface_data["dut_interface"],
                                  interface_data["dut_vlan_id"]],
                           tries=3, delay=10, logger=logger)

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('Test src ip and dst ip not in one subnet')
def test_src_ip_dst_ip_not_in_one_subnet(engines, players, pre_test_interface_data, interface_type):
    """
    Verify when arp request with src ip and dst ip not in one subnet, the corresponding arp will not be added into
    arp table, and dut will not reply the arp
    1. Host sends ARP request for broadcast with src ip and dst ip not in one subnet
    2. Verify DUT not add the Host's IP and MAC into the ARP table
    3. Verify host not receive the arp response
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """
    try:
        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Send ARP request from host to DUT and check arp response will not be received on the host'):
            interface_data["host_ip"] = "1.2.3.4"
            arp_request_traffic_validation(players=players, interface_data=interface_data,
                                           dst_mac="FF:FF:FF:FF:FF:FF", receive_packet_count=0)

        with allure.step("Verify DUT not add Host's IP and MAC into the ARP table"):
            retry_call(verify_arp_entry_not_in_arp_table,
                       fargs=[engines.dut, interface_data["host_ip"]],
                       tries=3,
                       delay=10,
                       logger=logger)

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('Test static arp')
def test_static_arp(engines, players, pre_test_interface_data, interface_type):
    """
    Verify the following behaviors
    1. When there is a dynamic arp, static arp can not overide it
    2. DUT can add static arp into arp table
    3. Static arp will not be updated by dynamic arp
    4. Static arp can be removed
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """
    try:
        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Generate one dynamic arp entry'):
            send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data)

        with allure.step('Add static arp with the same Ip and interface, and check it will not be permitted'):
            regrex_file_exists = ".*RTNETLINK answers: File exists.*"
            if interface_type == "vlan":
                dev = "Vlan{}".format(interface_data["dut_vlan_id"])
            else:
                dev = interface_data["dut_interface"]
            output = IpCliCommon.add_ip_neigh(engines.dut, interface_data["host_ip"],
                                              interface_data["host_mac"], dev, action="add")
            assert re.match(regrex_file_exists, output), "Static arp entry has unexpectedly overridden a dynamic entry"

        with allure.step("Clear dynamic arp"):
            clear_dynamic_arp_table_and_check_the_specified_arp_entry_deleted(engines.dut, interface_data["host_ip"])

        with allure.step('DUT add static arp'):
            output = IpCliCommon.add_ip_neigh(engines.dut, interface_data["host_ip"],
                                              interface_data["host_mac"], dev, action="add")
            assert not output, "Add static arp failed. Output is {}".format(output)

        with allure.step('DUT check static arp is in arp table'):
            retry_call(verify_arp_entry_in_arp_table,
                       fargs=[engines.dut, interface_data["host_ip"], interface_data["host_mac"],
                              interface_data["dut_interface"], interface_data["dut_vlan_id"]],
                       tries=3, delay=10, logger=logger)

        with allure.step('Host sends dynamic ARP request to DUT '):
            old_mac = interface_data["host_mac"]
            interface_data["host_mac"] = gen_new_mac_based_old_mac(old_mac)
            arp_request_traffic_validation(players=players, interface_data=interface_data,
                                           dst_mac="FF:FF:FF:FF:FF:FF", receive_packet_count=1)

        with allure.step("Verify that the dynamic arp entry didn't override the static one"):
            current_mac_in_arp_table = SonicArpCli.show_arp_table(engines.dut)[interface_data["host_ip"]]["MacAddress"]
            assert interface_data["host_mac"] != current_mac_in_arp_table, \
                "Dynamic ARP mac: {} overide the static arp mac:{}".format(
                    interface_data["host_mac"], current_mac_in_arp_table)

        with allure.step('DUT del static arp'):
            IpCliCommon.del_ip_neigh(engines.dut, interface_data["host_ip"], old_mac, dev)

        with allure.step('DUT check static arp is deleted from the arp table'):
            retry_call(verify_arp_entry_not_in_arp_table, fargs=[engines.dut, interface_data["host_ip"]],
                       tries=3, delay=10, logger=logger)

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('test arp gratuitous without arp update')
def test_arp_gratuitous_without_arp_update(engines, players, pre_test_interface_data, interface_type):
    """
    Verify When receiving gratuitous ARP packet, if it was not resolved in ARP table before,
    DUT should discard the request and won't add ARP entry for the GARP
    1. DUT clear all arp table by sonic-clear arp
    2. Host A sends GARP request
    3. Verify Host A not receive any arp response
    4. Verify DUT not add the Host A's IP and MAC into the ARP table
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """
    try:

        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Host A sends GARP request to DUT and check that not receives the arp response'):
            arp_request_traffic_validation(players=players, interface_data=interface_data, dst_mac="FF:FF:FF:FF:FF:FF",
                                           receive_packet_count=0, is_garp=True)

        with allure.step("Verify DUT not add Host's IP and MAC into the ARP table"):
            retry_call(verify_arp_entry_not_in_arp_table, fargs=[engines.dut, interface_data["host_ip"]], tries=3,
                       delay=10,
                       logger=logger)

    except Exception as err:
        raise AssertionError(err)


@pytest.mark.parametrize("interface_type", INTERFACE_TYPE_LIST)
@allure.title('test arp gratuitous with arp update')
def test_arp_gratuitous_with_arp_update(engines, players, pre_test_interface_data, interface_type):
    """
    Verify When receiving gratuitous ARP packet, if it was resolved in ARP table before,
    DUT should update ARP entry with new mac
    1. DUT clear all arp table by conic-clear arp
    2. Generater one arp by Host sendsing one unicast ARP
    3. Check A''s IP and MAC have been added into the ARP table
    4. Host A sends GARP request
    5. Verify Host A not receive any arp response
    6. Verify DUT update ARP entry with new mac
    :param engines: engines fixture
    :param players: players fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    :param interface_type: interface type
    """

    try:
        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data[interface_type])
            logger.info("interface test data for {} is: {}".format(interface_type, interface_data))

        with allure.step('Send a unicast arp request and check update the corresponding arp entry into arp table'):
            send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data,
                                                                                 request_type="unicast")

        with allure.step('Host A sends GARP request to DUT with new mac and check that not receives the arp response'):
            interface_data["host_mac"] = "ec:23:9e:c3:b1:f0"
            arp_request_traffic_validation(players=players, interface_data=interface_data, dst_mac="FF:FF:FF:FF:FF:FF",
                                           receive_packet_count=0, is_garp=True)

        with allure.step("Verify DUT add Host IP and MAC into the ARP table"):
            retry_call(verify_arp_entry_in_arp_table,
                       fargs=[engines.dut, interface_data["host_ip"],
                              interface_data["host_mac"],
                              interface_data["dut_interface"],
                              interface_data["dut_vlan_id"]],
                       tries=3, delay=10, logger=logger)

    except Exception as err:
        raise AssertionError(err)


@allure.title('test arp proxy')
def test_arp_proxy(engines, players, interfaces, pre_test_interface_data):
    """
    Verify arp behavior when arp proxy is disable/enable in one l2 domain
    1. Disable arp proxy in vlan 40
    2. Host A sends arp request to Host B
    3. Verify Host B reply the arp request
    4. Verify host A's mac and ip doesn't exist on DUT's arp table
    5. Enable arp proxy in vlan 40
    6. Host A sends arp request to Host B
    7. Verify Dut reply the arp request, and host A's mac and ip exists on DUT's arp table
    8. Recover the arp proxy to the default value by disabling it
    :param engines: engines fixture
    :param players: players fixture
    :param interfaces: interfaces fixture
    :param pre_test_interface_data: pre_test_interface_data fixture
    """
    try:
        with allure.step('Get test interface data'):
            interface_data = copy.deepcopy(pre_test_interface_data["vlan"])
            logger.info("interface test data  is: {}".format(interface_data))
        with allure.step('Disable arp proxy and check arp behavior'):
            with allure.step('Disable arp proxy'):
                SonicVlanCli.disable_vlan_arp_proxy(engines.dut, interface_data["dut_vlan_id"])
            with allure.step(
                    "Host A Send a broadcast arp request to host B, and Host B reply it"):
                host_b_ip = "40.0.0.10"
                host_b_mac = SonicMacCli.get_mac_address_for_interface(engines.hb, interfaces.hb_dut_1)
                dut_mac = interface_data["dut_mac"]
                interface_data["dut_ip"] = host_b_ip
                interface_data["dut_mac"] = host_b_mac
                arp_request_traffic_validation(players=players, interface_data=interface_data,
                                               dst_mac="FF:FF:FF:FF:FF:FF",
                                               receive_packet_count=1)
            with allure.step("Verify DUT not add Host's IP and MAC into the ARP table"):
                retry_call(verify_arp_entry_not_in_arp_table, fargs=[engines.dut, interface_data["host_ip"]], tries=3,
                           delay=10,
                           logger=logger)

        with allure.step('Enable arp proxy and check arp behavior'):
            with allure.step('Enable arp proxy'):
                SonicVlanCli.enable_vlan_arp_proxy(engines.dut, interface_data["dut_vlan_id"])
            with allure.step(
                    "Host A Send a broadcast arp request to host B, and DUT reply it"):
                interface_data["dut_mac"] = dut_mac
                send_arp_request_and_check_update_corresponding_entry_into_arp_table(engines, players, interface_data)

    except Exception as err:
        raise AssertionError(err)
    finally:
        with allure.step('Recover the default config of arp proxy by disabing arp proxy'):
            SonicVlanCli.disable_vlan_arp_proxy(engines.dut, interface_data["dut_vlan_id"])
