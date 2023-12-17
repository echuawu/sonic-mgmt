import pytest
import logging

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_constants.constants_nvos import DatabaseConst
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.MultiPlanarTool import MultiPlanarTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import NvosConsts, IbInterfaceConsts
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.tools.test_utils.allure_utils import step as allure_step


logger = logging.getLogger()


@pytest.mark.interface
@pytest.mark.multiplanar
@pytest.mark.simx_xdr
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_interface_aggregated_port_split(engines, devices, test_api, players, interfaces):
    """
    validate all show fae interface commands.

    Test flow:
    1. Change platform json
    2. Check aggregated port lanes
    3. Change system profile to breakout mode
    4. Split a port
    5. Do set command for a port
    6. Redis validation
    7. Run traffic and check counters
    8. Clear counters and validate
    9. Unset a port
    """

    TestToolkit.tested_api = test_api
    system = System(None)

    with allure_step("Select random aggregated port and validate planarized ports"):
        selected_fae_aggregated_port = MultiPlanarTool.select_random_aggregated_port(devices)
        fae_interface_output = OutputParsingTool.parse_show_interface_output_to_dictionary(
            selected_fae_aggregated_port.port.interface.show()).get_returned_value()
        ValidationTool.compare_values(fae_interface_output['planarized-ports'],
                                      devices.dut.AGGREGATED_PORT_PLANARIZED_PORTS).verify_result()

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
        parent_port = split_ports[0]
        parent_port.ib_interface.link.set(op_param_name='breakout',
                                          op_param_value=IbInterfaceConsts.LINK_BREAKOUT_NDR,
                                          apply=True, ask_for_confirmation=True).verify_result()

    with allure_step("Get split ports"):
        child_ports = MultiPlanarTool._get_split_child_ports(parent_port)

    with allure_step("Validate next two ports not exist"):
        Fae(port_name='sw11p1').port.interface.show(should_succeed=False)
        Fae(port_name='sw11p2').port.interface.show(should_succeed=False)
        Fae(port_name='sw11p1s1').port.interface.show(should_succeed=False)
        Fae(port_name='sw11p2s1').port.interface.show(should_succeed=False)

    with allure_step("Validate split port going to up"):
        fae_child_port = Fae(port_name='sw10p1s1')
        child_port_output = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
            fae_child_port.port.interface.show()).get_returned_value()
        current_state = child_port_output[IbInterfaceConsts.LINK]
        assert current_state == NvosConsts.LINK_STATE_UP, "Current state {} is not {} as expected".\
            format(current_state, NvosConsts.LINK_STATE_UP)

    with allure_step("Change mtu on child port and check changes"):
        child_ports[0].ib_interface.link.set(op_param_name='mtu', op_param_value=512, apply=True,
                                             ask_for_confirmation=True).verify_result()

        with allure_step("Verify changed values on child port"):
            child_ports[0].ib_interface.wait_for_port_state(NvosConsts.LINK_STATE_UP, sleep_time=8).verify_result()
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                child_ports[0].ib_interface.link.show()).get_returned_value()
            Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                              field_name='mtu',
                                                              expected_value='512').verify_result()

    with allure_step("Redis validation"):
        redis_cli_output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engines.dut, asic="",
                                                                db_name=DatabaseConst.CONFIG_DB_NAME,
                                                                db_config="IB_PORT\\|{0}".format('Infiniband72'),
                                                                param="planarized_ports")
        assert redis_cli_output != 2, "On split port planarized ports not 2"

        redis_cli_output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engines.dut, asic="",
                                                                db_name=DatabaseConst.CONFIG_DB_NAME,
                                                                db_config="IB_PORT\\|{0}".format('Infiniband80'),
                                                                param="planarized_ports")
        assert redis_cli_output != 2, "On split port planarized ports not 2"

        redis_cli_output = Tools.DatabaseTool.sonic_db_cli_hget(engine=engines.dut, asic="",
                                                                db_name=DatabaseConst.CONFIG_DB_NAME,
                                                                db_config="IB_PORT\\|{0}".format('Infiniband72'),
                                                                param="planarized_ports")
        assert redis_cli_output != '(empty array)', "Planarized port not exist in redis db"

    with allure_step("Run traffic and check counters"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

        with allure_step("Check counters before split, should be not 0"):
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
                parent_port.ib_interface.link.stats.show()).get_returned_value()
            assert (output_dictionary[IbInterfaceConsts.LINK_STATS_IN_PKTS] ==
                    output_dictionary[IbInterfaceConsts.LINK_STATS_OUT_PKTS]) != 0

    with allure_step("Clear counters and validate"):
        parent_port.ib_interface.action_clear_counter_for_all_interfaces(engines.dut).verify_result()

        with allure_step("Check counters after clear counters, should be 0"):
            output_dictionary = Tools.OutputParsingTool.parse_show_interface_stats_output_to_dictionary(
                parent_port.ib_interface.link.stats.show()).get_returned_value()
            assert (output_dictionary[IbInterfaceConsts.LINK_STATS_IN_PKTS] ==
                    output_dictionary[IbInterfaceConsts.LINK_STATS_OUT_PKTS]) == 0

    with allure_step("set config to default"):
        child_ports[0].ib_interface.link.unset(op_param='breakout', apply=True, ask_for_confirmation=True).\
            verify_result()
