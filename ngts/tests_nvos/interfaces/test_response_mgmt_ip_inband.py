import pytest
import time

from ngts.nvos_constants.constants_nvos import ApiType, DatabaseConst, IpConsts, UfmMadConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts
from ngts.nvos_tools.infra.DatabaseTool import DatabaseTool
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.IpTool import IpTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RegisterTool import RegisterTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_feature_state(engines, prepare_traffic, test_api):
    """
    Validate configuring feature state by using the fae commands:
    - show fae ib ufm-mad command
    - set/unset ib ufm-mad state command

    Test flow:
    1. Verify feature state enabled and IP address configured:
    2. Disable feature:
    3. Validate ufm-mad state:
    4. Enable feature (by set):
    5. Validate ufm-mad state:
    6. Disable feature:
    7. Enable feature (by unset):
    8. Validate ufm-mad state:
    """
    TestToolkit.tested_api = test_api
    engines_dut = engines.dut
    engines_ha = engines.ha
    fae = Fae()

    try:
        with allure.step("Get mgmt port ip addresses"):
            mgmt_port = MgmtPort('eth0')
            mgmt_ip_dict = get_mgmt_port_ip_addresses(mgmt_port, engines_dut)

        with allure.step("Verify feature state enabled and IP address configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Disable ufm-mad feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True).verify_result()

        with allure.step("Validate ufm-mad state disabled and IP address is empty"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.DISABLED.value)

        with allure.step("Enable feature (by set command)"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                               apply=True).verify_result()

        with allure.step("Verify feature state enabled and IP address configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])
            time.sleep(UfmMadConsts.CONFIG_TIME)

        with allure.step("Disable ufm-mad feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True).verify_result()

        with allure.step("Enable feature (by unset command)"):
            fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True).verify_result()

        with allure.step("Verify feature state enabled and IP address configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

    finally:
        with allure.step("Set feature state to default"):
            fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True).verify_result()


@pytest.mark.interface
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_configure_mgmt_port_ipv4(engines, topology_obj, prepare_traffic, test_api):
    """
    Validate configuring management port ipv4 address in several cases

    Test flow:
    1. Disable feature
    2. Update mgmt port ipv4 address (static ip)
    3. Validate ufm-mad
    4. Enable feature (by set)
    5. Update mgmt port ipv4 address (another static ip)
    6. Validate ufm-mad
    7. Delete mgmt port ipv4 address (zeros)
    8. Validate ufm-mad
    9. Set to default mgmt port ipv4 address
    """
    TestToolkit.tested_api = test_api
    engines_dut = engines.dut
    engines_ha = engines.ha
    serial_engine = topology_obj.players['dut_serial']['engine']
    fae = Fae()

    try:
        with allure.step("Get mgmt port ip addresses"):
            mgmt_port = MgmtPort('eth0')
            mgmt_ip_dict = get_mgmt_port_ip_addresses(mgmt_port, engines_dut)

            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Disable ufm-mad feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True).verify_result()

        with allure.step("Update mgmt port ipv4 address (static ip)"):
            mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV4, apply=True,
                                               ask_for_confirmation=True).verify_result()

        # Connection in SSH is lost, continue in serial port
        with allure.step("Validate ufm-mad state disabled and IP address is empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.DISABLED.value)

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engine=serial_engine, state=UfmMadConsts.State.DISABLED.value)

        with allure.step("Enable feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                               apply=True, dut_engine=serial_engine).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        with allure.step("Validate ufm-mad state enabled and IP static address is configured"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         UfmMadConsts.STATIC_IPV4, mgmt_ip_dict[UfmMadConsts.IPV6_SLAAC])

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(serial_engine, UfmMadConsts.State.ENABLED.value,
                                    UfmMadConsts.STATIC_IPV4, mgmt_ip_dict[UfmMadConsts.IPV6_SLAAC])

        with allure.step("Update mgmt port ipv4 address when ufm-mad state is enabled"):
            mgmt_port.interface.ip.address.unset(dut_engine=serial_engine, apply=True).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        # Connection in SSH is back, continue in engines.dut
        with allure.step("Validate ufm-mad state enabled and IP address is configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engines_dut, UfmMadConsts.State.ENABLED.value,
                                    mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Delete mgmt port ipv4 address (set ip 0.0.0.0/0)"):
            mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.ZEROS_IPV4, apply=True,
                                               ask_for_confirmation=True).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        # Connection in SSH is lost, continue in serial port
        with allure.step("Validate ufm-mad state disabled and IPV4 address is empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         ipv6=mgmt_ip_dict[UfmMadConsts.IPV6_SLAAC])

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engine=serial_engine, state=UfmMadConsts.State.ENABLED.value,
                                    ipv6=mgmt_ip_dict[UfmMadConsts.IPV6])

    finally:
        with allure.step("Set to default mgmt port address and ufm-mad feature state"):
            mgmt_port.interface.ip.address.unset(dut_engine=serial_engine).verify_result()
            fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True, dut_engine=serial_engine).verify_result()


