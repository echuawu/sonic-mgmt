import allure
import logging
import pytest
from retry import retry

from ngts.constants.constants_nvos import NvosConst, DatabaseConst
from ngts.nvos_tools.database.database import Database
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
def test_system_services(engines):
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
    err_flag = True
    with allure.step("Validate services are active"):
        for service in NvosConst.SERVICES_LIST:
            cmd_output = engines.dut.run_cmd('systemctl --type=service | grep {}'.format(service))
            if NvosConst.SERVICE_STATUS not in cmd_output:
                logger.error("{service} service is not {service}active \n".format(service=NvosConst.SERVICE_STATUS))
                err_flag = False
        assert err_flag, "one or more services are not active"


@pytest.mark.init_flow
def test_existence_of_tables_in_databases(engines):
    """
    Verifying the NVOS Databases created the correct tables in redis
    :return: None, raise error in case one or more tables are missed
    """
    with allure.step("Validate no missing database default tables"):
        err_flag = True
        storage = [Database(DatabaseConst.APPL_DB_NAME, DatabaseConst.APPL_DB_ID, DatabaseConst.APPL_DB_TABLES_DICT),
                   Database(DatabaseConst.ASIC_DB_NAME, DatabaseConst.ASIC_DB_ID, DatabaseConst.ASIC_DB_TABLES_DICT),
                   Database(DatabaseConst.COUNTERS_DB_NAME, DatabaseConst.COUNTERS_DB_ID, DatabaseConst.COUNTERS_DB_TABLES_DICT),
                   Database(DatabaseConst.CONFIG_DB_NAME, DatabaseConst.CONFIG_DB_ID, DatabaseConst.CONFIG_DB_TABLES_DICT)]

        for database_obj in storage:
            try:
                validate_database_tables(engines, database_obj)
            except Exception:
                err_flag = False

        assert err_flag, "one or more default tables are missing"


@retry(Exception, tries=3, delay=5)
def validate_database_tables(engines, database_obj):
    res_obj = database_obj.verify_num_of_tables_in_database(engines.dut)
    assert res_obj.result, res_obj.info
    return True


@pytest.mark.init_flow
def test_ports_are_up(engines):
    """
    Verifying the NVOS ports are up
    :return: None, raise error in case one or more ports are down
    """
    with allure.step("Validate all ports status is up"):
        config_db = Database(DatabaseConst.CONFIG_DB_NAME, DatabaseConst.CONFIG_DB_ID, DatabaseConst.CONFIG_DB_TABLES_DICT)
        field_name = NvosConst.PORT_STATUS_LABEL
        expected_value = NvosConst.PORT_STATUS_UP
        table_name_substring = NvosConst.PORT_CONFIG_DB_TABLES_PREFIX
        res_obj = config_db.verify_filed_value_in_all_tables(engines.dut, table_name_substring, field_name, expected_value)
        assert res_obj.result, "one or more ports are down"
