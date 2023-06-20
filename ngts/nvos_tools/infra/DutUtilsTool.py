import logging
import time
from .ResultObj import ResultObj, IssueType
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from retry.api import retry_call
from ngts.nvos_constants.constants_nvos import ReadFromDataBase
import allure

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
                dummy_cmd = ''
                retry_call(engine.run_cmd, fargs=[dummy_cmd], tries=80, delay=2, logger=logger)

            if not should_wait_till_system_ready:
                return ResultObj(result=True, info="system is not ready yet")

            with allure.step('Waiting for switch to be ready'):
                logger.info("Waiting for switch to be ready")
                retry_call(engine.run_cmd, fargs=[''], tries=find_prompt_tries, delay=find_prompt_delay, logger=logger)
                result_obj = DutUtilsTool.wait_for_nvos_to_become_functional(engine=engine, find_prompt_delay=find_prompt_delay)

        return result_obj

    @staticmethod
    def wait_for_nvos_to_become_functional(engine, find_prompt_tries=600, find_prompt_delay=10):
        with allure.step('wait until the system is ready - check SYSTEM_STATE table'):
            result_obj = ResultObj(result=True, info="System Is Ready", issue_type=IssueType.PossibleBug)
            retry_call(f=DutUtilsTool._wait_for_system_table_to_exist, fargs=engine, tries=find_prompt_tries, delay=find_prompt_delay, logger=logger)
            if 'DOWN' in engine.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS):
                return ResultObj(result=False, info="THE SYSTEM IS NOT OK", issue_type=IssueType.PossibleBug)
            return result_obj

    @staticmethod
    def _wait_for_system_table_to_exist(engine):
        if 'UP' not in engine.run_cmd(ReadFromDataBase.READ_SYSTEM_STATUS):
            logger.info('Waiting to SYSTEM_STATUS table to be available')
            return False
        return True
