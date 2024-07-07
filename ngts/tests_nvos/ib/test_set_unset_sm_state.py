import pytest
from ngts.tools.test_utils import allure_utils as allure
import logging
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import IbConsts, NvosConst
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool

logger = logging.getLogger()


@pytest.mark.ib
@pytest.mark.sm
def test_show_ib_sm_default_values(engines, devices):
    """
    Test flow:
        1. Select all ports in state Active or initialize
        2. for each port set state to down
        3. Stop openSM
        4. run nv show ib sm
        5. verify all default values: State = disabled, Is-running = no, sm-priority = 0, sm-sl = 0 ,max-nodes = 2048
        6. select random port
        7. set the state of the random_port to up
        8. Start OpenSm
        9. verify the ports logical state = initialize
        10. set the state of the random_port to up
        11. verify it's active now
        12. for each port in the list set state to up (as a clean up step)
    """
    ib = Ib(None)
    switch_type = devices.dut.switch_type.lower()
    with allure.step('get all active or initialize ports'):
        active_ports = \
            Tools.RandomizationTool.select_random_ports(requested_ports_type=switch_type, num_of_ports_to_select=0,
                                                        requested_ports_logical_state=NvosConsts.LINK_LOG_STATE_ACTIVE).get_returned_value()

    with allure.step('verify ib sm default values'):
        sm_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
        labels_list = [IbConsts.SM_STATE, IbConsts.SM_PRIORITY, IbConsts.SM_SL, IbConsts.MAX_NODES, IbConsts.IS_RUNNING]
        values_list = [IbConsts.SM_STATE_DISABLE, IbConsts.PRIO_SL_DEFAULT_VALUE, IbConsts.PRIO_SL_DEFAULT_VALUE, IbConsts.MAX_NODES_DEFAULT_VALUE, IbConsts.IS_RUNNING_NO]
        ValidationTool.validate_fields_values_in_output(labels_list, values_list, sm_dict).verify_result()

    if not active_ports:
        logger.info('no active ports!')
        with allure.step("Start openSM"):
            OpenSmTool.start_open_sm_on_dut(engines).verify_result()
        return

    with allure.step('set down the state of all active ports'):
        set_all_ports_state(active_ports, NvosConst.PORT_STATUS_DOWN)

    with allure.step('set up the state of all active ports as a clean up step'):
        set_all_ports_state(active_ports, NvosConst.PORT_STATUS_UP)

    with allure.step("Start openSM"):
        OpenSmTool.start_open_sm_on_dut(engines).verify_result()

    with allure.step('verify all ports back to active'):
        active_ports[0].interface.wait_for_port_state(state=NvosConst.PORT_STATUS_UP,
                                                      logical_state="Active").verify_result()


@pytest.mark.ib
@pytest.mark.sm
def test_set_unset_sm_state_many_times(engines, times=5):
    """
    :param engines: dut engine
    :param times: how many times you want to enable and disable the sm

    Test flow:
        1. Run nv set ib sm state enabled
        2. Run nv config apply
        3. Run nv set ib sm state disable
        4. Run nv config apply
        5. Rerun 1-4 steps <times> times
        6. Run nv show ib sm log files
        7. Verify only one file exist
    """
    ib = Ib(None)
    with allure.step('enable and disable sm {times} times'.format(times=times)):
        for i in range(times):
            with allure.step('Run nv set ib sm {param} {value} and apply the configurations'.format(param=IbConsts.SM_STATE, value=IbConsts.SM_STATE_ENABLE)):
                OpenSmTool.start_open_sm_on_dut(engines).verify_result()

            with allure.step('Run nv set ib sm {param} {value} and apply the configurations'.format(param=IbConsts.SM_STATE, value=IbConsts.SM_STATE_DISABLE)):
                OpenSmTool.stop_open_sm_on_dut(engines).verify_result()

    with allure.step('check if only one sm log file exist'):
        log_files = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.log.show(IbConsts.FILES)).verify_result()
        assert len(log_files) == 1, "more than one sm log file exist"


def set_all_ports_state(ports, state):
    port = None
    for port in ports:
        TestToolkit.update_tested_ports([port])
        port.interface.link.state.set(state, apply=True).verify_result()
    if port:
        port.interface.wait_for_port_state(state=state).verify_result()