@pytest.mark.interface
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_configure_mgmt_port_ipv6(engines, topology_obj, prepare_traffic, test_api):
    """
    Validate configuring management port ipv6 address in several cases

    Test flow:
    1. Disable feature
    2. Update mgmt port ipv6 address (static ip)
    3. Validate ufm-mad
    4. Enable feature (by set)
    5. Update mgmt port ipv6 address (another static ip)
    6. Validate ufm-mad
    7. Delete mgmt port ipv6 address (zeros)
    8. Validate ufm-mad
    9. Set to default mgmt port ipv4 address
    """
    TestToolkit.tested_api = test_api
    engines_dut = engines.dut
    engines_ha = engines.ha
    serial_engine = topology_obj.players['dut_serial']['engine']
    fae = Fae()

    try:
        with allure.step("Get mgmt port ip addresses"):
            mgmt_port = MgmtPort('eth0')
            mgmt_ip_dict = get_mgmt_port_ip_addresses(mgmt_port, engines_dut)

        with allure.step("Disable ufm-mad feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True).verify_result()

        with allure.step("Update mgmt port ipv6 address (static ip)"):
            mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV6, apply=True,
                                               ask_for_confirmation=True).verify_result()

        # Connection in SSH is lost, continue in serial port
        with allure.step("Validate ufm-mad state disabled and IP address is empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.DISABLED.value)

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engine=serial_engine, state=UfmMadConsts.State.DISABLED.value)

        with allure.step("Enable feature"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                               apply=True, dut_engine=serial_engine).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        with allure.step("Validate ufm-mad state enabled and IP static address is configured"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         ipv6=UfmMadConsts.STATIC_IPV6)

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(serial_engine, UfmMadConsts.State.ENABLED.value, ipv6=UfmMadConsts.STATIC_IPV6)

        with allure.step("Update mgmt port ipv6 address when ufm-mad state is enabled"):
            mgmt_port.interface.ip.address.unset(dut_engine=serial_engine, apply=True).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        # Connection in SSH is back, continue in engines.dut
        with allure.step("Validate ufm-mad state enabled and IP address is configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engines_dut, UfmMadConsts.State.ENABLED.value,
                                    mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Delete mgmt port ipv6 address (set ip 0:0:0:0:0:0:0:0/0)"):
            mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.ZEROS_IPV6, apply=True,
                                               ask_for_confirmation=True).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        # Connection in SSH is lost, continue in serial port
        with allure.step("Validate ufm-mad state disabled and both IPV4 and IPV6 addresses are empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         ipv6=mgmt_ip_dict[UfmMadConsts.IPV6_SLAAC])

        with allure.step("Verify State DB:UFM-MAD value"):
            verify_ufm_mad_db_table(engine=serial_engine, state=UfmMadConsts.State.ENABLED.value,
                                    ipv6=mgmt_ip_dict[UfmMadConsts.IPV6_SLAAC])

    finally:
        with allure.step("Set to default mgmt port address and ufm-mad feature state"):
            mgmt_port.interface.ip.address.unset(dut_engine=serial_engine).verify_result()
            fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True, dut_engine=serial_engine).verify_result()


