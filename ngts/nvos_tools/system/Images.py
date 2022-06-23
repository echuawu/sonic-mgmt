import allure
import logging
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType, ActionConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
logger = logging.getLogger()


class Images(BaseComponent):
    image_id = ''

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/images/{image_id}'
        self.parent_obj = parent_obj

    def get_resource_path(self):
        self_path = self._resource_path.format(image_id=self.image_id).rstrip("/")
        return "{parent_path}{self_path}".format(
            parent_path=self.parent_obj.get_resource_path() if self.parent_obj else "", self_path=self_path)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /images/{image_id}")

    def _action(self, action_type, op_param=""):
        return SendCommandTool.execute_command_success_str(self.api_obj[TestToolkit.tested_api].action_image,
                                                           "Action succeeded",
                                                           TestToolkit.engines.dut,
                                                           action_type, "images", op_param).get_returned_value()

    def action_install(self, image_file_path):
        with allure.step("Install image '{path}'".format(path=image_file_path)):
            logging.info("Trying to install image '{path}'".format(path=image_file_path))
            return self._action(ActionConsts.INSTALL, image_file_path)

    def action_cleanup(self):
        with allure.step("Cleanup system images"):
            logging.info("Cleanup system images")
            return self._action(ActionConsts.CLEANUP)

    def action_uninstall(self, img_id):
        with allure.step("Uninstall system image with id: {id}".format(id=img_id)):
            logging.info("Uninstall system image with id: {id}".format(id=img_id))
            return self._action(ActionConsts.UNINSTALL, img_id)

    def action_boot_next(self, img_id):
        with allure.step("Set image '{id}' to boot next".format(id=img_id)):
            logging.info("Set image '{id}' to boot next".format(id=img_id))
            return self._action(ActionConsts.BOOT_NEXT, img_id)
