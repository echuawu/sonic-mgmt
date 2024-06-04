import time

import pytest

from ngts.nvos_constants.constants_nvos import SystemConsts, NvosConst, TcpDumpConsts, ApiType
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.LLDPTool import LLDPTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_enabled(engines, devices, test_api):
    """
    Verify lldp functionality is working by default.

    1. Verify lldp is running.
    2. Verify lldp is sending and receiving frames.
    """
    TestToolkit.tested_api = test_api
    system = System()
    lldp = system.lldp
    _verify_lldp_is_sending_frames(lldp=lldp, engine=engines.dut, device=devices.dut)


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_disabled(engines, devices, test_api):
    """
    Check that lldp is disabled correctly.

    1. Verify lldp is running.
    2. Disable lldp state.
    3. Verify lldp is not running and not sending any frames.
    4. Verify neighbors table is empty
    5. Enable back lldp and verify it is working.
    """
    TestToolkit.tested_api = test_api
    system = System()
    lldp = system.lldp

    _verify_lldp_is_sending_frames(lldp, engine=engines.dut, device=devices.dut)

    try:
        _set_lldp_state(lldp, key=SystemConsts.STATE, val=NvosConst.DISABLED)
        _verify_lldp_not_running(lldp, engine=engines.dut, device=devices.dut)

    finally:
        _set_lldp_state(lldp, key=SystemConsts.STATE, val=NvosConst.ENABLED)
        _verify_lldp_is_sending_frames(lldp, engine=engines.dut, device=devices.dut)


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_with_custom_interval(engines, devices, test_api):
    """
    Check that lldp frames have correct data in them.
    1. Verify lldp is running with custom interval.
    2. Verify lldp information is the same as in tcpdump.
    """
    TestToolkit.tested_api = test_api

    system = System()
    lldp = system.lldp
    cli_output = lldp.parsed_show()
    default_interval = cli_output[SystemConsts.LLDP_INTERVAL]

    _verify_lldp_running(lldp, engine=engines.dut)

    interval = 5

    try:
        system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
        _set_lldp_state(lldp, SystemConsts.LLDP_INTERVAL, interval)

        _verify_cli_output_with_dump_output(engines.dut, devices.dut, lldp, system_output)
    finally:
        _set_lldp_state(lldp, SystemConsts.LLDP_INTERVAL, default_interval)


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_custom_hostname(engines, devices, test_api):
    """
    Check that lldp frames have correct custom hostname.
    1. Verify lldp is running.
    2. Change default hostname to custom.
    3. Verify lldp is sending correct hostname.
    4. Change hostname back to default.
    """
    TestToolkit.tested_api = test_api
    system = System()
    _verify_lldp_running(system.lldp, engine=engines.dut)

    custom_hostname = "lldp-host"
    with allure.step("Get current system hostname"):
        system_dict = OutputParsingTool.parse_json_str_to_dictionary(
            system.show()).get_returned_value()
        default_hostname = system_dict[SystemConsts.HOSTNAME]
    try:
        system.set(SystemConsts.HOSTNAME, custom_hostname, apply=True, ask_for_confirmation=True).verify_result()
        with allure.step("Verify hostname in tcpdump"):
            lldp_dump = LLDPTool.get_lldp_frames(engine=engines.dut)
            lldp_dict = LLDPTool.parse_lldp_dump(lldp_dump)
            assert lldp_dict[
                TcpDumpConsts.LLDP_SYSTEM_NAME] == custom_hostname, f'The lldp {lldp_dict[TcpDumpConsts.LLDP_SYSTEM_NAME]} is not {custom_hostname}'
    finally:
        system.set(SystemConsts.HOSTNAME, default_hostname, apply=True, ask_for_confirmation=True).verify_result()


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_one_neighbor(engines, devices, test_api):
    """
    Check that interfaces have only one lldp neighbor.
    1. Verify lldp is running.
    2. For each mgmt interface verify it has only one neighbor.
    3. Verify neighbor's output is not empty
    """
    TestToolkit.tested_api = test_api
    system = System()
    _verify_lldp_running(system.lldp, engine=engines.dut)

    for interface_name in devices.dut.mgmt_interfaces:
        with allure.step(f"Verify {interface_name} has only one neighbor"):
            mgmt_interface = MgmtPort(name=interface_name)
            output_dict = OutputParsingTool.parse_json_str_to_dictionary(
                mgmt_interface.interface.lldp.neighbor.show()).get_returned_value()
            neighbor_keys = list(output_dict.keys())
            assert len(neighbor_keys) == 1, "There is not only one neighbor"
        neighbor_id = neighbor_keys[0]

        with allure.step(f"Verify neighbor {neighbor_id} is not empty for {interface_name}"):
            neighbor_dict = OutputParsingTool.parse_json_str_to_dictionary(
                mgmt_interface.interface.lldp.neighbor.show_neighbor_id(engine=engines.dut,
                                                                        neighbor_id=neighbor_id)).get_returned_value()
            assert neighbor_dict, f"The neighbor {neighbor_id} is empty"


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_incorrect_values(engines, devices, test_api):
    """
    Check that lldp set commands are not working for values outside the range.
    1. Verify lldp is running.
    2. Try to set incorrect interval.
    3. Try to set incorrect multiplier.
    """
    TestToolkit.tested_api = test_api
    system = System()
    lldp = system.lldp

    _verify_lldp_running(lldp, engine=engines.dut)
    wrong_interval = 32769
    wrong_multiplier = 8193

    with allure.step(f"Verify can't set interval to {wrong_interval}"):
        lldp.set(SystemConsts.LLDP_INTERVAL, wrong_interval).verify_result(should_succeed=False)
    with allure.step(f"Verify can't set hold-multiplier to {wrong_multiplier}"):
        lldp.set(SystemConsts.LLDP_MULTIPLIER, wrong_multiplier).verify_result(should_succeed=False)


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_lldp_max_values(engines, devices, test_api):
    """
    Check that lldp set commands are working with max values
    1. Verify lldp is running.
    2. Set max interval and multiplier.
    3. Verify ttl.
    """

    pytest.skip("Currently has a bug opened")  # TODO: Need to update with new ranges and test ttl

    TestToolkit.tested_api = test_api
    system = System()
    lldp = system.lldp

    _verify_lldp_running(lldp, engine=engines.dut)
    max_interval = 32768
    max_multiplier = 8192

    with allure.step(f"Verify lldp works with interval {max_interval}"):
        _set_lldp_state(lldp, SystemConsts.LLDP_INTERVAL, max_interval)
    with allure.step(f"Verify lldp works with interval {max_multiplier}"):
        _set_lldp_state(lldp, SystemConsts.LLDP_MULTIPLIER, max_multiplier)

    # TODO: TEST TTL with enabling/disabling lldp