@pytest.mark.interface
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_configure_mgmt_port_link_state(engines, topology_obj, prepare_traffic, test_api):
    """
    Validate configuring management port link state in several cases

    Test flow:

    1. Disable ufm-mad feature when link state is up
    2. Validate ufm-mad state disabled and IP address is empty
    3. Enable ufm-mad feature when link state is up
    4. Validate ufm-mad state enabled and IP addresses are configured
    5. Set mgmt port link state to down
    6. Disable ufm-mad feature when link state is down
    7. Validate ufm-mad state disabled and IP addressed are empty
    8. Enable ufm-mad feature when link state is down
    9. Validate ufm-mad state enabled and IP addressed are empty
    10. Set to default mgmt port address and ufm-mad feature state
    """
    TestToolkit.tested_api = test_api
    engines_dut = engines.dut
    engines_ha = engines.ha
    serial_engine = topology_obj.players['dut_serial']['engine']
    fae = Fae()

    try:
        with allure.step("Get mgmt port ip addresses"):
            mgmt_port = MgmtPort('eth0')
            mgmt_ip_dict = get_mgmt_port_ip_addresses(mgmt_port, engines_dut)

        with allure.step("Disable ufm-mad feature when link state is up"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True).verify_result()

        with allure.step("Validate ufm-mad state disabled and IP address is empty"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.DISABLED.value)

        with allure.step("Enable ufm-mad feature when link state is up"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                               apply=True).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)

        with allure.step("Validate ufm-mad state enabled and IP addresses are configured"):
            verify_ufm_mad_configuration(fae, engines_dut, engines_ha, UfmMadConsts.State.ENABLED.value,
                                         mgmt_ip_dict[UfmMadConsts.IPV4], mgmt_ip_dict[UfmMadConsts.IPV6])

        with allure.step("Set mgmt port link state to down"):
            mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                               ask_for_confirmation=True).verify_result()

        # Connection in SSH is lost, continue in serial port
        with allure.step("Disable ufm-mad feature when link state is down"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                               apply=True, dut_engine=serial_engine).verify_result()

        with allure.step("Validate ufm-mad state disabled and IP addressed are empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.DISABLED.value)

        with allure.step("Enable ufm-mad feature when link state is down"):
            fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                               apply=True, dut_engine=serial_engine).verify_result()

        with allure.step("Validate ufm-mad state enabled and IP addressed are empty"):
            verify_ufm_mad_configuration(fae, serial_engine, engines_ha, UfmMadConsts.State.ENABLED.value)

    finally:
        with allure.step("Set mgmt port link state to up and enable ufm-mad feature state"):
            mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, ask_for_confirmation=True,
                                               apply=True, dut_engine=serial_engine).verify_result()
            time.sleep(UfmMadConsts.CONFIG_TIME)
            fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True, dut_engine=serial_engine).verify_result()


@pytest.mark.interfacel
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_fae_invalid_commands(test_api):
    """
    Check set fae command with invalid param value.

    Test flow:
    1. nv set fae ib ufm-mad <invalid state>
    """

    TestToolkit.tested_api = test_api

    with allure.step("Validate set fae interface link lanes with invalid lanes"):
        Fae().ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value='invalid_state',
                             apply=True).verify_result(should_succeed=False)


# ----------------------------------------------------------------------------------------------------
# test_interface_shutdown and test_dhcp_shutdown will be enabled when we have system with 2 mgmt ports
# ----------------------------------------------------------------------------------------------------

