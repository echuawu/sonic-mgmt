import logging
import pytest
import allure
from ngts.nvos_tools.infra.Tools import Tools

logger = logging.getLogger()


@pytest.mark.nvos_ci
@pytest.mark.general
def test_basic_traffic(players, interfaces, start_sm):
    """
    Basic traffic test
    """
    with allure.step("Validate ib traffic"):
        Tools.TrafficGeneratorTool.send_ib_traffic(players, interfaces, True).verify_result()

    with allure.step("Validate ipoib traffic"):
        Tools.TrafficGeneratorTool.send_ipoib_traffic(players, interfaces, True).verify_result()
