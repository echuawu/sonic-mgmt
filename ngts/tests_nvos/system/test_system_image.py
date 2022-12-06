import logging
import pytest
import os
import allure
import string
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import ImageConsts, NvosConst
from ngts.constants.constants import InfraConst
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from infra.tools.redmine.redmine_api import *


logger = logging.getLogger()

PATH_TO_IMAGED_DIRECTORY = "/auto/sw_system_release/nos/nvos/"
PATH_TO_IMAGE_TEMPLATE = "{}/amd64/"


@pytest.mark.checklist
@pytest.mark.nvos_ci
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_show_system_image():
    """
    Show system image test

    Test flow:
    1. Run show system image
    2. Compare the current image value to the output from 'show system image current'
    3. Compare the output of 'show system image current' to 'show system version'
    4. Compare the output of 'show system image' to 'show system image installed'
    5. Compare the output of 'show system image' to 'show system image next'
    """
    system = System()
    with allure.step("Run show command to view system image"):
        logging.info("Run show command to view system image")
        show_output = system.image.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             [ImageConsts.CURRENT_IMG, ImageConsts.PARTITION1_IMG, ImageConsts.NEXT_IMG]).verify_result()
            logging.info("All expected fields were found")

        with allure.step("Validate the values exist"):
            assert output_dictionary[ImageConsts.CURRENT_IMG] is not None, "'{}' image can't be found the the output".format(ImageConsts.CURRENT_IMG)
            assert output_dictionary[ImageConsts.PARTITION1_IMG] is not None, "'{}' image can't be found the the output".format(ImageConsts.PARTITION1_IMG)
            assert output_dictionary[ImageConsts.NEXT_IMG] is not None, "'{}' image can't be found the the output".format(ImageConsts.NEXT_IMG)

    with allure.step("Run show command to view system image files"):
        logging.info("Run show command to view system image files ")
        show_output = system.image.files.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_system_image_rename(release_name):
    """
    Check the image rename cmd.
    Validate that install and delete commands will success with the new name
    and will fail with the old name.
    1. Fetch random image
    2. Rename image
    3. Install original image name, should fail
    4. Delete the original image name , should fail
    5. Install new image name , success
    6. Uninstall image
    7. Delete the new image name , success
    """
    system = System()
    original_images, _, original_image_partition, partition_id_for_new_image, images_to_install = \
        get_image_data_and_fetch_random_image_files(release_name, system)
    fetched_image = images_to_install[0]

    with allure.step("Rename image and verify"):
        new_name = RandomizationTool.get_random_string(20, ascii_letters=string.ascii_letters + string.digits)
        system.image.files.rename_and_verify(fetched_image, new_name)

    with allure.step("Install original image name, should fail"):
        logging.info("Install original image name: {}, should fail".format(fetched_image))
        system.image.files.action_file_install(fetched_image, "Action failed")

    with allure.step("Delete original image name, should fail"):
        logging.info("Delete original image name, should fail")
        system.image.files.delete_system_files([fetched_image], "File not found")

    with allure.step("Install new image name"):
        logging.info("Install new image name: {}".format(new_name))
        system.image.files.action_file_install(new_name)

    with allure.step("Verify installed image"):
        logging.info("Verify installed image, we should see the origin name and not the new name,"
                     "because the name is taken from the code it self and not from the file name")
        expected_show_images_output = original_images.copy()
        expected_show_images_output[ImageConsts.NEXT_IMG] = normalize_image_name(fetched_image)
        expected_show_images_output[partition_id_for_new_image] = expected_show_images_output[ImageConsts.NEXT_IMG]
        system.image.verify_show_images_output(expected_show_images_output)
    cleanup_test(system, original_images, original_image_partition, [new_name])


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_system_image_upload(engines, release_name):
    """
    Uploading image file to player and validate.
    1. Fetch random image
    2. Upload image to player
    3. Validate image uploaded to player
    4. Delete image file from player
    5. Delete image file from dut
    """
    system = System()
    _, _, _, _, image_names = get_image_data_and_fetch_random_image_files(release_name, system)
    image_name = image_names[0]
    upload_protocols = ['scp', 'sftp']
    player = engines['sonic_mgmt']

    with allure.step("Upload image to player {} with the next protocols : {}".format(player.ip, upload_protocols)):
        logging.info("Upload image to player {} with the next protocols : {}".format(player.ip, upload_protocols))
        for protocol in upload_protocols:

            with allure.step("Upload image to player with {} protocol".format(protocol)):
                logging.info("Upload image to player with {} protocol".format(protocol))
                upload_path = '{}://{}:{}@{}/tmp/{}'.format(protocol, player.username, player.password, player.ip, image_name)
                system.image.files.action_upload(image_name, upload_path)

            with allure.step("Validate file was uploaded to player and delete it"):
                logging.info("Validate file was uploaded to player and delete it")
                assert player.run_cmd(cmd='ls /tmp/ | grep {}'.format(image_name)), "Did not find the file with ls cmd"
                player.run_cmd(cmd='rm -f /tmp/{}'.format(image_name))

    with allure.step("Delete file from player"):
        logging.info("Delete file from player")
        system.image.files.delete_system_files([image_name])
        system.image.files.verify_show_files_output(unexpected_files=[image_name])


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_image_uninstall(release_name):
    """
     Will check the uninstall commands

    Test flow:
    1. Validate that uninstall with 1 image only will fail
    2. Fetch and install an images
    3. Validate that uninstall will fail (because one is the current and the other is next-boot)
    4. Set the original image to be booted next
    5. Validate that uninstall will success
    """
    image_uninstall_test(release_name, uninstall_force="")


