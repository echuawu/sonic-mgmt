import logging
import pytest
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_constants.constants_nvos import FastRecoveryConsts
from ngts.tools.test_utils.allure_utils import step as allure_step
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.interfaces
@pytest.mark.simx
def test_show_fae_fast_recovery(engines):
    """
    Run show fae fast-recovery state command and verify the required state
        Test flow:
            1. Check show fae fast-recovery state and verify state field are available
    """

    fae = Fae()

    try:

        with allure_step('Run show fae fast-recovery state command and verify that it has default value'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                        FastRecoveryConsts.STATE_ENABLED).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_show_fae_fast_recovery_trigger(engines):
    """
    Run show fae fast-recovery trigger command and verify all fields are available
        Test flow:
            1. Check show fae fast-recovery trigger and verify all fields are available
    """

    fae = Fae()

    try:

        with allure_step('Run show fae fast-recovery trigger command and verify that each field has a value'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.trigger.show()).get_returned_value()
            ValidationTool.verify_field_exist_in_json_output(fast_recovery_output,
                                                             [FastRecoveryConsts.TRIGGER_CREDIT_WATCHDOG,
                                                              FastRecoveryConsts.TRIGGER_EFFECTIVE_BER,
                                                              FastRecoveryConsts.TRIGGER_RAW_BER,
                                                              FastRecoveryConsts.TRIGGER_SYMBOL_BER]).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_show_fae_fast_recovery_trigger_id(engines):
    """
    Run show fae fast-recovery trigger trigger_id command and verify fields are available
        Test flow:
            1. Check show fae fast-recovery trigger trigger_id and verify all fields are available
    """

    fae = Fae()

    try:
        for trigger_id in FastRecoveryConsts.TRIGGERS:
            with allure_step('Run show fae fast-recovery trigger <id> command and verify that it has a value'):
                fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                    fae.fast_recovery.trigger.show(trigger_id)).get_returned_value()
                ValidationTool.verify_field_value_in_output(fast_recovery_output,
                                                            FastRecoveryConsts.TRIGGER_EVENT,
                                                            FastRecoveryConsts.SEVERITY_DEFAULT).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_set_fast_recovery_state(engines):
    """
    Run set/unset fae fast-recovery state command and verify the required state
        Test flow:
            1. Set fae fast-recovery state to 'disabled'[run cmd + apply conf]
            2. Verify fae fast-recovery trigger state changed to 'disabled' in show command
            3. Unset fae fast-recovery state [run cmd + apply conf]
            4. Verify fae fast-recovery state changed to default('enabled') in show command
    """

    fae = Fae()

    try:
        with allure_step('Run set fae fast-recovery state command and apply config'):
            fae.fast_recovery.set(FastRecoveryConsts.STATE,
                                  FastRecoveryConsts.STATE_DISABLED, apply=True, dut_engine=engines.dut)

        with allure_step('Verify fae fast-recovery state changed to new state in show fas fast-recovery'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                        FastRecoveryConsts.STATE_DISABLED).verify_result()

        with allure_step('Run unset fae fast-recovery state command and apply config'):
            fae.fast_recovery.unset(FastRecoveryConsts.STATE, apply=True, dut_engine=engines.dut).verify_result()

        with allure_step('Verify fae fast-recovery state changed to default state in show system'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                        FastRecoveryConsts.STATE_DEFAULT).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_set_fast_recovery_trigger_id(engines):
    """
    Run set/unset fae fast-recovery trigger trigger_id command and verify the required state
        Test flow:
            1. Set fae fast-recovery trigger trigger-id event to 'warning'[run cmd + apply conf] for 'credit watchdog'
            2. Verify fae fast-recovery trigger event for 'credit-watchdog' changed to 'warning' in show command
            3. Unset fae fast-recovery trigger event for 'credit-watchdog' [run cmd + apply conf]
            4. Verify fae fast-recovery trigger event for 'credit-watchdog' changed to 'error' in show command
            5. Repeat steps 1 to 4 for other triggers : raw-ber, symbol-ber and effective-ber
    """

    fae = Fae()

    try:
        for trigger_id in FastRecoveryConsts.TRIGGERS:
            with allure_step('Run set fae fast-recovery trigger trigger-id event command and apply config'):
                fae.fast_recovery.trigger.set(trigger_id + ' ' + FastRecoveryConsts.TRIGGER_EVENT,
                                              FastRecoveryConsts.SEVERITY_WARNING, apply=True,
                                              dut_engine=engines.dut).verify_result()

            with allure_step('Verify fae fast-recovery trigger event for trigger-id is changed in show command'):
                fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                    fae.fast_recovery.trigger.show(trigger_id)).get_returned_value()
                ValidationTool.verify_field_value_in_output(fast_recovery_output,
                                                            FastRecoveryConsts.TRIGGER_EVENT,
                                                            FastRecoveryConsts.SEVERITY_WARNING).verify_result()

            with allure_step('Run unset fae fast-recovery trigger trigger-id event command and apply config'):
                fae.fast_recovery.trigger.unset(trigger_id, apply=True, dut_engine=engines.dut).verify_result()

            with allure_step('Verify fae fast-recovery trigger event for trigger-id is changed in show system'):
                fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                    fae.fast_recovery.trigger.show(trigger_id)).get_returned_value()
                ValidationTool.verify_field_value_in_output(fast_recovery_output,
                                                            FastRecoveryConsts.TRIGGER_EVENT,
                                                            FastRecoveryConsts.SEVERITY_DEFAULT).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_bad_flow_fast_recovery_state(engines):
    """
    Run set fae fast-recovery state command with invalid param value and verify the required state
        Test flow:
            1. Set fae fast-recovery state to random string 'neutral'[run cmd + apply conf]
            2. Verify that the output of the command execution is 'Invalid command'
            3. Verify fae fast-recovery trigger state is unchanged in show command
    """

    fae = Fae()
    invalid_state = 'neutral'
    try:
        with allure_step('Run set fae fast-recovery state command with neutral string and apply config'):
            cmd_execution_output = fae.fast_recovery.set(FastRecoveryConsts.STATE, invalid_state, apply=True,
                                                         dut_engine=engines.dut)
            assert cmd_execution_output.result is False

        with allure_step('Verify fae fast-recovery state is unchanged in show fas fast-recovery'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(fast_recovery_output, FastRecoveryConsts.STATE,
                                                        FastRecoveryConsts.STATE_ENABLED).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


@pytest.mark.interfaces
@pytest.mark.simx
def test_bad_flow_fast_recovery_trigger_event(engines):
    """
    Run set fae fast-recovery trigger event command with invalid param value and verify the required event
        Test flow:
            1. Set fae fast-recovery trigger event to random string 'info'[run cmd + apply conf]
            2. Verify that the output of the command execution is 'Invalid command'
            3. Verify fae fast-recovery trigger trigger event is unchanged in show command
    """

    fae = Fae()
    invalid_event = 'info'
    trigger_id = FastRecoveryConsts.TRIGGER_CREDIT_WATCHDOG
    try:
        with allure_step('Run set fae fast-recovery state command with neutral string and apply config'):
            cmd_execution_output = fae.fast_recovery.trigger.set(trigger_id + ' ' + FastRecoveryConsts.TRIGGER_EVENT,
                                                                 invalid_event, apply=True, dut_engine=engines.dut)
            assert cmd_execution_output.result is False, "Invalid command did not fail"

        with allure_step('Verify fae fast-recovery trigger event for trigger-id is unchanged in show command'):
            fast_recovery_output = OutputParsingTool.parse_json_str_to_dictionary(
                fae.fast_recovery.trigger.show(trigger_id)).get_returned_value()
            ValidationTool.verify_field_value_in_output(fast_recovery_output,
                                                        FastRecoveryConsts.TRIGGER_EVENT,
                                                        FastRecoveryConsts.SEVERITY_DEFAULT).verify_result()

    finally:
        clear_port_fast_recovery(fae, engines)


def clear_port_fast_recovery(fae, engines):
    """
    Method to unset the port fast-recovery
    :param fae: System object
    :param engines: Engines object
    """

    with allure_step('Run unset port fast-recovery command and apply config'):
        fae.fast_recovery.unset(apply=True, dut_engine=engines.dut).verify_result()