@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_interface_shutdown(engines, prepare_traffic, test_api):
    """
    Distinguish between 2 types of systems:
    1. One mgmt. port system (eth0)
    2. Two mgmt. ports system (eth0 and eth1)
    The test will shutdown mgmt. interface eth0 and then in case of:
    1 mgmt port – UFM MAD ip should return zeros.
    2 mgmt ports – UFM MAD ip should return eth1 configured ip.
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort('eth0')
    fae = Fae()
    two_mgmt_ports = False

    with allure.step("Verify number of mgmt ports"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        two_mgmt_ports = True if UfmMadConsts.MGMT_PORT1 in ufm_mad_show else False

    with allure.step("Shutdown eth0 mgmt port"):
        mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        if two_mgmt_ports:
            assert True  # TODO Verify first mgmt port is eth1
        else:
            assert True  # TODO Verify eth0 is down (no eth1)

    with allure.step("Activate eth0 mgmt port"):
        mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        # TODO Verify first mgmt port is eth0
        if two_mgmt_ports:
            assert True  # TODO Verify second mgmt port is eth1


@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_dhcp_shutdown(engines, prepare_traffic, test_api):
    """
    Distinguish between 2 types of systems:
    1. One mgmt. port system (eth0)
    2. Two mgmt. ports system (eth0 and eth1)
    The test will shutdown mgmt. dhcp eth0 and then in case of:
    1 mgmt port – UFM MAD ip should return zeros.
    2 mgmt ports – UFM MAD ip should return eth1 configured ip.
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort('eth0')
    fae = Fae()
    two_mgmt_ports = False

    with allure.step("Verify number of mgmt ports"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        two_mgmt_ports = True if UfmMadConsts.MGMT_PORT1 in ufm_mad_show else False

    with allure.step("Shutdown eth0 dhcp"):
        mgmt_port.interface.ip.dhcp_client.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                               ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        if two_mgmt_ports:
            assert True  # TODO Verify first mgmt port is eth1
        else:
            assert True  # TODO Verify eth0 is down (no eth1)

    with allure.step("Activate eth0 dhcp"):
        mgmt_port.interface.ip.dhcp_client.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True,
                                               ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        # TODO Verify first mgmt port is eth0
        if two_mgmt_ports:
            assert True  # TODO Verify second mgmt port is eth1

# ----------------------------------------------


def get_mgmt_port_ip_addresses(mgmt_port, dut_engine):
    with allure.step("Get mgmt port ip addresses"):
        ip_addresses_show = list(OutputParsingTool.parse_json_str_to_dictionary(
            mgmt_port.interface.ip.address.show(dut_engine=dut_engine)).get_returned_value())

    ip_address = {}
    ip_address.update({UfmMadConsts.IPV4: ip_addresses_show[0]})
    if len(ip_addresses_show[2]) > len(ip_addresses_show[1]):
        ip_address.update({UfmMadConsts.IPV6: ip_addresses_show[1]})
        ip_address.update({UfmMadConsts.IPV6_SLAAC: ip_addresses_show[2]})
    else:
        ip_address.update({UfmMadConsts.IPV6: ip_addresses_show[2]})
        ip_address.update({UfmMadConsts.IPV6_SLAAC: ip_addresses_show[1]})

    return ip_address


def verify_ufm_mad_configuration(fae, dut_engine, engines_ha, state, ipv4='', ipv6=''):
    with allure.step("Validate ufm-mad state in show command"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(
            fae.ib.ufm_mad.show(dut_engine=dut_engine)).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == state, f"Ufm-Mad state should be {state}"
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(
            fae.ib.ufm_mad.show(UfmMadConsts.ADVERTISED_ADDRESSED, dut_engine=dut_engine)).get_returned_value()

    with allure.step("Run MAD request from traffic server"):
        output = IpTool.send_ufm_mad(engines_ha, UfmMadConsts.NVMAD_PATH, UfmMadConsts.LID).get_returned_value()
        mads_response = IpTool.parse_mad_output(output)
        ipv4_res = mads_response[IpConsts.IPV4]
        ipv6_res = mads_response[IpConsts.IPV6]

    with allure.step("Get MAD from IBSNI register"):
        output = RegisterTool.get_mst_register_value(dut_engine, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.IBSNI_REGISTER)
        ibsni_response = parse_ibsni_register(output)
        ipv4_reg = ibsni_response[IpConsts.IPV4]
        ipv6_reg = ibsni_response[IpConsts.IPV6]

    with allure.step("Verify ip addresses via: show command, MAD request from traffic server, and IBSNI register"):
        if ipv4:
            assert ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV4_PREFIX] == ipv4, \
                f"ipv4 should be {ipv4}, but it is {ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV4_PREFIX]}"
            assert ipv4_res == ipv4.split('/')[0], f"ufm mad ipv4 response is: {ipv4_res}, " \
                                                   f"but expected: {ipv4.split('/')[0]}"
            assert ipv4_reg == ipv4.split('/')[0], f"IBSNI ipv4 response is: {ipv4_reg}, " \
                                                   f"but expected: {ipv4.split('/')[0]}"
        else:
            assert UfmMadConsts.IPV4_PREFIX not in ufm_mad_show[UfmMadConsts.MGMT_PORT0].keys(), \
                f"{UfmMadConsts.IPV4_PREFIX} should be empty, but it is: " \
                f"{ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV4_PREFIX]}"
            assert ipv4_res == UfmMadConsts.MAD_NO_IPV4, f"ufm mad ipv4 response is: {ipv4_res}, " \
                                                         f"but expected: {UfmMadConsts.MAD_NO_IPV4}"
            assert ipv4_reg == UfmMadConsts.MAD_NO_IPV4, f"IBSNI ipv4 response is: {ipv4_reg}, " \
                                                         f"but expected: {UfmMadConsts.MAD_NO_IPV4}"
        if ipv6:
            assert ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV6_PREFIX] == ipv6, \
                f"ipv6 should be {ipv6}, but it is {ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV6_PREFIX]}"
            assert ipv6_res == ipv6.split('/')[0], f"ufm mad ipv6 response is: {ipv6_res}, " \
                                                   f"but expected: {ipv6.split('/')[0]}"
            assert ipv6_reg == ipv6.split('/')[0], f"IBSNI ipv6 response is: {ipv6_reg}, " \
                                                   f"but expected: {ipv6.split('/')[0]}"
        else:
            assert UfmMadConsts.IPV6_PREFIX not in ufm_mad_show[UfmMadConsts.MGMT_PORT0].keys(), \
                f"{UfmMadConsts.IPV6_PREFIX} should be empty, but it is: " \
                f"{ufm_mad_show[UfmMadConsts.MGMT_PORT0][UfmMadConsts.IPV6_PREFIX]}"
            assert ipv6_res == UfmMadConsts.MAD_NO_IPV6, f"ufm mad ipv6 response is: {ipv6_res}, " \
                                                         f"but expected: {UfmMadConsts.MAD_NO_IPV6}"
            assert ipv6_reg == UfmMadConsts.MAD_NO_IPV6, f"IBSNI ipv6 response is: {ipv6_reg}, " \
                                                         f"but expected: {UfmMadConsts.MAD_NO_IPV6}"