@pytest.mark.checklist
@pytest.mark.simx
@pytest.mark.image
@pytest.mark.system
def test_image_uninstall_force(release_name):
    """
     Will check the uninstall force commands

    Test flow:
    1. Validate that uninstall force with 1 image only will fail
    2. Fetch and install force an images
    3. Validate that uninstall force success
    4. Set the original image to be booted next
    5. Validate that uninstall force will success
    """
    image_uninstall_test(release_name, uninstall_force="force")


def image_uninstall_test(release_name, uninstall_force=""):
    """
     Will check the uninstall commands
     for uninstall force command , the uninstall_force param need to get "force"

    Test flow:
    1. Validate that uninstall [force] with 1 image only will fail
    2. Fetch and install an images
    3. Validate that uninstall will fail (beause one is the current and the other is next-boot),
        but uninstall force success
        3.1. if we check the force command so we will install the new image again
    4. Set the original image to be booted next
    5. Validate that uninstall [force] will success
    """
    system = System()
    original_images, original_image, original_image_partition, partition_id_for_new_image, images_to_install = \
        get_image_data_and_fetch_random_image_files(release_name, system)
    fetched_image = images_to_install[0]

    with allure.step("{} uninstall image, while there is just 1 image- should fail".format(uninstall_force)):
        system.image.action_uninstall(params=uninstall_force, expected_str="Nothing to uninstall")
        system.image.verify_show_images_output(original_images)

    with allure.step("Install image and verify"):
        installed_images_output = install_image_and_verify(fetched_image, partition_id_for_new_image, original_images, system)

    with allure.step("{} uninstall images, while both partitions are used - should {}"
                     .format(uninstall_force, "success" if uninstall_force else "fail")):
        if uninstall_force:
            system.image.action_uninstall(params=uninstall_force)
            system.image.verify_show_images_output(original_images)

            with allure.step("Install image"):
                install_image_and_verify(fetched_image, partition_id_for_new_image, original_images, system)
        else:
            system.image.action_uninstall(expected_str="Not uninstalling. image set to boot-next")
            system.image.verify_show_images_output(installed_images_output)

    cleanup_test(system, original_images, original_image_partition, [fetched_image], uninstall_force)


def normalize_image_name(image_name):
    return image_name.replace("-amd64", "").replace(".bin", "")