def test_lldp_additional_ipv6(engines, devices):
    """
    Check that correct lldp frames sent all IpV6 addresses.
    1. Verify lldp is running.
    2. Add additional IpV6 address.
    3. Verify lldp frames contain this new IpV6 address.
    """
    pass


@pytest.mark.lldp
@pytest.mark.system
@pytest.mark.interface
def test_lldp_interface_flapping(engines, devices):
    """
    Check that correct lldp frames are sent after interface flapping
    1. Verify lldp is running.
    2. Do interface flapping for each of mgmt ports.
    3. Verify lldp frames are sent and valid.
    """
    pytest.skip("Need to check why connection is not dropped.")

    system = System()
    lldp = system.lldp
    _verify_lldp_running(lldp, engine=engines.dut)

    mgmt_ports = [MgmtPort(name=interface_name) for interface_name in devices.dut.mgmt_interfaces]
    engine = engines.dut

    for _ in range(4):
        for mgmt_port in mgmt_ports:
            mgmt_port.interface.link.set(SystemConsts.STATE, NvosConst.PORT_STATUS_DOWN).verify_result()

        engine.run_cmd("nv config apply -y")

        for mgmt_port in mgmt_ports:
            mgmt_port.interface.link.set(SystemConsts.STATE, NvosConst.PORT_STATUS_UP).verify_result()

        engine.run_cmd("nv config apply -y")

    _verify_lldp_is_sending_frames(lldp=lldp, engine=engine, device=devices.dut)


def test_lldp_disable_dhcp(engines, devices):
    """
    Check that correct lldp sends mac address if dhcp is disabled.
    1. Verify lldp is running.
    2. Disable dhcp client
    3. Verify lldp frames do not contain ip addresses and hostnames.
    4. Verify lldp frames contain mac address.
    """
    pass


