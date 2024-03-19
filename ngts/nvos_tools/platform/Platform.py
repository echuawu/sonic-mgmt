import logging
from typing import List
import requests

from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import ApiType, ImageConsts, OutputFormat, ActionConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.platform.Environment import Environment
from ngts.nvos_tools.platform.Hardware import Hardware
from ngts.nvos_tools.platform.Software import Software
from ngts.tools.test_utils import allure_utils as allure


logger = logging.getLogger()


class Platform(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli},
                               path='/platform')
        self.firmware = Firmware(self)
        self.environment = Environment(self)
        self.software = Software(self)
        self.hardware = Hardware(self)

    def set(self, op_param_name="", op_param_value=""):
        raise Exception("set is not implemented for /platform")

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /platform")


class Firmware(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj,
                               api={ApiType.NVUE: NvuePlatformCli, ApiType.OPENAPI: OpenApiPlatformCli},
                               path='/firmware')
        self.cpld = FaeCpldComponent(self, 'cpld')
        self.ssd = FaePlatformComponent(self, 'ssd')

    def install_bios_firmware(self, bios_image_path, device):
        with allure.step("installing bios firmware from {action_type}".format(action_type=bios_image_path)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_install_fae_bios_firmware,
                                                   TestToolkit.engines.dut, bios_image_path, self.get_resource_path(), device)


class FaePlatformComponent(BaseComponent):
    def __init__(self, parent_obj=None, component_name=None):
        BaseComponent.__init__(self, parent=parent_obj, path=f"/{component_name}")

    def show_files(self):
        """nv show fae platform firmware (bios|cpld|ssd) files"""
        return super().show(op_param='files')

    def show_files_as_list(self) -> List[str]:
        return OutputParsingTool.parse_show_files_to_names(self.show_files()).get_returned_value()

    def action_fetch(self, path, base_url='') -> ResultObj:
        """nv action fetch fae platform firmware (bios|cpld|ssd) <remote-url>"""
        url = (base_url or ImageConsts.SCP_PATH) + path
        return self.action(ActionConsts.FETCH, '', 'remote-url', url, expected_output='File fetched successfully')

    def action_install(self, filename, device, expect_reboot) -> ResultObj:
        """nv action install fae platform firmware (bios|cpld|ssd) files <file-name> [force]"""
        return self.action(ActionConsts.INSTALL, 'files ' + filename, 'force', expect_reboot=expect_reboot)

    def action_delete(self, filename) -> ResultObj:
        """nv action delete fae platform firmware (bios|cpld|ssd) files <file-name> [force]"""
        return self.action(ActionConsts.DELETE, 'files ' + filename, expected_output='File delete successfully')


class FaeCpldComponent(FaePlatformComponent):
    def action_install(self, filename, device, expect_reboot) -> ResultObj:
        # This override is necessary because cpld-fw installation is done in two steps (BURN then REFRESH), and
        # when running action-install on the REFRESH image the system immediately reboots and connection is lost.
        try:
            return super().action_install(filename, device, expect_reboot)
        except requests.exceptions.ConnectionError:
            if expect_reboot:
                logger.info(f"GET request failed as expected")
                return ResultObj(True)
            else:
                raise
