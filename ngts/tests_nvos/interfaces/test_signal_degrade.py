import logging
import allure
import pytest
import time
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import IbConsts

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.checklist
def test_show_signal_degrade(engines):
    """
    Execute show signal degrade and verify the output
    :param engines: ssh engine
    """
    with allure.step("Get a random active port"):
        selected_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]

    with allure.step("Check show signal degrade output"):
        output = selected_port.ib_interface.signal_degrade.show()
        Tools.ValidationTool.verify_field_exist_in_json_output(json_output=output,
                                                               keys_to_search_for=[IbConsts.SIGNAL_DEGRADE_STATE,
                                                                                   IbConsts.SIGNAL_DEGRADE_ACTION,
                                                                                   "fec"]).verify_result()


@pytest.mark.ib
@pytest.mark.checklist
def test_set_unset_signal_degrade(engines):
    """
    Check set/unset command for signal degrade (without traffic) and verify the output
    :param engines: ssh engine
    """
    with allure.step("Get a random active port"):
        selected_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]

    with allure.step("Set signal degrade status to 'disabled'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_DISABLED)

    with allure.step("Set signal degrade status to 'enabled'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_ENABLED)

    with allure.step("Set signal degrade action to 'shutdown'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_SHUTDOWN)

    with allure.step("Set signal degrade action to 'no-shutdown'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_NO_SHUTDOWN)

    with allure.step("Set signal degrade action to 'shutdown' and status to 'disabled'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_DISABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_SHUTDOWN)

    with allure.step("Set signal degrade action to 'no-shutdown' and status to 'disabled'"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_ENABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_NO_SHUTDOWN)

    with allure.step("Unset action"):
        _unset_signal_degrade_and_verify_output(port_obj=selected_port, unset_action=True)

    with allure.step("Unset state"):
        _unset_signal_degrade_and_verify_output(port_obj=selected_port, unset_state=True)


@pytest.mark.ib
@pytest.mark.checklist
def test_check_signal_degrade_functionality(engines, mst_device):
    """
    Send broken traffic and make sure the signal degrade functionality works as expected
    :param engines: ssh engine
    """
    with allure.step("Get a random active port"):
        selected_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]

    with allure.step("Verify selected port physical state is up"):
        port_state = selected_port.ib_interface.physical_port_state.get_operational()
        assert port_state == "up", "Physical state of selected port is down, can't proceed"

    try:
        with allure.step("Verify correct Noga setup"):
            assert engines.server, "Traffic server details can't be found in Noga setup"

        with allure.step("Check signal degrade for state = enabled and action = shutdown"):
            _check_signal_degrade_while_state_enabled_action_shutdown(engines, mst_device, selected_port)
            _recover_port(selected_port)

        with allure.step("Check signal degrade for state = disabled and action = shutdown"):
            _check_signal_degrade_while_state_disabled_action_shutdown(engines, mst_device, selected_port)

        with allure.step("Check signal degrade for state = enabled and action = no-shutdown"):
            _check_signal_degrade_while_state_enabled_action_no_shutdown(engines, mst_device, selected_port)

        with allure.step("Check signal degrade for state = disabled and action = no-shutdown"):
            _check_signal_degrade_while_state_enabled_action_no_shutdown(engines, mst_device, selected_port)

    finally:
        _recover_port(selected_port)
        selected_port.ib_interface.signal_degrade.unset(comp=IbConsts.SIGNAL_DEGRADE_STATE)
        selected_port.ib_interface.signal_degrade.unset(comp=IbConsts.SIGNAL_DEGRADE_ACTION)


def _check_signal_degrade_while_state_enabled_action_shutdown(engines, mst_device, selected_port):
    with allure.step("Set signal degrade status to enabled and action to shutdown"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_ENABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_SHUTDOWN)

    port_state = _simulate_signal_degrade(engines, mst_device, selected_port)
    assert port_state == "down", "The port is now down after signal degrade event"


def _check_signal_degrade_while_state_disabled_action_shutdown(engines, mst_device, selected_port):
    with allure.step("Set signal degrade status to disabled and action to shutdown"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_DISABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_SHUTDOWN)

        port_state = _simulate_signal_degrade(engines, mst_device, selected_port)
        assert port_state == "up", "The port is down while the status of signal degrade is disabled"


def _check_signal_degrade_while_state_enabled_action_no_shutdown(engines, mst_device, selected_port):
    with allure.step("Set signal degrade status to disabled and action to shutdown"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_ENABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_NO_SHUTDOWN)

        port_state = _simulate_signal_degrade(engines, mst_device, selected_port)
        assert port_state == "up", "The port is down while the action of signal degrade is no shutdown"


def _check_signal_degrade_while_state_disabled_action_no_shutdown(engines, mst_device, selected_port):
    with allure.step("Set signal degrade status to disabled and action to shutdown"):
        _set_signal_degrade_and_verify_output(port_obj=selected_port,
                                              state_value=IbConsts.SIGNAL_DEGRADE_STATE_DISABLED,
                                              action_value=IbConsts.SIGNAL_DEGRADE_ACTION_NO_SHUTDOWN)

        port_state = _simulate_signal_degrade(engines, mst_device, selected_port)
        assert port_state == "up", "The port is down while the action of signal degrade is no shutdown and" \
                                   "the state is disabled"


def _recover_port(selected_port):
    with allure.step("Recover selected port"):
        selected_port.ib_interface.signal_degrade.recover()
        with allure.step("Wait until selected port is up after recovering"):
            timer = 120
            port_state = "down"
            while timer > 0:
                port_state = selected_port.ib_interface.physical_port_state.get_operational()
                if port_state == "up":
                    break
                else:
                    time.sleep(10)
                    timer -= 10
            assert port_state == "up", "Physical state of selected port is not up after 120 seconds"


def _set_signal_degrade_and_verify_output(port_obj, state_value="", action_value=""):
    logging.info("Set signal degrade state to {} and/or action to {}".format(state_value, action_value))
    port_obj.ib_interface.signal_degrade.set(state=state_value, action=action_value)
    output = port_obj.ib_interface.signal_degrade.show()
    if state_value:
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_STATE,
                                                          expected_value=state_value).verify_result()
    if action_value:
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_ACTION,
                                                          expected_value=action_value).verify_result()


def _unset_signal_degrade_and_verify_output(port_obj, unset_state=False, unset_action=False):
    logging.info("Save the output before unset")
    output = port_obj.ib_interface.signal_degrade.show()
    pre_state = output[IbConsts.SIGNAL_DEGRADE_STATE]
    pre_action = output[IbConsts.SIGNAL_DEGRADE_ACTION]

    logging.info("Unset signal degrade")
    if unset_state:
        port_obj.ib_interface.signal_degrade.unset(comp=IbConsts.SIGNAL_DEGRADE_STATE)
    if unset_action:
        port_obj.ib_interface.signal_degrade.unset(comp=IbConsts.SIGNAL_DEGRADE_ACTION)

    logging.info("Verify output after unset")
    output = port_obj.ib_interface.signal_degrade.show()

    if unset_state:
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_STATE,
                                                          expected_value=IbConsts.SIGNAL_DEGRADE_STATE_DISABLED).\
            verify_result()
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_ACTION,
                                                          expected_value=pre_action).verify_result()

    if unset_action:
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_ACTION,
                                                          expected_value=IbConsts.SIGNAL_DEGRADE_ACTION_SHUTDOWN).\
            verify_result()
        Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output,
                                                          field_name=IbConsts.SIGNAL_DEGRADE_STATE,
                                                          expected_value=pre_state).verify_result()


def _simulate_signal_degrade(engines, mst_device, selected_port):
    with allure.step("Signal degrade simulator"):
        try:
            _start_signal_degrade_simulator(engines, mst_device)

            time.sleep(3)

            with allure.step("Read port status after signal degrade event"):
                port_state = selected_port.ib_interface.physical_port_state.get_operational()

        finally:
            _stop_signal_degrade_simulator(engines, mst_device)
    return port_state


def _start_signal_degrade_simulator(engines, mst_device):
    with allure.step("Start signal degrade simulator"):
        logging.info("Start signal degrade simulator")
        output = engines.server.run_cmd(
            "/auto/sw_system_project/MLNX_OS_INFRA/flaky_cable_new/cx4_ber_generator_qtm.sh {} 7".format(mst_device))
        assert "Done" in output, "Failed to start signal degrade simulator"


def _stop_signal_degrade_simulator(engines, mst_device):
    with allure.step("Stop signal degrade simulator"):
        logging.info("Stop signal degrade simulator")
        output = engines.server.run_cmd(
            "/auto/sw_system_project/MLNX_OS_INFRA/flaky_cable_new/cx4_ber_generator_qtm.sh {} 0".format(mst_device))
        assert "Done" in output, "Failed to stop signal degrade simulator"
