import allure
import logging
import pytest
from ngts.nvos_constants.constants_nvos import NvosConst

logger = logging.getLogger()


@pytest.mark.init_flow
def test_bugs_status():
    """
    Run journal-ctl bugs command and verify there is no unknown bugs
        TODO
    Run sudo journalctl -b -p warning --no-pager and validate all bugs are either "known-bug" or "wont-fix/not-a-bug"
    :return: None, open a ticket for any new bug
    """
    pass


@pytest.mark.init_flow
@pytest.mark.simx
def test_system_services(engines, devices):
    """
    Verifying the NVOS system services are in active state
    TODO
    Run sudo systemctl status and validate systemctl state is active and no jobs or failures"
        should be:
            State: active
            Jobs: 0 queued
            Failed: 0 units
        for now it's:
            State: degraded
            Jobs: 0 queued
            Failed: 1 units

    Run sudo systemctl is-active hw-management and validate hw_management is active"
    :return: None, raise error in case one or more services are inactive
    """
    with allure.step("Validate services are active"):
        res_obj = devices.dut.verify_services(engines.dut)
        assert res_obj.result, res_obj.info


'''
@pytest.mark.init_flow
def test_existence_of_tables_in_databases(engines, devices):
    """
    Verifying the NVOS Databases created the correct tables in redis
    :return: None, raise error in case one or more tables are missed
    """
    with allure.step("Validate no missing database default tables"):
        res_obj = devices.dut.verify_databases(engines.dut)
        assert res_obj.result, res_obj.info
'''


@pytest.mark.init_flow
def test_ports_are_up(engines, devices):
    """
    Verifying the NVOS ports are up
    :return: None, raise error in case one or more ports are down
    """
    with allure.step("Validate all ports status is up"):
        res_obj = devices.dut.verify_ib_ports_state(engines.dut, NvosConst.PORT_STATUS_UP)
        assert res_obj.result, res_obj.info
