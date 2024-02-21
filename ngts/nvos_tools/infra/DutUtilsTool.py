import logging
import time

from paramiko.ssh_exception import AuthenticationException

from .ResultObj import ResultObj, IssueType
import subprocess
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from retry.api import retry_call, retry
from ngts.nvos_constants.constants_nvos import SystemConsts, DatabaseConst, NvosConst
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.DatabaseTool import DatabaseTool

logger = logging.getLogger()


class DutUtilsTool:

    @staticmethod
    def reload(engine, device, command, find_prompt_tries=80, find_prompt_delay=2, should_wait_till_system_ready=True,
               confirm=False):
        """

        :param should_wait_till_system_ready: if True then we will wait till the system is ready, if false then we only will wait till we can re-connect to the system
        :param engine:
        :param device:
        :param command:
        :param find_prompt_tries:
        :param find_prompt_delay:
        :return:
        """
        with allure.step('Reload the system with {} command, and wait till system is ready'.format(command)):
            if confirm:
                list_commands = [command, 'y']
                device.reload_device(engine, list_commands)
            else:
                device.reload_device(engine, [command])

            with allure.step('Waiting for switch shutdown after reload command'):
                check_port_status_till_alive(False, engine.ip, engine.ssh_port)
                engine.disconnect()

            if not should_wait_till_system_ready:
                time.sleep(40)
                return ResultObj(result=True, info="system is not ready yet")

            with allure.step('Waiting for switch to be ready'):
                check_port_status_till_alive(True, engine.ip, engine.ssh_port)
                result_obj = device.wait_for_os_to_become_functional(engine, find_prompt_delay=find_prompt_delay)
        return result_obj

    @staticmethod
    def check_ssh_for_authentication_error(engine, device):
        try:
            retry_call(engine.run_cmd, fargs=[''], tries=2, delay=3, logger=logger)
        except AuthenticationException as e:
            if engine.password == device.default_password:
                engine.password = NvosConst.OLD_PASS
            else:
                engine.password = device.default_password

    @staticmethod
    def run_cmd_and_reconnect(engine, command, find_prompt_tries=5, find_prompt_delay=2):
        """
            this tool will help u to run commands that disconnect the admin

        :param engine:
        :param command:
        :param find_prompt_tries:
        :param find_prompt_delay:
        :return:
        """
        with allure.step('Run {} and reconnect'.format(command)):
            engine.send_config_set(command, exit_config_mode=False, cmd_verify=False)
            engine.disconnect()
            retry_call(engine.run_cmd, fargs=[''], tries=find_prompt_tries, delay=find_prompt_delay, logger=logger)

            return ResultObj(result=True, info="Reconnected After Running {}".format(command))

    @staticmethod
    def wait_for_nvos_to_become_functional(engine, find_prompt_tries=60, find_prompt_delay=10):
        with allure.step('wait until the system is ready - check SYSTEM_STATE table'):
            with allure.step('wait for the system table to exist'):
                wait_for_system_table_to_exist(engine)

            output = DatabaseTool.sonic_db_cli_hgetall(engine=engine, asic="",
                                                       db_name=DatabaseConst.STATE_DB_NAME,
                                                       table_name='\"SYSTEM_READY|SYSTEM_STATE\"')
            if SystemConsts.STATUS_DOWN in output:
                return ResultObj(result=False, info="THE SYSTEM IS NOT OK", issue_type=IssueType.PossibleBug)

            if '(empty array)' in output:
                return ResultObj(result=False, info="SYSTEM_READY|SYSTEM_STATE TABLE IS MISSED",
                                 issue_type=IssueType.PossibleBug)

            with allure.step('wait until the CLI is up'):
                wait_until_cli_is_up(engine)

            with allure.step('wait for ib-utils to be up'):
                wait_for_ib_utils_docker(engine)

            return ResultObj(result=True, info="System Is Ready", issue_type=IssueType.PossibleBug)

    @staticmethod
    def wait_for_cumulus_to_become_functional(engine, find_prompt_tries=60, find_prompt_delay=10):
        with allure.step('wait until the CLI is up'):
            wait_until_cli_is_up(engine)

        return ResultObj(result=True, info="System Is Ready", issue_type=IssueType.PossibleBug)

    @staticmethod
    def get_url(engine, command_opt='scp', file_full_path=''):
        if not engine or not engine.username:
            return ResultObj(result=False, info="No Engine")

        with allure.step('Trying to create url for {}'.format(engine.username)):

            with allure.step('check engine is reachable'):
                ssh_connection = ConnectionTool.create_ssh_conn(engine.ip, engine.username,
                                                                engine.password).verify_result()
                if not ssh_connection:
                    return ResultObj(result=False, info="{} is unreachable".format(engine.ip))

            with allure.step('generate url'):
                remote_url = '{}://{}:{}@{}{}'.format(command_opt, engine.username, engine.password, engine.ip,
                                                      file_full_path)

            return ResultObj(result=True, info=remote_url, returned_value=remote_url)


def ping_device(ip_add):
    try:
        return _ping_device(ip_add)
    except BaseException as ex:
        logging.error(str(ex))
        logging.info(f"ip address {ip_add} is unreachable")
        return False


@retry(Exception, tries=5, delay=10)
def _ping_device(ip_add):
    with allure.step(f"Ping device ip {ip_add}"):
        cmd = f"ping -c 3 {ip_add}"
        logging.info(f"Running cmd: {cmd}")
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        logging.info("output: " + str(output))
        logging.info("error: " + str(error))
        if " 0% packet loss" in str(output):
            logging.info("Reachable using ip address: " + ip_add)
            return True
        else:
            logging.error("Unreachable using ip address: " + ip_add)
            logging.info(f"ip address {ip_add} is unreachable")
            raise Exception(f"ip address {ip_add} is unreachable")


@retry(Exception, tries=60, delay=10)
def wait_for_system_table_to_exist(engine):
    output = DatabaseTool.sonic_db_cli_hgetall(engine=engine, asic="",
                                               db_name=DatabaseConst.STATE_DB_NAME,
                                               table_name='\"SYSTEM_READY|SYSTEM_STATE\"')
    if '(empty array)' in output:
        logger.info('Waiting to SYSTEM_STATUS table to be available')
        raise Exception("System is not ready yet")
    return True


@retry(Exception, tries=60, delay=2)
def wait_for_ib_utils_docker(engine):
    cmd_output = engine.run_cmd('docker ps --format \"table {{.Names}}\"')
    assert 'ib-utils' in cmd_output, "ib-utils still down"


@retry(Exception, tries=60, delay=10)
def wait_until_cli_is_up(engine):
    logger.info('Checking the status of nvued')
    output = engine.run_cmd('nv show system version')
    logger.info(output)
    if 'CLI is unavailable' in output:
        raise Exception("Waiting for NVUE to become functional")
