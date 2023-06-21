import logging
import time
from ngts.tools.test_utils import allure_utils as allure
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from retry.api import retry_call
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import *
from ngts.tests_nvos.general.security.conftest import *

logger = logging.getLogger()


@pytest.mark.init_flow
def test_system_ready_state_up(engines):
    """
    Test flow:
        0. serial connection
        1. Run nv action reboot system (using engine.dut)
        2. validate Status = System is ready
        3. Run nv show fae system ready
        4. validate state = enabled
        5. Run nv action reboot system - will ends after catching "system is ready message" and CLI is up
        6. Run nv show system ready
        7. validate Status = System is ready
    """
    with allure.step('reboot the system'):
        reload_cmd_set = "nv action reboot system"
        DutUtilsTool.reload(engines=engines.dut, command=reload_cmd_set,
                            should_wait_till_system_ready=False).verify_result()

    with allure.step('reconnect to the switch'):
        ssh_connection = ConnectionTool.create_ssh_conn(engines.dut.ip, engines.dut.username, engines.dut.password).get_returned_value()

    with allure.step('verify NVUE is not working before system is ready'):
        assert 'System is initializing!' in ssh_connection.run_cmd('nv show system'), "WE CAN NOT RUN NV COMMANDS BEFORE SYSTEM IS READY MESSAGE"

    with allure.step('verify SYSTEM_READY|SYSTEM_STATE is not exist yet'):
        assert '(empty array)' in ssh_connection.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS), "SYSTEM_READY state table should not be exist before system is ready"

    with allure.step('wait until the system is ready'):
        DutUtilsTool.wait_for_nvos_to_become_functional(ssh_connection).verify_result()

    logs_to_find = ['Wait until the NOS signal we are ready to serve', 'System is ready']
    verify_expected_logs(ssh_connection, logs_to_find)

    with allure.step('check the system status in DB'):
        assert SystemConsts.STATUS_UP in ssh_connection.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS), "SYSTEM STATE SHOULD BE UP"

    with step("verify the system is ready using nv show system"):
        system = System(None)
        ValidationTool.verify_field_value_in_output(OutputParsingTool.parse_json_str_to_dictionary(system.show()).verify_result(), SystemConsts.STATUS, SystemConsts.STATUS_DEFAULT_VALUE).verify_result()


@pytest.mark.init_flow
def test_system_ready_state_down(engines, devices):
    """
    Test flow:
        0. serial connection
        1. Run nv action reboot system (using engine.dut)
        2. kill one of the dockers
        3. validate we can not run CLI and also the system status table is not exist
        4. verify expected logs after waiting 10 minuets
        5. start docker as a cleanup step
    """
    with allure.step('reboot the system'):
        reload_cmd_set = "nv action reboot system"
        DutUtilsTool.reload(engines=engines.dut, command=reload_cmd_set, should_wait_till_system_ready=False).verify_result()

    with allure.step('reconnect to the switch'):
        ssh_connection = ConnectionTool.create_ssh_conn(engines.dut.ip, engines.dut.username, engines.dut.password).get_returned_value()

    try:

        with allure.step('test system status after killing swss docker'):
            with allure.step('pick a docker to kill'):
                docker_to_kill = [i for i in devices.dut.available_dockers if i.startswith('swss')][0]

            with allure.step('kill docker {}'.format(docker_to_kill)):
                engines.dut.run_cmd('sudo systemctl stop {}'.format(docker_to_kill))

        with allure.step('Sleep 5 min'):
            time.sleep(300)

        with allure.step('verify SYSTEM_READY|SYSTEM_STATE is not exist yet'):
            assert '(empty array)' in ssh_connection.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS), "SYSTEM_READY state table should not be exist before system is ready"

        with allure.step('verify NVUE is not working before system is ready'):
            assert 'System is initializing!' in ssh_connection.run_cmd('nv show system'), "WE CAN NOT RUN NV COMMANDS BEFORE SYSTEM IS READY MESSAGE"

        with allure.step('Sleep 5 min'):
            time.sleep(300)

        logs_to_find = ['Wait until the NOS signal we are ready to serve', 'System is not ready']
        verify_expected_logs(ssh_connection, logs_to_find)

        with allure.step('verify the system status is DOWN'):
            assert SystemConsts.STATUS_DOWN in ssh_connection.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS), "SYSTEM STATE SHOULD BE DOWN"

        with step("verify we can run nvue command and the system status is not ok"):
            system = System(None)
            ValidationTool.verify_field_value_in_output(OutputParsingTool.parse_json_str_to_dictionary(system.show()).verify_result(), SystemConsts.STATUS, SystemConsts.STATUS_NOT_OK).verify_result()

    finally:
        with allure.step('start docker {} as a cleanup step'.format(docker_to_kill)):
            engines.dut.run_cmd('sudo systemctl start {}'.format(docker_to_kill))


def verify_expected_logs(engine, logs_to_find):
    """

    :param engine:
    :param logs_to_find: list of logs to find
    :return:
    """
    with allure.step('verify expected logs'):
        log_file = engine.run_cmd('cat /var/log/nvued.log')
        for log in logs_to_find:
            with allure.step('try to find "{}" in the logs'.format(log)):
                assert log in log_file, "missing logs, we expect to see {} in the output".format(log)
