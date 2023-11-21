import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ApiType, ActionConsts
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import ImageConsts
from ngts.nvos_tools.system.Asic import Asic
logger = logging.getLogger()


class Firmware(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/firmware')
        self.asic = Asic(self)

    def _action(self, action_type, op_param="", expected_str="Action succeeded"):
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_firmware_image,
                                                            expected_str,
                                                            TestToolkit.engines.dut,
                                                            action_type, self.get_resource_path(),
                                                            op_param).get_returned_value()

    def action_fetch(self, url="", expected_str="Action succeeded"):
        with allure.step("Image fetch {url} ".format(url=url)):
            logging.info("Image fetch {url} system image".format(url=url))
            if TestToolkit.tested_api == ApiType.OPENAPI and expected_str == "Action succeeded":
                expected_str = 'File fetched successfully'
            return self._action(ActionConsts.FETCH, url, expected_str)

    def action_boot_next(self, partition_id, expected_str=''):
        with allure.step("Set image '{id}' to boot next".format(id=partition_id)):
            logging.info("Set image '{id}' to boot next".format(id=partition_id))
            return self._action(ActionConsts.BOOT_NEXT, partition_id, expected_str)

    def get_fw_image_field_values(self, field_names=[ImageConsts.ACTUAL_FIRMWARE, ImageConsts.INSTALLED_FIRMWARE]):
        output = OutputParsingTool.parse_json_str_to_dictionary(BaseComponent.show(self)).get_returned_value()
        values = {}
        for field_name in field_names:
            values[field_name] = output[ImageConsts.ASIC].get(field_name, "")
        return values
