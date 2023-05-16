import allure
import logging

from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType, StatsConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool


class Stats(BaseComponent):
    category = None
    files = None

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/stats'
        self.parent_obj = parent_obj
        self.category = StatsCategory(self)
        self.files = StatsFiles(self)


class StatsCategory(BaseComponent):
    categoryName = {}

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/category'
        self.parent_obj = parent_obj
        # for name in TestToolkit.engines.dut.CATEGORY_LIST:
        for name in StatsConsts.CATEGORY_LIST:
            self.categoryName.update({name: StatsCategoryName(self, name)})
        self.categoryName.update(
            {StatsConsts.INVALID_CATEGORY_NAME: StatsCategoryName(self, StatsConsts.INVALID_CATEGORY_NAME)})


class StatsCategoryName(BaseComponent):
    def __init__(self, parent_obj, resource):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{resource}'.format(resource=resource)
        self.parent_obj = parent_obj

    def action_clear(self):
        with allure.step("Clear system stats"):
            logging.info("Clear system stats")
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_clear,
                                                   TestToolkit.engines.dut, self.get_resource_path())


class StatsFiles(BaseComponent):
    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/files'
        self.parent_obj = parent_obj

    def action_delete(self, file_name):
        with allure.step("Delete system stats file"):
            logging.info("Delete system stats file")
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_delete,
                                                   TestToolkit.engines.dut, self.get_resource_path(), file_name)

    def action_generate(self, file_name):
        with allure.step("Generate system stats file"):
            logging.info("Generate system stats file")
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_generate_files,
                                                   TestToolkit.engines.dut, self.get_resource_path(), file_name)

    def action_upload(self, upload_path, file_name):
        with allure.step("Upload {file} to '{path}".format(file=file_name, path=upload_path)):
            logging.info("Upload {file} to '{path}".format(file=file_name, path=upload_path))
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_upload,
                                                   TestToolkit.engines.dut, self.get_resource_path(),
                                                   file_name, upload_path)
