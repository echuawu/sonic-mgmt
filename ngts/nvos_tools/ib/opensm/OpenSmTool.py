import allure
import pytest
import logging
from ngts.nvos_tools.ib.Ib import Ib
from ngts.nvos_constants.constants_nvos import IbConsts
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.ResultObj import ResultObj

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
            return TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut)

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
            return TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut)

    @staticmethod
    def verify_open_sm_is_running():
        with allure.step("Check if OpenSM is running"):
            ib = Ib(None)
            sm_dict = Tools.OutputParsingTool.parse_json_str_to_dictionary(ib.sm.show()).verify_result()
            if IbConsts.SM_STATE not in sm_dict.keys():
                logger.info('state label is not exist')
                return

            if sm_dict[IbConsts.SM_STATE] == IbConsts.SM_STATE_ENABLE:
                logger.info('OpenSM is already enabled')
                return True

            else:
                logging.info("OpenSM is disabled")
                return False