def verify_ufm_mad_db_table(engine, state, ipv4='', ipv6=''):
    table_eth0 = DatabaseTool.sonic_db_cli_hgetall(engine=engine, asic="", db_name=DatabaseConst.STATE_DB_NAME,
                                                   table_name=UfmMadConsts.UFM_MAD_TABLE_ETH0)
    table_general = DatabaseTool.sonic_db_cli_hgetall(engine=engine, asic="", db_name=DatabaseConst.STATE_DB_NAME,
                                                      table_name=UfmMadConsts.UFM_MAD_TABLE_GENERAL)
    reg_state = table_general.split(': ')[1].replace("'", "").replace("}", "")
    ValidationTool.compare_values(reg_state, state)
    if ipv4:
        reg_ipv4 = table_eth0.split(',')[0].split(': ')[1].replace("'", "")
        ValidationTool.compare_values(reg_ipv4, ipv4)
    if ipv6:
        reg_ipv6 = table_eth0.split(',')[1].split(': ')[1].replace("'", "").replace("}", "")
        ValidationTool.compare_values(reg_ipv6, ipv6)


def parse_ibsni_register(ibsni_value):
    """
    @Summary:
        This function will parse the IBSNI register value and return a dict of the required fields.
        IPV4, IPV6 And their netmasks.
    @param ibsni_value: The IBSNI register value. for example:
        Sending access register...

        Field Name    | Data
        ===========================
        ipv4_0        | 0x0a07909a
        netmask_0     | 0xfffff800
        ipv4_1        | 0x00000000
        netmask_1     | 0x00000000
        ipv4_2        | 0x00000000
        netmask_2     | 0x00000000
        ipv4_3        | 0x00000000
        netmask_3     | 0x00000000
        ipv6[0]       | 0xfdfdfdfd
        ipv6[1]       | 0x00070145
        ipv6[2]       | 0x00000000
        ipv6[3]       | 0x1000484c
        netmask[0]    | 0xffffffff
        netmask[1]    | 0xffffffff
        netmask[2]    | 0xffffffff
        netmask[3]    | 0xffffffff
        ipv6[0]       | 0x00000000
        ipv6[1]       | 0x00000000
        ipv6[2]       | 0x00000000
        ipv6[3]       | 0x00000000
        netmask[0]    | 0x00000000
        netmask[1]    | 0x00000000
        netmask[2]    | 0x00000000
        netmask[3]    | 0x00000000
        ipv6[0]       | 0x00000000
        ipv6[1]       | 0x00000000
        ipv6[2]       | 0x00000000
        ipv6[3]       | 0x00000000
        netmask[0]    | 0x00000000
        netmask[1]    | 0x00000000
        netmask[2]    | 0x00000000
        netmask[3]    | 0x00000000
        ipv6[0]       | 0x00000000
        ipv6[1]       | 0x00000000
        ipv6[2]       | 0x00000000
        ipv6[3]       | 0x00000000
        netmask[0]    | 0x00000000
        netmask[1]    | 0x00000000
        netmask[2]    | 0x00000000
        netmask[3]    | 0x00000000
        ===========================
    @return: Dict:
        {'ipv4': '10.7.144.154',
        'ipv4_netmask': '255.255.248.0',
        'ipv6': 'fdfd:fdfd:7:145::1000:484c',
        'ipv6_netmask': 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'}
    """
    mad_output_list = ibsni_value.split('\n')
    ips_dict = {}
    ipv6 = '0x'
    ipv6_netmask = '0x'
    for out in mad_output_list:
        if UfmMadConsts.IPV4_PREF in out:
            out = out.split("|")[-1]
            ips_dict[UfmMadConsts.IPV4] = IpTool.hex_to_ipv4(out)
        elif UfmMadConsts.IPV4_NETMASK_PREF in out:
            out = out.split("|")[-1]
            ips_dict[UfmMadConsts.IPV4_NETMASK] = IpTool.hex_to_ipv4(out)
        elif UfmMadConsts.IPV6 in out:
            out1 = out.split("|")[-1]
            ipv6 += out1.split("x")[-1]
            if UfmMadConsts.LAST_IP_INDEX in out:
                ips_dict[UfmMadConsts.IPV6] = IpTool.hex_to_ipv6(ipv6)
        elif UfmMadConsts.IPV6_NETMASK_PREF in out:
            out1 = out.split("|")[-1]
            ipv6_netmask += out1.split("x")[-1]
            if UfmMadConsts.LAST_IP_INDEX in out:
                ips_dict[UfmMadConsts.IPV6_NETMASK] = IpTool.hex_to_ipv6(ipv6_netmask)
        if len(ips_dict) == UfmMadConsts.NUMBER_OF_ADDRESSES_IN_MAD_RESPONSE:
            break
    return ips_dict
