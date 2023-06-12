import allure

from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_constants.constants_nvos import ApiType, StatsConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tools.test_utils.allure_utils import step
from ngts.nvos_tools.system.Files import Files


class Stats(BaseComponent):
    category = None
    files = None

    def __init__(self, parent_obj, devices_dut):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/stats'
        self.parent_obj = parent_obj
        self.category = StatsCategory(self, devices_dut)
        self.files = Files(self)


class StatsCategory(BaseComponent):
    categoryName = {}

    def __init__(self, parent_obj, devices_dut):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/category'
        self.parent_obj = parent_obj
        if devices_dut:
            for name in devices_dut.CATEGORY_LIST:
                self.categoryName.update({name: StatsCategoryName(self, name)})
            self.categoryName.update(
                {StatsConsts.INVALID_CATEGORY_NAME: StatsCategoryName(self, StatsConsts.INVALID_CATEGORY_NAME)})
            self.categoryName.update(
                {StatsConsts.ALL_CATEGORIES: StatsCategoryName(self, StatsConsts.ALL_CATEGORIES)})


class StatsCategoryName(BaseComponent):
    def __init__(self, parent_obj, resource):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/{resource}'.format(resource=resource)
        self.parent_obj = parent_obj

    def action_general(self, action_str):
        with step("Run system stats category action '{action_type}'".format(action_type=action_str)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_general,
                                                   TestToolkit.engines.dut, action_str, self.get_resource_path())
