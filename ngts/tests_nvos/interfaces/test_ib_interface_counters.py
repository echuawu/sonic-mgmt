import logging
import allure
import pytest

from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.infra.ResultObj import ResultObj

logger = logging.getLogger()


@pytest.mark.ib_interfaces
def test_ib_clear_counters(engines, players, interfaces):
    """
    Clear counters test
    Commands:
        > nv action interface {port_name} link clear stats

    flow:
    1. Select a random port (which is up)
    2. Run traffic and identify which ports are connected to a traffic server
    3. Select a random traffic port
    4. Run clear counters for selected port
    5. Make sure the counters were cleared
    6. Run traffic and make sure the counters are not 0
    """
    with allure.step('Select a random port which connected to a server'):
        selected_port = Tools.RandomizationTool.get_random_port_connected_to_server().get_returned_value()
        logging.info('selected port: ' + selected_port.name)

    with allure.step('Clear counter for selected port "{}"'.format(selected_port.name)):
        selected_port.ib_interface.link.stats.clear_stats()
        with allure.step('Check selected port counters'):
            check_port_counters(selected_port, True).verify_result()
        logging.info("The counters were cleared for port '{}".format(selected_port.name))

    with allure.step('Send traffic throw selected port'):
        Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces)

    with allure.step('Check selected port counters'):
        check_port_counters(selected_port, False).verify_result()


def check_port_counters(selected_port, should_be_zero):
    counters = selected_port.ib_interface.link.stats.in_bytes.get_operational()
    counters += selected_port.ib_interface.link.stats.in_drops.get_operational(False)
    counters += selected_port.ib_interface.link.stats.in_errors.get_operational(False)
    counters += selected_port.ib_interface.link.stats.in_symbol_errors.get_operational(False)
    counters += selected_port.ib_interface.link.stats.in_pkts.get_operational(False)
    counters += selected_port.ib_interface.link.stats.out_bytes.get_operational(False)
    counters += selected_port.ib_interface.link.stats.out_drops.get_operational(False)
    counters += selected_port.ib_interface.link.stats.out_errors.get_operational(False)
    counters += selected_port.ib_interface.link.stats.out_pkts.get_operational(False)
    counters += selected_port.ib_interface.link.stats.out_wait.get_operational(False)
    return ResultObj((should_be_zero and not counters) or {counters and not should_be_zero}, "")
