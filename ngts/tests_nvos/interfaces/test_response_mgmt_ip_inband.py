import pytest

from ngts.nvos_constants.constants_nvos import ApiType, DatabaseConst, UfmMadConsts
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
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_feature_state(engines, devices, test_api):
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
    fae = Fae()

    with allure.step("Verify feature state enabled and IP address configured"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        ValidationTool.compare_nested_dictionary_content(ufm_mad_show, UfmMadConsts.UFM_MAD_DEFAULT).verify_result()

    with allure.step("Disable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                           apply=True).verify_result()

    with allure.step("Validate ufm-mad state"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.DISABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.DISABLED.value}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Enable feature (by set command)"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                           apply=True).verify_result()

    with allure.step("Validate ufm-mad state"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Disable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                           apply=True).verify_result()

    with allure.step("Enable feature (by unset command)"):
        fae.ib.ufm_mad.unset(op_param=UfmMadConsts.STATE, apply=True).verify_result()

    with allure.step("Validate ufm-mad state"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)


@pytest.mark.interface
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_mgmt_port_ipv4(engines, devices, test_api):
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
    mgmt_port = MgmtPort('eth0')
    fae = Fae()

    with allure.step("Disable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                           apply=True).verify_result()

    with allure.step("Update mgmt port ipv4 address (static ip)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV4, apply=True,
                                           ask_for_confirmation=True).verify_result()

    # TODO Connection in SSH is lost, continue in serial port
    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.DISABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.DISABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV4] == UfmMadConsts.NONE_IP, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV4]}, instead of {UfmMadConsts.NONE_IP}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)
        table_eth0 = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                       table_name=UfmMadConsts.UFM_MAD_TABLE_ETH0)
        table_general = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                          db_name=DatabaseConst.STATE_DB_NAME,
                                                          table_name=UfmMadConsts.UFM_MAD_TABLE_GENERAL)
        # TODO assert: Verify State DB:UFM-MAD value (will be completed once drop image is ready)

    with allure.step("Enable feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                           apply=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV4] == UfmMadConsts.STATIC_IPV4, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV4]}, instead of {UfmMadConsts.STATIC_IPV4}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)
        table_eth0 = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                       table_name=UfmMadConsts.UFM_MAD_TABLE_ETH0)
        table_general = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                          db_name=DatabaseConst.STATE_DB_NAME,
                                                          table_name=UfmMadConsts.UFM_MAD_TABLE_GENERAL)
        # TODO assert: Verify State DB:UFM-MAD value (will be completed once drop image is ready)

    with allure.step("Update mgmt port ipv4 address (static ip2)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV4_2, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV4] == UfmMadConsts.STATIC_IPV4_2, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV4]}, instead of {UfmMadConsts.STATIC_IPV4_2}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)
        table_eth0 = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                       table_name=UfmMadConsts.UFM_MAD_TABLE_ETH0)
        table_general = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                          db_name=DatabaseConst.STATE_DB_NAME,
                                                          table_name=UfmMadConsts.UFM_MAD_TABLE_GENERAL)
        # TODO assert: Verify State DB:UFM-MAD value (will be completed once drop image is ready)

    with allure.step("Delete mgmt port ipv4 address (0.0.0.0)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.NONE_IP, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV4] == UfmMadConsts.NONE_IP, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV4]}, instead of {UfmMadConsts.NONE_IP}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)
        table_eth0 = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                       table_name=UfmMadConsts.UFM_MAD_TABLE_ETH0)
        table_general = DatabaseTool.sonic_db_cli_hgetall(engine=engines.dut, asic="",
                                                          db_name=DatabaseConst.STATE_DB_NAME,
                                                          table_name=UfmMadConsts.UFM_MAD_TABLE_GENERAL)
        # TODO assert: Verify State DB:UFM-MAD value (will be completed once drop image is ready)

    with allure.step("Set to default mgmt port ipv4 address"):
        mgmt_port.interface.ip.address.unset(apply=True).verify_result()


