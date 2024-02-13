import logging
import pytest
from ngts.tools.test_utils import allure_utils as allure
import string
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.system.Files import File
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import ImageConsts
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_constants.constants_nvos import PlatformConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()


@pytest.mark.checklist
@pytest.mark.nvos_ci
@pytest.mark.system
def test_show_system_firmware(devices):
    """
    Show system firmware test

    Test flow:
    1. Run show system firmware
    2. Make sure that all required fields exist
    3. Run show system firmware asic
    4. Compare the output results to the results of show system firmware
    5. Run show system firmware asic <id>
    6. Compare the output results to the results of show system firmware
    """
    validate_show_firmware(devices, is_fae_cmd=False)


@pytest.mark.checklist
@pytest.mark.system
def test_show_fae_firmware(devices):
    """
    Show system firmware test

    Test flow:
    1. Run show fae firmware
    2. Make sure that all required fields exist
    3. Run show fae firmware asic
    4. Compare the output results to the results of show system firmware
    """
    validate_show_firmware(devices, is_fae_cmd=True)


def validate_show_firmware(devices, is_fae_cmd=False):
    system_or_fae_str = "fae" if is_fae_cmd else "system"
    system_or_fae_obj = Fae() if is_fae_cmd else System()
    with allure.step("Run show command to view {} firmware".format(system_or_fae_str)):
        logging.info("Run show command to view {} firmware".format(system_or_fae_str))
        show_output = system_or_fae_obj.firmware.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             ["asic", "auto-update", "default"]).verify_result()
            assert output_dictionary["asic"], "'asic' field is empty in show system firmware output"

            with allure.step("Validate asic amount"):
                expected_asic_amount = len(devices.dut.device_list) - 1 if is_fae_cmd else 6
                assert len(output_dictionary["asic"]) == expected_asic_amount, \
                    "Unexpected num of ASIC\n Expected : {}\n but got {}".format(
                    expected_asic_amount, len(output_dictionary["asic"]))

            with allure.step("Validate asic fields"):
                verify_asic_fields(output_dictionary["asic"], is_fae_cmd)

        asic_list = output_dictionary["asic"]

    with allure.step("Run show {} firmware asic".format(system_or_fae_str)):
        logging.info("Run show {} firmware asic".format(system_or_fae_str))
        show_output = system_or_fae_obj.firmware.asic.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate asic fields"):
            verify_asic_fields(output_dictionary, is_fae_cmd)

        with allure.step("Compare asic names in outputs"):
            compare_asic_names(asic_list, output_dictionary)

        with allure.step("Compare current output to the output from 'show {} firmware".format(system_or_fae_str)):
            if is_fae_cmd:
                for asic_name, asic_prop in output_dictionary.items():
                    compare_asic_fields(asic_list[asic_name], asic_prop)


