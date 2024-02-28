import pytest

from ngts.nvos_constants.constants_nvos import ApiType, PtpConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RegisterTool import RegisterTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.system
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_configure_ptp_state(engines, devices, test_api):
    """
    Validate configuring feature state by using the fae commands:
    - Validate show system ptp command
    - Validate set system ptp tc <enabled|disabled> command
    - Validate unset system ptp tc command

    Test flow:
    1. Verify unset system ptp command
    2. Verify set system ptp tc enabled command
    3. Verify set system ptp tc disabled command
    4. Verify set system ptp tc enabled command
    5. Verify unset system ptp command
    6. Verify tc-state persist disabled after reboot
    """
    TestToolkit.tested_api = test_api
    engines_dut = engines.dut
    system = System()

    try:
        with allure.step("Verify unset system ptp command"):
            system.ptp.unset(apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                "stats state parameter is enabled, but expected to be 'disabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                    "mtpcpc state parameter is enabled, but expected to be 'disabled'"

        with allure.step("Verify set system ptp tc enabled command"):
            system.stats.set(op_param_name=PtpConsts.TC_STATE, op_param_value=PtpConsts.TcState.ENABLED.value,
                             apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.ENABLED.value, \
                "stats state parameter is disabled, but expected to be 'enabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.ENABLED.value, \
                    "mtpcpc state parameter is disabled, but expected to be 'enabled'"

        with allure.step("Verify set system ptp tc disabled command"):
            system.stats.set(op_param_name=PtpConsts.TC_STATE, op_param_value=PtpConsts.TcState.DISABLED.value,
                             apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                "stats state parameter is enabled, but expected to be 'disabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                    "mtpcpc state parameter is enabled, but expected to be 'disabled'"

        with allure.step("Verify set system ptp tc enabled command"):
            system.stats.set(op_param_name=PtpConsts.TC_STATE, op_param_value=PtpConsts.TcState.ENABLED.value,
                             apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.ENABLED.value, \
                "stats state parameter is disabled, but expected to be 'enabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.ENABLED.value, \
                    "mtpcpc state parameter is disabled, but expected to be 'enabled'"

        with allure.step("Verify unset system ptp command"):
            system.ptp.unset(apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                "stats state parameter is enabled, but expected to be 'disabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                    "mtpcpc state parameter is enabled, but expected to be 'disabled'"

        with allure.step("Verify tc-state persist disabled after reboot"):
            with allure.step("Perform system reboot"):
                system.reboot.action_reboot(params='force').verify_result()

            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.ptp.show()).get_returned_value()
            assert stats_show[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                "stats state parameter is enabled, but expected to be 'disabled'"

            with allure.step("Get tc-state from MTPCPC register"):
                output = RegisterTool.get_mst_register_value(engines_dut, devices.dut.mst_dev_name,
                                                             PtpConsts.MTPCPC_REGISTER)
                mtpcpc_response = parse_mtpcpc_register(output)
                assert mtpcpc_response[PtpConsts.TC_STATE] == PtpConsts.TcState.DISABLED.value, \
                    "mtpcpc state parameter is enabled, but expected to be 'disabled'"

    finally:
        with allure.step("Set ptp tc-state to default"):
            system.ptp.unset(apply=True).verify_result()


@pytest.mark.system
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_set_ptp_invalid_commands(test_api):
    """
    Check set ptp command with invalid param value.

    Test flow:
    1. nv set system ptp tc <invalid state>
    """

    TestToolkit.tested_api = test_api

    with allure.step("Validate set fae interface link lanes with invalid lanes"):
        System().ptp.set(op_param_name=PtpConsts.TC_STATE, op_param_value='invalid_state',
                         apply=True).verify_result(should_succeed=False)


def parse_mtpcpc_register(mtpcpc_value):
    """
    @Summary:
        TODO update summary
    @param mtpcpc_value: The mtpcpc register value. for example:
        TODO update summary
    @return: Dict:
        TODO update
    """
    # TODO update implementation
    output = mtpcpc_value
    return output