def install_image_and_verify(image_name, partition_id, original_images, system):
    with allure.step("Installing image {}".format(image_name)):
        logging.info("Installing image '{}'".format(image_name))
        system.image.files.action_file_install(image_name)
    with allure.step("Verify installed image"):
        expected_show_images_output = original_images.copy()
        expected_show_images_output[ImageConsts.NEXT_IMG] = normalize_image_name(image_name)
        expected_show_images_output[partition_id] = expected_show_images_output[ImageConsts.NEXT_IMG]
        system.image.verify_show_images_output(expected_show_images_output)
        return expected_show_images_output


def get_list_of_directories(current_installed_img, starts_with=None):
    def mtime(f): return os.stat(os.path.join(PATH_TO_IMAGED_DIRECTORY, f)).st_mtime
    all_directories = list(sorted(os.listdir(PATH_TO_IMAGED_DIRECTORY), key=mtime))
    all_directories.reverse()
    return_directories = {}
    for directory in all_directories:
        temp_dir = PATH_TO_IMAGED_DIRECTORY + PATH_TO_IMAGE_TEMPLATE.format(directory)
        if os.path.isdir(temp_dir) and starts_with and directory.startswith(starts_with):
            logging.info("Searching for images in path: " + temp_dir)
            relevant_images = [f for f in os.listdir(temp_dir) if f.startswith("nvos-amd64-25.") and
                               current_installed_img.replace("nvos-25", "nvos-amd64-25") not in f]
            if relevant_images:
                return_directories[temp_dir] = relevant_images
        if len(return_directories) > 4:
            break
    return return_directories


def get_images_to_install(release_name, current_installed_img, images_amount=1):
    images_to_install = []
    with allure.step("Get list of images"):
        logging.info("Get list of images")
        relevant_directories = get_list_of_directories(current_installed_img, release_name)
        for directory, images_list in relevant_directories.items():
            images_to_install.append((images_list[0], directory + images_list[0]))
            logging.info("Selected image: " + directory + images_list[0])
            if len(images_to_install) == images_amount:
                break
    return images_to_install


def get_next_partition_id(partition_id):
    return ImageConsts.PARTITION2_IMG if partition_id == ImageConsts.PARTITION1_IMG else ImageConsts.PARTITION1_IMG


def cleanup_test(system, original_images, original_image_partition, fetched_image_files, uninstall_force=""):
    with allure.step("Set the original image to be booted next and verify"):
        system.image.boot_next_and_verify(original_image_partition)

    with allure.step("{} uninstall unused images and verify".format(uninstall_force)):
        system.image.action_uninstall(params=uninstall_force)
        system.image.verify_show_images_output(original_images)

    with allure.step("Delete all images that have been fetch during the test and verify"):
        system.image.files.delete_system_files(fetched_image_files)
        system.image.files.verify_show_files_output(unexpected_files=fetched_image_files)


def get_image_data(system):
    with allure.step("Save original installed image name"):
        original_images = system.image.get_image_field_values()
        original_image = original_images[ImageConsts.CURRENT_IMG]
        original_image_partition = system.image.get_image_partition(original_image, original_images)
        partition_id_for_new_image = get_next_partition_id(original_image_partition)
        logging.info("Original image: {}, partition: {}".format(original_image, original_image_partition))
        return original_images, original_image, original_image_partition, partition_id_for_new_image


def get_image_data_and_fetch_random_image_files(release_name, system, images_amount_to_fetch=1):
    original_images, original_image, original_image_partition, partition_id_for_new_image = get_image_data(system)

    with allure.step("Get {} available image files".format(images_amount_to_fetch)):
        images_to_install = get_images_to_install(release_name, original_image, images_amount_to_fetch)
        images_name = []
        for image_name, image_path in images_to_install:
            scp_path = 'scp://{}:{}@{}'.format(NvosConst.ROOT_USER, NvosConst.ROOT_PASSWORD,
                                               InfraConst.HTTP_SERVER.replace("http://", ""))
            with allure.step("Fetch an image {}".format(scp_path + image_path)):
                system.image.action_fetch(scp_path + image_path)
                images_name.append(image_name)
    return original_images, original_image, original_image_partition, partition_id_for_new_image, images_name