@pytest.mark.checklist
@pytest.mark.system
def test_set_unset_system_firmware_auto_update():
    """
    set/unset system firmware auto update test

    Test flow:
    1. Disable firmware auto-update and make sure the configuration applied successfully
    2. Enable firmware auto-update and make sure the configuration applied successfully
    3. Disable firmware auto-update and make sure the configuration applied successfully
    4. Unset firmware auto-update and make sure the configuration is updated to default (enable)
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Disable firmware auto-update"):
        set_auto_update(system, "disabled")

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firmware_value(system, "auto-update", "disabled")

    with allure.step("Enable firmware auto-update"):
        set_auto_update(system, "enabled")

    with allure.step("Verify the configuration applied successfully - auto-update enabled"):
        verify_firmware_value(system, "auto-update", "enabled")

    with allure.step("Disable firmware auto-update"):
        set_auto_update(system, "disabled")

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firmware_value(system, "auto-update", "disabled")

    with allure.step("Unset auto-update"):
        unset_auto_update(system)

    with allure.step("Verify the configuration applied successfully - auto-update disabled"):
        verify_firmware_value(system, "auto-update", "enabled")


@pytest.mark.checklist
@pytest.mark.system
def test_set_unset_system_firmware_default(engines):
    """
    set/unset system firmware default test

    Test flow:
    1. Set firmware default to 'user' and make sure the configuration applied successfully
    2. Set firmware default to 'image' and make sure the configuration applied successfully
    4. Set firmware default to 'user' and make sure the configuration applied successfully
    3. Unset firmware default and make sure the configuration is updated to default (image)
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Set firmware default to 'user'"):
        set_firmware_default(system, "user")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firmware_value(system, "default", "user")

    with allure.step("Set firmware default to 'image'"):
        set_firmware_default(system, "image")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firmware_value(system, "default", "image")

    with allure.step("Set firmware default to 'user'"):
        set_firmware_default(system, "user")

    with allure.step("Verify the configuration applied successfully - firmware default is user"):
        verify_firmware_value(system, "default", "user")

    with allure.step("Unset firmware default"):
        unset_firmware_default(system)

    with allure.step("Verify the configuration applied successfully - firmware default is image"):
        verify_firmware_value(system, "default", "image")


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_system_firmware_image_rename(engines, devices, topology_obj):
    """
    Check the image rename cmd.
    Validate that install and delete commands will success with the new name
    and will fail with the old name.
    1. Fetch random image, fetch image
    2. Rename image without mfa ending
    3. Install original image name , should fail
    4. Install original image new name , should success
    5. Delete the original image name , should fail
    6. Install new image name , success
    7. Uninstall image
    8. Delete the new image name , success
    """
    system = System()
    dut = devices.dut
    original_images, original_image, fetched_image, default_firmware = \
        get_image_data_and_fetch_random_image_files(system, dut, topology_obj)
    fetched_image_file = File(system.firmware.asic.files, fetched_image)
    player = engines['sonic_mgmt']
    with allure.step("Rename image without mfa ending"):
        system.firmware.asic.action_fetch(url="scp://{}:{}@{}{}/{}".format(player.username, player.password, player.ip, PlatformConsts.FM_PATH, fetched_image))

    with allure.step("Rename image and verify"):
        new_name = RandomizationTool.get_random_string(20, ascii_letters=string.ascii_letters + string.digits)
        fetched_image_file.action_rename(new_name, expected_str="", rewrite_file_name=False)

    with allure.step("Rename already exist image and verify"):
        fetched_image_file.action_rename(new_name, expected_str="already exists")

    with allure.step("Install original image name, should fail"):
        logging.info("Install original image name: {}, should fail".format(fetched_image))
        system.firmware.asic.action_install_fw(fetched_image, "Action failed")

    with allure.step("Delete original image name, should fail"):
        logging.info("Delete original image name, should fail")
        system.firmware.asic.files.delete_system_files([fetched_image], "File not found")

    try:
        with allure.step("Install new image name"):
            logging.info("Install new image name: {}".format(new_name))
            system.firmware.asic.action_install_fw(new_name, "Action succeeded")

    finally:
        set_firmware_default(system, "image")


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_system_firmware_image_upload(engines, devices, topology_obj):
    """
    Uploading image file to player and validate.
    1. Fetch random image
    2. Upload image to player
    3. Validate image uploaded to player
    4. Delete image file from player
    5. Delete image file from dut
    """
    system = System()
    dut = devices.dut
    original_images, original_image, fetched_image, _ = get_image_data_and_fetch_random_image_files(system, dut, topology_obj)
    upload_protocols = ['scp', 'sftp']
    player = engines['sonic_mgmt']
    image_file = File(system.firmware.asic.files, fetched_image)

    with allure.step("Upload image to player {} with the next protocols : {}".format(player.ip, upload_protocols)):
        logging.info("Upload image to player {} with the next protocols : {}".format(player.ip, upload_protocols))

        for protocol in upload_protocols:
            with allure.step("Upload image to player with {} protocol".format(protocol)):
                logging.info("Upload image to player with {} protocol".format(protocol))
                upload_path = '{}://{}:{}@{}/tmp/{}'.format(protocol, player.username, player.password, player.ip, fetched_image)
                image_file.action_upload(upload_path, expected_str='File upload successfully')

            with allure.step("Validate file was uploaded to player and delete it"):
                logging.info("Validate file was uploaded to player and delete it")
                assert player.run_cmd(cmd='ls /tmp/ | grep {}'.format(fetched_image)), "Did not find the file with ls cmd"
                player.run_cmd(cmd='rm -f /tmp/{}'.format(fetched_image))

    with allure.step("Delete file from player"):
        logging.info("Delete file from player")
        system.firmware.asic.files.delete_system_files([fetched_image])
        system.firmware.asic.files.verify_show_files_output(unexpected_files=[fetched_image])


