from ngts.tools.test_utils import allure_utils as allure
import logging
import pytest
from ngts.nvos_constants.constants_nvos import SystemConsts, DatabaseConst
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.DatabaseTool import DatabaseTool


logger = logging.getLogger()


def test_multi_asic(engines, devices):
    """
    This test should run only on multi asic system!
    configure hostname and validate it is written in all the redis-dbs over all the asic and system
    (in database, database0 and database1).
    """
    system = System()
    new_hostname_value = "temp-hostname"
    try:
        with allure.step("Configure new hostname: {}".format(new_hostname_value)):
            logger.info("Configure new hostname: {}".format(new_hostname_value))
            system.set(SystemConsts.HOSTNAME, new_hostname_value, apply=True, ask_for_confirmation=True)

        with allure.step("Validate new hostname with show command"):
            logger.info("Validate new hostname with show command")
            system_output = OutputParsingTool.parse_json_str_to_dictionary(system.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(system_output, SystemConsts.HOSTNAME,
                                                        new_hostname_value).verify_result()

        with allure.step("Validate new hostname in all redis-db"):
            logger.info("Validate new hostname in all redis-db")
            validate_hostname_in_redis_database(engines.dut, devices.dut, new_hostname_value)
    finally:
        with allure.step("Cleanup: unset system"):
            logger.info("Cleanup: unset system")
            system.unset(SystemConsts.HOSTNAME, apply=True, ask_for_confirmation=True)


def validate_hostname_in_redis_database(engine, device, expected_hostname):
    '''
    validate expected_hostname is written in all the redis-dbs
    run the cmd:
     docker exec -it {database docker} redis-cli -n 4 hget "DEVICE_METADATA|localhost" "hostname"
    for each database docker, the system database (database) and the asic's databases (marlin: database0 , database1)
    '''
    database_dockers = ['database']
    for asic_num in range(device.asic_amount):
        database_dockers.append('database{}'.format(asic_num))
    for database_docker in database_dockers:
        output = DatabaseTool.sonic_db_run_hget_in_docker(docker_name=database_docker, engine=engine, asic="",
                                                          db_name=DatabaseConst.CONFIG_DB_NAME,
                                                          db_config='\"DEVICE_METADATA|localhost\"',
                                                          param="hostname")
        # cmd = 'docker exec -it {database_docker} redis-cli -n 4 hget \"DEVICE_METADATA|localhost\" \"hostname\"'.format(database_docker=database_docker)
        # output = engine.run_cmd(cmd).replace("\"", "")
        assert output == expected_hostname, "Expect to get the new hostname: {}, but got {}".format(expected_hostname, output)
