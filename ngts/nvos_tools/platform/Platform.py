from ngts.cli_wrappers.nvue.nvue_platform_clis import NvuePlatformCli
from ngts.cli_wrappers.openapi.openapi_platform_clis import OpenApiPlatformCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.platform.Environment import Environment
from ngts.nvos_tools.platform.Hardware import Hardware
from ngts.nvos_tools.platform.Software import Software
from ngts.tools.test_utils import allure_utils as allure


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

    def install_bios_firmware(self, bios_image_path):
        with allure.step("installing bios firmware from {action_type}".format(action_type=bios_image_path)):
            return SendCommandTool.execute_command(self.api_obj[TestToolkit.tested_api].action_install_fae_bios_firmware,
                                                   TestToolkit.engines.dut, bios_image_path, self.get_resource_path())