def set_firmware_default(system, value):
    logging.info("Setting firmware default to '{}'".format(value))
    system.firmware.asic.set("default", value)
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def unset_firmware_default(system):
    logging.info("Unset firmware default")
    system.firmware.asic.unset("default")
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def verify_firmware_value(system, field_name, expected_value):
    logging.info("Verify the configuration applied successfully")
    show_output = system.firmware.asic.show()
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
    ValidationTool.verify_field_value_in_output(output_dictionary, field_name, expected_value).verify_result()


def unset_auto_update(system):
    logging.info('unset firmware auto-update')
    system.firmware.asic.unset("auto-update")
    TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(TestToolkit.engines.dut, True)


def set_auto_update(system, value):
    logging.info('{} firmware asic auto-update'.format(value))
    system.firmware.asic.set("auto-update", value, apply=True)


def verify_asic_fields(asic_dictionary, is_fae_cmd):
    with allure.step("Validate asic fields"):
        logging.info("Verify all expected asic fields are presented in the output")
        asic_fields = ["actual-firmware", "installed-firmware", "part-number", "type"]
        if is_fae_cmd:
            for asic_name, asic_prop in asic_dictionary.items():
                ValidationTool.verify_field_exist_in_json_output(asic_prop, asic_fields).verify_result()
        else:
            asic_fields.extend(['auto-update', 'default'])
            ValidationTool.verify_field_exist_in_json_output(asic_dictionary, asic_fields).verify_result()
    logging.info("All expected fields were found")


def compare_asic_names(first_dictionary, second_dictionary):
    logging.info("Compare asic names")
    assert set(first_dictionary.keys()) == set(second_dictionary.keys()), "asic lists are not equal"


def compare_asic_fields(first_dictionary, second_dictionary):
    logging.info("Compare asic fields")
    ValidationTool.compare_dictionaries(first_dictionary, second_dictionary).verify_result()


def get_image_data_and_fetch_random_image_files(system, dut, topology_obj, images_amount_to_fetch=1):
    original_images, original_image, default_firmware = get_image_data(system, dut)

    with allure.step("Get {} available image files".format(images_amount_to_fetch)):
        asic_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific'][
            'chip_type']
        image_to_fetch = '{}fw-{}-'.format(PlatformConsts.FM_PATH, asic_type) + \
                         ImageConsts.FW_STABLE_VERSION
        image_name = 'fw-{}-'.format(asic_type) + ImageConsts.FW_STABLE_VERSION
        with allure.step("Fetch an image {}".format(ImageConsts.SCP_PATH + image_to_fetch)):
            system.firmware.asic.action_fetch(ImageConsts.SCP_PATH + image_to_fetch)
    return original_images, original_image, image_name, default_firmware


def get_image_data(system, dut):
    with allure.step("Save original installed image name"):
        original_images = system.firmware.get_fw_image_field_values()
        original_image = original_images[ImageConsts.ACTUAL_FIRMWARE]
        if dut.asic_type == "Quantum2":
            default_firmware = 'fw-QTM2.mfa'
        elif dut.asic_type == "Quantum":
            default_firmware = 'fw-QTM.mfa'
        else:
            default_firmware = 'fw-SIB2.mfa'
        logging.info("Actual firmware: {}".format(original_image))
        return original_images, original_image, default_firmware