def _verify_cli_output_with_dump_output(engine, device, lldp, system_output):
    cli_output = lldp.parsed_show()
    for interface_name in device.mgmt_interfaces:
        with allure.step(f"Get and parse tcp dump for {interface_name}"):
            lldp_dump = LLDPTool.get_lldp_frames(engine=engine, interface=interface_name)
            lldp_dict = LLDPTool.parse_lldp_dump(lldp_dump)
            ttl = int(cli_output[SystemConsts.LLDP_INTERVAL]) * int(cli_output[SystemConsts.LLDP_MULTIPLIER])
            assert lldp_dict[
                TcpDumpConsts.LLDP_PORT_ID] == interface_name, f'The {interface_name} name does not match lldp frame port id'
            assert int(
                lldp_dict[
                    TcpDumpConsts.LLDP_TIME_TO_LIVE]) == ttl, 'The cli ttl does not match sent frame time to live'
            assert lldp_dict[TcpDumpConsts.LLDP_SYSTEM_NAME] == system_output[
                SystemConsts.HOSTNAME], "The hostname do not match"


def _verify_lldp_running(lldp, engine):
    with allure.step("Verify lldp container is running"):
        lldp_running = engine.run_cmd('docker inspect --format \'{{.State.Running}}\' lldp')
        assert lldp_running == 'true', 'The lldp docker container is down'
    with allure.step("Verify lldp is running and enabled"):
        cli_output = lldp.parsed_show()
        assert cli_output[SystemConsts.LLDP_IS_RUNNING] == SystemConsts.SHOW_VALUE_YES, 'The lldp is not running'
        assert cli_output[SystemConsts.LLDP_STATE] == NvosConst.ENABLED, 'The lldp is not enabled'


def _verify_lldp_is_sending_frames(lldp, engine, device):
    _verify_lldp_running(lldp, engine)
    cli_output = lldp.parsed_show()

    with allure.step("Verify lldp frames are being sent for each active mgmt interface"):
        interval = int(cli_output[SystemConsts.LLDP_INTERVAL])
        for interface_name in device.mgmt_interfaces:
            output = LLDPTool.get_lldp_frames(engine=engine, interval=interval, interface=interface_name)
            assert interface_name in output, f"The data for {interface_name} not found in lldp frames"

            mgmt_interface = MgmtPort(name=interface_name)
            output_dict = OutputParsingTool.parse_json_str_to_dictionary(
                mgmt_interface.interface.lldp.neighbor.show()).get_returned_value()
            assert output_dict, f"The neighbors output for {interface_name} is empty"


def _verify_lldp_not_running(lldp, engine, device):
    with allure.step("Verify lldp container is not running"):
        lldp_running = engine.run_cmd('docker inspect --format \'{{.State.Running}}\' lldp')
        assert lldp_running == 'false', 'The lldp docker container is up'
    with allure.step("Verify lldp is not running and not enabled"):
        cli_output = lldp.parsed_show()
        assert cli_output[SystemConsts.LLDP_IS_RUNNING] == SystemConsts.SHOW_VALUE_NO, 'The lldp is running'
        assert cli_output[SystemConsts.LLDP_STATE] == NvosConst.DISABLED, 'The lldp is enabled'

    with allure.step("Verify lldp frames are not being sent for each active mgmt interface"):
        for interface_name in device.mgmt_interfaces:
            mgmt_interface = MgmtPort(name=interface_name)
            output_dict = OutputParsingTool.parse_json_str_to_dictionary(
                mgmt_interface.interface.lldp.neighbor.show()).get_returned_value()
            assert not output_dict, f"The neighbors output for {interface_name} is not empty"

            with allure.step(f"Verify that no lldp frames are sent"):
                lldp_frames_output = LLDPTool.get_lldp_frames(engine=engine, interface=interface_name)
                assert not lldp_frames_output, f"There are still lldp frames sent for {interface_name}"


def _set_lldp_state(lldp, key, val):
    with allure.step(f"Set lldp {key} to {val}"):
        lldp.set(key, val, apply=True).verify_result()
        time.sleep(10)  # It takes time for is_running to change
