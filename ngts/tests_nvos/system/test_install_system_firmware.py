import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.checklist
def test_install_system_firmware(engines):
    """
    Install system firmware test

    Test flow:
    1. Install system firmware
    2. Make sure the installed firmware exist in 'installed-firmware'
    3. Reboot the system
    4. Verify the firmware is updated successfully
    5. Install the original firmware
    """
    with allure.step("Create System object"):
        system = System()

    fw_file = ""
    fw_file_name = ""
    original_fw_path = ""
    logging.info("using {} fw file".format(fw_file))

    with allure.step("Check actual firmware value"):
        show_output = system.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert output_dictionary and len(output_dictionary.keys()) > 0, "asic list is empty"

        first_asic_name = list(output_dictionary.keys())[0]
        with allure.step("Check actual firmware value"):
            logging.info("Verify all expected fields are presented in the output")
            ValidationTool.verify_field_exist_in_json_output(output_dictionary[first_asic_name], ["actual-firmware", "installed-firmware"]
                                                             ).verify_result()

        actual_firmware = output_dictionary[first_asic_name]["actual-firmware"]
        logging.info("Original actual firmware - " + actual_firmware)
        installed_firmware = output_dictionary[first_asic_name]["installed-firmware"]
        logging.info("Original actual installed firmware - " + installed_firmware)

    with allure.step("Install system firmware file - " + fw_file):
        system.firmware.action_install(fw_file)

    with allure.step("Verify installed file can be found in show output"):
        show_output = system.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary[first_asic_name], "installed-firmware",
                                                    fw_file_name)

    with allure.step('Rebooting the dut after image installation'):
        logging.info("Rebooting dut")
        system.reboot.action_reboot()

    with allure.step('Verify the firmware installed successfully'):
        show_output = system.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary[first_asic_name], "actual-firmware",
                                                    fw_file_name)

    with allure.step("Install original system firmware file - " + original_fw_path):
        system.firmware.action_install(original_fw_path)

    with allure.step('Rebooting the dut after image installation'):
        logging.info("Rebooting dut")
        system.reboot.action_reboot()

    with allure.step('Verify the firmware installed successfully'):
        show_output = system.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_value_in_output(output_dictionary[first_asic_name], "actual-firmware",
                                                    actual_firmware)