@pytest.mark.interface
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_mgmt_port_ipv6(engines, devices, test_api):
    """
    Validate configuring management port ipv4 address in several cases

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
    mgmt_port = MgmtPort('eth0')
    fae = Fae()

    with allure.step("Disable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                           apply=True).verify_result()

    with allure.step("Update mgmt port ipv6 address (static ip)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV6, apply=True,
                                           ask_for_confirmation=True).verify_result()

    # TODO Connection in SSH is lost, continue in serial port
    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.DISABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.DISABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV6] == UfmMadConsts.NONE_IP, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV6]}, instead of {UfmMadConsts.NONE_IP}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Enable feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                           apply=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV6] == UfmMadConsts.STATIC_IPV6, \
            f"Ufm-Mad ipv6 is {ufm_mad_show[UfmMadConsts.IPV6]}, instead of {UfmMadConsts.STATIC_IPV6}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Update mgmt port ipv6 address (static ip2)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.STATIC_IPV6_2, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV6] == UfmMadConsts.STATIC_IPV6_2, \
            f"Ufm-Mad ipv4 is {ufm_mad_show[UfmMadConsts.IPV6]}, instead of {UfmMadConsts.STATIC_IPV6_2}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Delete mgmt port ipv6 address (0.0.0.0)"):
        mgmt_port.interface.ip.address.set(op_param_name=UfmMadConsts.NONE_IP, apply=True,
                                           ask_for_confirmation=True).verify_result()

    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.IPV6] == UfmMadConsts.NONE_IP, \
            f"Ufm-Mad ipv6 is {ufm_mad_show[UfmMadConsts.IPV6]}, instead of {UfmMadConsts.NONE_IP}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Set to default mgmt port ipv4 address"):
        mgmt_port.interface.ip.address.unset(apply=True).verify_result()


@pytest.mark.interface
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_mgmt_port_link_state(engines, devices, test_api):
    """
    Validate configuring management port link state in several cases

    Test flow:
    1. Disable feature
    2. Disable mgmt port link state
    3. Validate ufm-mad
    4. Enable feature (by set)
    5. Enable mgmt port link state
    6. Validate ufm-mad
    """
    TestToolkit.tested_api = test_api
    mgmt_port = MgmtPort('eth0')
    fae = Fae()

    with allure.step("Disable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.DISABLED.value,
                           apply=True).verify_result()

    with allure.step("Disable mgmt port link state"):
        mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_DOWN, apply=True,
                                           ask_for_confirmation=True).verify_result()

    # TODO Connection in SSH is lost, continue in serial port
    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.DISABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.DISABLED.value}"
        assert ufm_mad_show[UfmMadConsts.LINK_STATE] == NvosConsts.LINK_STATE_DOWN, \
            f"Ufm-Mad link state is {ufm_mad_show[UfmMadConsts.LINK_STATE]}, instead of {NvosConsts.LINK_STATE_DOWN}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)

    with allure.step("Enable ufm-mad feature"):
        fae.ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value=UfmMadConsts.State.ENABLED.value,
                           apply=True).verify_result()

    with allure.step("Enable mgmt port link state"):
        mgmt_port.interface.link.state.set(op_param_name=NvosConsts.LINK_STATE_UP, apply=True,
                                           ask_for_confirmation=True).verify_result()

    # TODO Connection in SSH is lost, continue in serial port
    with allure.step("Validate ufm-mad"):
        ufm_mad_show = OutputParsingTool.parse_json_str_to_dictionary(fae.ib.ufm_mad.show()).get_returned_value()
        assert ufm_mad_show[UfmMadConsts.STATE] == UfmMadConsts.State.ENABLED.value, \
            f"Ufm-Mad state should be {UfmMadConsts.State.ENABLED.value}"
        assert ufm_mad_show[UfmMadConsts.LINK_STATE] == NvosConsts.LINK_STATE_UP, \
            f"Ufm-Mad link state is {ufm_mad_show[UfmMadConsts.LINK_STATE]}, instead of {NvosConsts.LINK_STATE_UP}"

        reg_val = RegisterTool.get_mst_register_value(engines.dut, UfmMadConsts.MST_DEV_NAME, UfmMadConsts.MST_REGISTER)
        # TODO assert Verify IBSNI register (will be completed once drop image is ready)
        ufm_mad = IpTool.send_ufm_mad(directory=UfmMadConsts.LOCATION_TO_RUN_NVMAD)
        # TODO assert: Verify MAD request from traffic server (will be completed once drop image is ready)


@pytest.mark.interface
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_interface_shutdown(engines, devices, test_api):
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
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_dhcp_shutdown(engines, devices, test_api):
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


@pytest.mark.interface
@pytest.mark.simx
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_fae_invalid_commands(engines, devices, test_api):
    """
    Check set fae command with invalid param value.

    Test flow:
    1. nv set fae ib ufm-mad <invalid state>
    """

    TestToolkit.tested_api = test_api

    with allure.step("Validate set fae interface link lanes with invalid lanes"):
        Fae().ib.ufm_mad.set(op_param_name=UfmMadConsts.STATE, op_param_value='invalid_state',
                             apply=True).verify_result(should_succeed=False)

# ----------------------------------------------
