import allure
import logging
import pytest

from ngts.constants.constants_nvos import NvosConst, DatabaseConst
from ngts.nvos_tools.infra.DatabaseReaderTool import DatabaseReaderTool
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
def test_system_sevices(engines):
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
        storage = [Database('APPL_DB', DatabaseConst.APPL_DB_ID, DatabaseConst.APPL_DB_TABLES_DICT),
                   Database('ASIC_DB', DatabaseConst.ASIC_DB_ID, DatabaseConst.ASIC_DB_TABLES_DICT),
                   Database('COUNTERS_DB', DatabaseConst.COUNTERS_DB_ID, DatabaseConst.COUNTERS_DB_TABLES_DICT),
                   Database('CONFIG_DB', DatabaseConst.CONIFG_DB_ID, DatabaseConst.CONIFG_DB_TABLES_DICT)]

        for database_obj in storage:
            res_obj = database_obj.verify_num_of_tables_in_database(engines.dut)
            if not res_obj.result:
                logger.error(res_obj.info)
                err_flag = False
        assert err_flag, "one or more default tables are missing"


@pytest.mark.init_flow
def test_ports_are_up(engines):
    """
    Verifying the NVOS ports are up
    :return: None, raise error in case one or more ports are down
    """
    with allure.step("Validate all ports status is up"):
        err_flag = True
        output = DatabaseReaderTool.get_all_table_names_in_database(engines.dut, 'CONFIG_DB', 'IB_PORT').returned_value
        for table_name in output:
            obj = DatabaseReaderTool.read_from_database('CONFIG_DB', engines.dut, table_name, 'admin_status')
            if obj.returned_value != NvosConst.PORT_STATUS:
                err_flag = False
                logger.error("port {table_name} is down \n".format(table_name=table_name))
        assert err_flag, "one or more ports are down"
