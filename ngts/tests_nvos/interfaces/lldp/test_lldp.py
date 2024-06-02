import time

import pytest

from ngts.nvos_constants.constants_nvos import SystemConsts, NvosConst
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.LLDPTool import LLDPTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.lldp
@pytest.mark.system
def test_lldp_enabled(engines, devices):
    """
    Verify lldp functionality is working by default.

    1. Verify lldp is running.
    2. Verify lldp is sending and receiving frames.
    """
    system = System()
    lldp = system.lldp
    _verify_lldp_running(lldp=lldp, engine=engines.dut, device=devices.dut)


@pytest.mark.lldp
@pytest.mark.system
def test_lldp_disabled(engines, devices):
    """
    Check that lldp is disabled correctly.

    1. Verify lldp is running.
    2. Disable lldp state.
    3. Verify lldp is not running and not sending any frames.
    4. Verify neighbors table is empty
    5. Enable back lldp and verify it is working.
    """
    system = System()
    lldp = system.lldp

    _verify_lldp_running(lldp, engine=engines.dut, device=devices.dut)

    try:
        _set_lldp_state(lldp, state=NvosConst.DISABLED)
        _verify_lldp_not_running(lldp, engine=engines.dut, device=devices.dut)

    finally:
        _set_lldp_state(lldp, state=NvosConst.ENABLED)
        _verify_lldp_running(lldp, engine=engines.dut, device=devices.dut)


def _set_lldp_state(lldp, state):
    with allure.step(f"Set lldp state to {state}"):
        lldp.set(SystemConsts.LLDP_STATE, state, apply=True).verify_result()
        time.sleep(10)  # It takes time for is_running to change


def test_lldp_per_port(engines, devices):
    pass


def _verify_lldp_running(lldp, engine, device):
    with allure.step("Verify lldp is running and enabled"):
        cli_output = lldp.parsed_show()
        assert cli_output[SystemConsts.LLDP_IS_RUNNING] == SystemConsts.SHOW_VALUE_YES, 'The lldp is not running'
        assert cli_output[SystemConsts.LLDP_STATE] == NvosConst.ENABLED, 'The lldp is not enabled'

    with allure.step("Verify lldp frames are being sent for each active mgmt interface"):
        output = LLDPTool.get_lldp_frames(engine=engine, interval=cli_output[SystemConsts.LLDP_INTERVAL])
        for interface_name in device.mgmt_interfaces:
            assert interface_name in output, f"The data for {interface_name} not found in lldp frames"

            mgmt_interface = MgmtPort(name=interface_name)
            output_dict = OutputParsingTool.parse_json_str_to_dictionary(
                mgmt_interface.interface.lldp.neighbor.show()).get_returned_value()
            assert output_dict, f"The neighbors output for {interface_name} is empty"


def _verify_lldp_not_running(lldp, engine, device):
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
        lldp_frames_output = LLDPTool.get_lldp_frames(engine=engine)
        assert not lldp_frames_output, "There are still lldp frames sent or received"
