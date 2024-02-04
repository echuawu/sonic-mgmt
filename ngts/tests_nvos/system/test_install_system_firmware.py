import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.system.Files import File
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_constants.constants_nvos import NvosConst, SystemConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime

logger = logging.getLogger()


@pytest.mark.checklist
@pytest.mark.system
def test_install_system_firmware(engines, test_name):
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
    fw_has_changed = False
    fw_file_name = "fw-QTM2-rel-31_2012_3008-EVB.mfa"
    fw_file = f"/auto/sw_system_project/NVOS_INFRA/verification_files/{fw_file_name}"
    new_fw_name = "31.2012.3008"
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
            with allure.step("fetch firmware file to switch"):
                player_engine = engines['sonic_mgmt']
                scp_path = 'scp://{}:{}@{}'.format(player_engine.username, player_engine.password, player_engine.ip)
                system.firmware.action_fetch(scp_path + fw_file)
                firmware_file = File(system.firmware.asic.files, fw_file_name)
                # firmware_file.action_file_install(op_param="")

                res_obj, duration = OperationTime.save_duration('install user FW', 'include reboot', test_name,
                                                                install_new_user_fw, system, new_fw_to_install, fae,
                                                                new_fw_name, actual_firmware, engines, test_name)
                assert OperationTime.verify_operation_time(duration, 'install user FW'), \
                    'Install user FW took more time than threshold value'

        with allure.step('Verify the firmware installed successfully'):
            verify_firmware_with_system_and_fae_cmd(system, fae, new_fw_name, new_fw_name)
            validate_all_asics_have_same_info()
            fw_has_changed = True

    finally:
        with allure.step("cleanup steps"):
            OperationTime.save_duration('install default fw', 'include reboot', test_name, install_image_fw,
                                        system, engines, test_name, fw_has_changed)

        with allure.step('Verify the firmware installed successfully'):
            verify_firmware_with_system_and_fae_cmd(system, fae, actual_firmware, actual_firmware)
            validate_all_asics_have_same_info()


def install_image_fw(system, engines, test_name, fw_has_changed):
    with allure.step("Install original system firmware file"):
        system.firmware.asic.set("default", "image", apply=True)
        NvueGeneralCli.save_config(engines.dut)

    with allure.step('Rebooting the dut after image installation'):
        logging.info("Rebooting dut")
        if fw_has_changed:
            res_obj, duration = OperationTime.save_duration('reboot with default FW installation', '', test_name,
                                                            system.reboot.action_reboot)
            res = res_obj
            assert OperationTime.verify_operation_time(duration, 'reboot with default FW installation'), \
                'Reboot with default FW installation took more time than threshold value'
        else:
            res = system.reboot.action_reboot()

        return res


def install_new_user_fw(system, new_fw_to_install, fae, new_fw_name, actual_firmware, engines, test_name):
    system.firmware.asic.action_install_fw("{}".format(new_fw_to_install))
    system.firmware.asic.set("default", "user", apply=True)

    with allure.step("Verify installed file can be found in show output"):
        verify_firmware_with_system_and_fae_cmd(system, fae, new_fw_name, actual_firmware)
        validate_all_asics_have_same_info()
        NvueGeneralCli.save_config(engines.dut)

    with allure.step('Rebooting the dut after image installation'):
        logging.info("Rebooting dut")
        res, duration = OperationTime.save_duration('reboot with new user FW', '',
                                                    test_name, system.reboot.action_reboot)
        assert OperationTime.verify_operation_time(duration, 'reboot with new user FW'), \
            'Reboot with new user FW took more time than threshold value'

    return res


def get_original_fw_path(engines, original_fw):
    fw_dir = "/auto/sw_system_project/MLNX_OS_INFRA/mlnx_os2/sx_mlnx_fw/"
    orig_fw_file = engines[NvosConst.SONIC_MGMT].run_cmd("ls {}| grep {}".format(fw_dir, original_fw))
    fw_path = fw_dir + orig_fw_file
    logger.info(" original fw path is: {}".format(fw_path))
    return fw_path


def verify_field_value_in_output_for_each_asic(output_dictionary, field, value):
    ValidationTool.verify_field_value_in_output(output_dictionary, field, value).verify_result()


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
    for asic in output_dictionary:
        verify_field_value_in_output_for_each_asic(output_dictionary[asic], "installed-firmware", installed_fw)
        verify_field_value_in_output_for_each_asic(output_dictionary[asic], "actual-firmware", actual_fw)
