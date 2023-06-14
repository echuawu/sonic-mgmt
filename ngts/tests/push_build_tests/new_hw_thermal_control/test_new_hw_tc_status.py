import allure
import logging
import pytest
from ngts.helpers.new_hw_thermal_control_helper import check_hw_thermal_control_status, is_support_new_hw_tc


logger = logging.getLogger()


@allure.title('test hw tc status')
def test_hw_tc_status(cli_objects, is_simx):
    """
    This test is to verify new hw thermal control service status
    1. Check hw tc status is running
    """
    if not is_support_new_hw_tc(cli_objects, is_simx):
        pytest.skip("The new hw tc feature is missing, skipping the test case")

    with allure.step(f'Check hw thermal control status'):
        check_hw_thermal_control_status(cli_objects)
