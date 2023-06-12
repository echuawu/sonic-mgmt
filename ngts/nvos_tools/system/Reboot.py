import allure
import logging
import time
import pytest
import os
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.constants.constants import InfraConst
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.scripts.check_and_store_sanitizer_dump import check_sanitizer_and_store_dump

logger = logging.getLogger()


class Reboot(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/reboot'
        self.parent_obj = parent_obj

    def get_expected_fields(self, device):
        return device.constants.system['reboot']

    def action_reboot(self, engine=None, params=""):
        with allure.step('Execute action for {resource_path}'.format(resource_path=self.get_resource_path())):
            if not engine:
                engine = TestToolkit.engines.dut

            start_time = time.time()
            res_obj = SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_reboot,
                                                      engine,
                                                      self.get_resource_path().replace('/reboot', ' '), params)
            end_time = time.time()
            duration = end_time - start_time

            with allure.step("Reboot takes: {} seconds".format(duration)):
                logger.info("Reboot takes: {} seconds".format(duration))

            NvueGeneralCli.wait_for_nvos_to_become_functional(engine)
            end_time = time.time()
            duration = end_time - start_time
            with allure.step("Reboot till system is functional takes: {} seconds".format(duration)):
                logger.info("Reboot till system is functional takes: {} seconds".format(duration))

            if pytest.is_sanitizer:
                dumps_folder = os.environ.get(InfraConst.ENV_LOG_FOLDER)
                check_sanitizer_and_store_dump(engine, dumps_folder, pytest.test_name)

            return res_obj
