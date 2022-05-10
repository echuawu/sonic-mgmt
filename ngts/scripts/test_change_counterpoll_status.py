#!/usr/bin/env python
import allure
import logging
import pytest
from retry import retry

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
@pytest.mark.parametrize("action", ["enable", "disable"])
@allure.title('Workaround: change counterpooll status')
def test_change_counterpoll_status(topology_obj, action):
    """
    This test will change counterpoll status.
    It is a workaround due to the the bug of https://redmine.mellanox.com/issues/3047059.
    Before running qos sai test, disable all counterpolls.
    After running qos sai test, enable all counterpolls.
    :param topology_obj: topology object fixture
    :param action: enable or disable
    :return: raise assertion error in case of script failure
    """
    try:
        dut_cli_object = topology_obj.players['dut']['cli']
        with allure.step(" {} counterpoll status".format(action)):
            counterpoll_status_dict = dut_cli_object.counterpoll.parse_counterpoll_show()
            for counter, value in counterpoll_status_dict.items():
                if action == "enable":
                    if value['Status'] == 'disable':
                        dut_cli_object.counterpoll.enable_counterpoll()
                        dut_cli_object.general.reload_flow(topology_obj=topology_obj, reload_force=True)
                        break
                elif action == "disable":
                    if value['Status'] == 'enable':
                        dut_cli_object.counterpoll.disable_counterpoll()
                        dut_cli_object.general.reload_flow(topology_obj=topology_obj, reload_force=True)
                        break
        with allure.step("Verify counterpoll status is {}".format(action)):
            veify_counter_status(dut_cli_object, excepted_status=action)
    except Exception as err:
        raise AssertionError(err)


@retry(Exception, tries=10, delay=5)
def veify_counter_status(dut_cli_object, excepted_status):
    counterpoll_status_dict = dut_cli_object.counterpoll.parse_counterpoll_show()
    for counter, value in counterpoll_status_dict.items():
        assert value['Status'] == excepted_status, "The status of {} is: {}".format(counter, value['Status'])
