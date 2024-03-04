import pytest
import time
import logging
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_constants.constants_nvos import IbConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.tools.test_utils import allure_utils as allure
from retry import retry

logger = logging.getLogger()


class OpenSmTool:

    @staticmethod
    def start_open_sm(engine):
        """
        Start open sm if it's not running
        """
        ib = Ib(None)
        if OpenSmTool.verify_open_sm_is_running():
            return ResultObj(True, returned_value='opensm is already enabled')

        with allure.step("start OpenSM"):
            ib.sm.set(IbConsts.SM_STATE, IbConsts.SM_STATE_ENABLE)
            output = TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engine=TestToolkit.engines.dut,
                                                                                 ask_for_confirmation=True)
            if "applied" not in output:
                return ResultObj(False, "Failed to start openSM")

            _wait_until_sm_is_running(ib)
            res = OpenSmTool.verify_open_sm_is_running()
            return ResultObj(res, "Failed to start openSM")

    @staticmethod
    def stop_open_sm(engine):
        """
        Stop open sm if it's running
        """
        ib = Ib(None)
        if not OpenSmTool.verify_open_sm_is_running():
            return ResultObj(True, returned_value='opensm is already disabled')

        with allure.step("Stop OpenSM"):
            ib.sm.set(IbConsts.SM_STATE, IbConsts.SM_STATE_DISABLE)
            output = TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engine=TestToolkit.engines.dut,
                                                                                 ask_for_confirmation=True)
            return ResultObj("applied" in output, "Failed to start openSM")

    @staticmethod
    def verify_open_sm_is_running():
        with allure.step("Check if OpenSM is running"):
            ib = Ib(None)
            sm_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
            if IbConsts.SM_STATE not in sm_dict.keys():
                logger.info('state label is not exist')
                return

            if sm_dict[IbConsts.SM_STATE] == IbConsts.SM_STATE_ENABLE:
                logger.info('OpenSM is already enabled')
                return True

            else:
                logging.info("OpenSM is disabled")
                return False

    @staticmethod
    def start_open_sm_on_server(engines):
        """
        Start open sm if it's not running
        """
        if not hasattr(engines, "ha"):
            logging.warning("HA can't be found in topology")
            return ResultObj(False, "HA can't be found in topology")

        is_running, port_name = OpenSmTool.is_sm_running_on_server(engines)

        if is_running:
            logging.info("Open SM is already running")
            return ResultObj(True, "Open SM is already running")

        with allure.step("Get GUID to start OpenSM"):
            output = engines.ha.run_cmd("ibstat {}".format(port_name))
            guid = ''
            for line in output.splitlines():
                if "System image GUID" in line:
                    guid = line.split(":")[1]
                    logging.info("GUID: " + guid)
                    break
            if not guid:
                return ResultObj(False, "Failed to find GUID to start OpenSM")

        with allure.step("Start OpenSM"):
            engines.ha.run_cmd("opensm -g {} -B".format(guid))
            time.sleep(5)

        with allure.step("Verify OpenSM is running"):
            return ResultObj(OpenSmTool.verify_open_sm_is_running_on_server(engines), "Failed to start OpenSM")

    @staticmethod
    def stop_open_sm_on_server(engines):
        if not hasattr(engines, "ha"):
            logging.warning("HA can't be found in topology")
            return ResultObj(False, "HA can't be found in topology")

        is_running, port_name = OpenSmTool.is_sm_running_on_server(engines)

        if not is_running:
            logging.info("Open SM is not running")
            return ResultObj(True, "Open SM is not running")

        with allure.step("Get opensm process ids to stop"):
            output = engines.ha.run_cmd(f"ps aux | grep opensm")
            lines = [line for line in output.split('\n') if 'grep' not in line]
            if not lines:
                return ResultObj(True, "No opensm processes")

        with allure.step("Stop open sm process"):
            process_ids = [line.split()[1] for line in lines]
            cmd = "sudo kill -9"
            for process_id in process_ids:
                cmd += f" {process_id}"
            output = engines.ha.run_cmd(cmd)
            return ResultObj(True, info=output)

    @staticmethod
    def is_sm_running_on_server(engines):
        with allure.step("Check if OpenSM is running on a server"):
            output = engines.ha.run_cmd("ibdev2netdev")
            is_running = "(Up)" in output
            port_name = output.split()[0]
            return is_running, port_name

    @staticmethod
    def verify_open_sm_is_running_on_server(engines):
        is_running, port_name = OpenSmTool.is_sm_running_on_server(engines)
        return is_running


@retry(Exception, tries=25, delay=4)
def _wait_until_sm_is_running(ib):
    sm_dict = OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
    assert sm_dict[IbConsts.IS_RUNNING] == IbConsts.IS_RUNNING_YES
