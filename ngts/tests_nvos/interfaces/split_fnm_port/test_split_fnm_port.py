import pytest
import logging

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.MultiPlanarTool import MultiPlanarTool
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts, IbInterfaceConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.tools.test_utils.allure_utils import step as allure_step
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_interface_fnm_port_split(engines, devices, test_api, players, interfaces):
    """
    validate all show fae interface commands.

    Test flow:
    1. Validate show fae interface
    2. Validate show fae interface <interface-id>
    3. Validate show fae interface <interface-id> link
    4. Validate show fae interface <interface-id> link counters
    5. Validate show fae interface <interface-id> link diagnostics
    6. Validate show fae interface <interface-id> link state
    7. Validate show fae interface <interface-id> link plan-ports
    8. Validate set fae interface <interface-id> link lanes <1X/2X/4X>
    9. Validate unset fae interface <interface-id> link lanes
    """

    TestToolkit.tested_api = test_api
    system = System(None)

    with allure_step('Change system profile to breakout'):
        system.profile.action_profile_change(params='adaptive-routing enabled breakout-mode enabled')
        with allure_step('Verify changed values'):
            system_profile_output = OutputParsingTool.parse_json_str_to_dictionary(system.profile.show()) \
                .get_returned_value()
            values_to_verify = [SystemConsts.PROFILE_STATE_ENABLED, 1792,
                                SystemConsts.PROFILE_STATE_ENABLED, SystemConsts.PROFILE_STATE_DISABLED,
                                SystemConsts.DEFAULT_NUM_SWIDS]
            ValidationTool.validate_fields_values_in_output(SystemConsts.PROFILE_OUTPUT_FIELDS,
                                                            values_to_verify,
                                                            system_profile_output).verify_result()
            logging.info("All expected values were found")

    with allure_step("Start OpenSM and check traffic port up"):
        OpenSmTool.start_open_sm(engines.dut).verify_result()
        split_ports = MultiPlanarTool._get_split_ports()

    with allure_step("Split splitter port"):
        fnm_port = split_ports[0]
        fnm_port.ib_interface.link.set(op_param_name='breakout', op_param_value=IbInterfaceConsts.LINK_BREAKOUT_NDR,
                                       apply=True, ask_for_confirmation=True).verify_result()

    with allure_step("Validate split port going to up"):
        fae_child_port = Fae(port_name='fnm1s1')
        child_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            fae_child_port.port.interface.show()).get_returned_value()
        current_state = child_port_output[IbInterfaceConsts.LINK]
        assert current_state == NvosConsts.LINK_STATE_UP, "Current state {} is not {} as expected". \
            format(current_state, NvosConsts.LINK_STATE_UP)

    with allure_step("Run traffic and check counters"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

        with allure_step("Check counters before split, should be not 0"):
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
                fnm_port.ib_interface.link.stats.show()).get_returned_value()
            assert (output_dictionary[IbInterfaceConsts.LINK_STATS_IN_PKTS] ==
                    output_dictionary[IbInterfaceConsts.LINK_STATS_OUT_PKTS]) != 0

    with allure_step("Clear counters and validate"):
        fnm_port.ib_interface.action_clear_counter_for_all_interfaces(engines.dut).verify_result()

        with allure_step("Check counters after clear counters, should be 0"):
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
                fnm_port.ib_interface.link.stats.show()).get_returned_value()
            assert (output_dictionary[IbInterfaceConsts.LINK_STATS_IN_PKTS] ==
                    output_dictionary[IbInterfaceConsts.LINK_STATS_OUT_PKTS]) == 0
