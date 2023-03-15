import logging
import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import NvosConst, SystemConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()


@pytest.mark.checklist
@pytest.mark.system
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
    system = System()
    fae = Fae()
    fw_file = "/auto/sw_system_project/MLNX_OS_INFRA/mlnx_os2/sx_mlnx_fw/fw-QTM2-rel-31_2010_4026-EVB.mfa"
    new_fw_name = "31.2010.4026"
    new_fw_to_install = fw_file.split("/")[-1]
    logging.info("using {} fw file".format(fw_file))

    with allure.step("Check actual firmware value"):
        show_output = fae.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        assert output_dictionary and len(output_dictionary.keys()) > 0, "asic list is empty"

        first_asic_name = list(output_dictionary.keys())[0]
        actual_firmware = output_dictionary[first_asic_name]["actual-firmware"]
        logging.info("Original actual firmware - " + actual_firmware)
        installed_firmware = output_dictionary[first_asic_name]["installed-firmware"]
        logging.info("Original actual installed firmware - " + installed_firmware)
        validate_all_asics_have_same_info()

    try:
        with allure.step("Install system firmware file - " + fw_file):
            with allure.step("Copy firmware file to switch"):
                player_engine = engines['sonic_mgmt']
                player_engine.upload_file_using_scp(dest_username=SystemConsts.DEFAULT_USER_ADMIN,
                                                    dest_password=engines.dut.password,
                                                    dest_folder="/tmp/",
                                                    dest_ip=engines.dut.ip,
                                                    local_file_path=fw_file)

            system.firmware.action_install_fw("/tmp/{}".format(new_fw_to_install))
            system.firmware.set("default", "user", apply=True)

        with allure.step("Verify installed file can be found in show output"):
            verify_firmware_with_system_and_fae_cmd(system, fae, new_fw_name, actual_firmware)
            validate_all_asics_have_same_info()
            NvueGeneralCli.save_config(engines.dut)

        with allure.step('Rebooting the dut after image installation'):
            logging.info("Rebooting dut")
            system.reboot.action_reboot()

        with allure.step('Verify the firmware installed successfully'):
            verify_firmware_with_system_and_fae_cmd(system, fae, new_fw_name, new_fw_name)
            validate_all_asics_have_same_info()

    finally:
        with allure.step("Install original system firmware file"):
            system.firmware.set("default", "image", apply=True)
            NvueGeneralCli.save_config(engines.dut)

        with allure.step('Rebooting the dut after image installation'):
            logging.info("Rebooting dut")
            system.reboot.action_reboot()

        with allure.step('Verify the firmware installed successfully'):
            verify_firmware_with_system_and_fae_cmd(system, fae, actual_firmware, actual_firmware)
            validate_all_asics_have_same_info()


def get_original_fw_path(engines, original_fw):
    fw_dir = "/auto/sw_system_project/MLNX_OS_INFRA/mlnx_os2/sx_mlnx_fw/"
    orig_fw_file = engines[NvosConst.SONIC_MGMT].run_cmd("ls {}| grep {}".format(fw_dir, original_fw))
    fw_path = fw_dir + orig_fw_file
    logger.info(" original fw path is: {}".format(fw_path))
    return fw_path


def verify_field_value_in_output_for_each_asic(output_dictionary, field, value):
    for asic_name in output_dictionary:
        ValidationTool.verify_field_value_in_output(output_dictionary[asic_name], field, value).verify_result()


def validate_all_asics_have_same_info():
    show_output = Fae().firmware.asic.show()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
    assert output_dictionary and len(output_dictionary.keys()) > 0, "asic list is empty"

    if len(output_dictionary.keys()) > 1:
        with allure.step("Validate all the ASICs have the same info"):
            logging.info("Validate all the ASICs have the same info")
            asic_info = list(output_dictionary.values())[0]
            for asic in output_dictionary.keys():
                assert asic_info == output_dictionary[asic], "ASICs are different"


def verify_firmware_with_system_and_fae_cmd(system, fae, installed_fw, actual_fw):
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(system.firmware.asic.show()).get_returned_value()
    verify_field_value_in_output_for_each_asic(output_dictionary, "installed-firmware", installed_fw)
    verify_field_value_in_output_for_each_asic(output_dictionary, "actual-firmware", actual_fw)
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(
        fae.firmware.asic.show()).get_returned_value()
    verify_field_value_in_output_for_each_asic(output_dictionary, "installed-firmware", installed_fw)
    verify_field_value_in_output_for_each_asic(output_dictionary, "actual-firmware", actual_fw)
