import allure
import logging
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, ActionConsts
from ngts.nvos_constants.constants_nvos import ImageConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.Files import Files
logger = logging.getLogger()


class Image(BaseComponent):

    def __init__(self, parent_obj):
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/image'
        self.parent_obj = parent_obj
        self.files = Files(self)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /image")

    def _action(self, action_type, op_param="", expected_str="Action succeeded"):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_image,
                                                            expected_str,
                                                            TestToolkit.engines.dut,
                                                            action_type, self.get_resource_path(), op_param).get_returned_value()

    def action_install(self, params="", expected_str=""):
        with allure.step("Install {params} system image".format(params=params)):
            logging.info("Install {params} system image".format(params=params))
            return self._action(ActionConsts.INSTALL, params, expected_str)

    def action_uninstall(self, params="", expected_str=""):
        with allure.step("Uninstall {params} system image".format(params=params)):
            logging.info("Uninstall {params} system image".format(params=params))
            return self._action(ActionConsts.UNINSTALL, params, expected_str)

    def action_fetch(self, url="", expected_str="Action succeeded"):
        with allure.step("Image fetch {url} ".format(url=url)):
            logging.info("Image fetch {url} system image".format(url=url))
            return self._action(ActionConsts.FETCH, url, expected_str)

    def action_boot_next(self, partition_id, expected_str=''):
        with allure.step("Set image '{id}' to boot next".format(id=partition_id)):
            logging.info("Set image '{id}' to boot next".format(id=partition_id))
            return self._action(ActionConsts.BOOT_NEXT, partition_id, expected_str)

    def get_image_field_value(self, field_name):
        output = OutputParsingTool.parse_json_str_to_dictionary(BaseComponent.show(self)).get_returned_value()
        if field_name in output.keys():
            return output[field_name]
        return None

    def get_image_field_values(self, field_names=[ImageConsts.NEXT_IMG, ImageConsts.CURRENT_IMG, ImageConsts.PARTITION1_IMG,
                                                  ImageConsts.PARTITION2_IMG]):
        output = OutputParsingTool.parse_json_str_to_dictionary(BaseComponent.show(self)).get_returned_value()
        values = {}
        for field_name in field_names:
            if field_name in output.keys():
                values[field_name] = output[field_name]
            else:
                values[field_name] = ""
        return values

    def get_image_partition(self, image_name, images_dictionary={}):
        images_dictionary = images_dictionary if images_dictionary else self.get_image_field_values()
        partition = None
        if image_name == images_dictionary[ImageConsts.PARTITION1_IMG]:
            partition = ImageConsts.PARTITION1_IMG
        elif image_name == images_dictionary[ImageConsts.PARTITION2_IMG]:
            partition = ImageConsts.PARTITION2_IMG
        return partition

    def boot_next_and_verify(self, partition_id):
        self.action_boot_next(partition_id)
        with allure.step("Verifying the boot next image updated successfully"):
            images = self.get_image_field_values()
            assert images[ImageConsts.NEXT_IMG] == images[partition_id], "Failed to set the new image to boot next"

    def verify_show_images_output(self, expected_keys_values):
        output = self.get_image_field_values()
        for field, value in expected_keys_values.items():
            assert field in output.keys(), field + " can't be found int the output"
            assert value == output[field], "The value of {} is not {}".format(field, value)
