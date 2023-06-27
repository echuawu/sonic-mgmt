import logging
import time
from .ResultObj import ResultObj, IssueType
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from retry.api import retry_call, retry
from ngts.nvos_constants.constants_nvos import ReadFromDataBase, SystemConsts
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


class DutUtilsTool:

    @staticmethod
    def reload(engine, command, find_prompt_tries=80, find_prompt_delay=2, should_wait_till_system_ready=True):
        """

        :param should_wait_till_system_ready: if True then we will wait till the system is ready, if false then we only will wait till we can re-connect to the system
        :param engine:
        :param command:
        :param find_prompt_tries:
        :param find_prompt_delay:
        :return:
        """
        with allure.step('Reload the system with {} command, and wait till system is ready'):
            engine.send_config_set(command, exit_config_mode=False, cmd_verify=False)

            with allure.step('Waiting for switch shutdown after reload command'):
                logger.info("Waiting for switch shutdown after reload command")
                check_port_status_till_alive(False, engine.ip, engine.ssh_port)
                engine.disconnect()

            if not should_wait_till_system_ready:
                return ResultObj(result=True, info="system is not ready yet")

            with allure.step('Waiting for switch to be ready'):
                logger.info("Waiting for switch to be ready")
                retry_call(engine.run_cmd, fargs=[''], tries=find_prompt_tries, delay=find_prompt_delay, logger=logger)
                result_obj = DutUtilsTool.wait_for_nvos_to_become_functional(engine=engine, find_prompt_delay=find_prompt_delay)

        return result_obj

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

            # after merge we need to check if '(empty array)' in output then table is missed
            if SystemConsts.STATUS_DOWN in engine.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS):
                return ResultObj(result=False, info="THE SYSTEM IS NOT OK", issue_type=IssueType.PossibleBug)

            with allure.step('wait until the CLI is up'):
                time.sleep(5)

            return ResultObj(result=True, info="System Is Ready", issue_type=IssueType.PossibleBug)


@retry(False, tries=60, delay=10)
def wait_for_system_table_to_exist(engine):
    if '(empty array)' in engine.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS):
        logger.info('Waiting to SYSTEM_STATUS table to be available')
        return False
    return True
