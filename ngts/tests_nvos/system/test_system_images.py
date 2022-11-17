import logging
import pytest
import os
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.constants.constants import InfraConst
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from infra.tools.redmine.redmine_api import *

logger = logging.getLogger()

PATH_TO_IMAGED_DIRECTORY = "/auto/sw_system_release/nos/nvos/"
PATH_TO_IMAGE_TEMPLATE = "{}/amd64/"
PATH_ON_SWITCH = "/tmp/"
NEXT_IMG = 'next'
CURRENT_IMG = 'current'
PARTITION1_IMG = 'partition1'
PARTITION2_IMG = 'partition2'


@pytest.mark.checklist
@pytest.mark.nvos_ci
def test_show_system_images(engines):
    """
    Show system images test

    Test flow:
    1. Run show system images
    2. Compare the current image value to the output from 'show system images current'
    3. Compare the output of 'show system images current' to 'show system version'
    4. Compare the output of 'show system images' to 'show system images installed'
    5. Compare the output of 'show system images' to 'show system images next'
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Run show command to view system images"):
        logging.info("Run show command to view system images")
        show_output = system.images.show()
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()

        with allure.step("Validate all expected fields in show output"):
            ValidationTool.verify_field_exist_in_json_output(output_dictionary,
                                                             [CURRENT_IMG, PARTITION1_IMG, NEXT_IMG]).verify_result()
            logging.info("All expected fields were found")

        with allure.step("Validate the values exist"):
            assert output_dictionary[CURRENT_IMG] is not None, "'current' image can't be found the the output"
            assert output_dictionary[PARTITION1_IMG] is not None, "'current' image can't be found the the output"
            assert output_dictionary[NEXT_IMG] is not None, "'current' image can't be found the the output"


@pytest.mark.checklist
def test_install_system_images(engines, release_name):
    """
    Install and remove system images test

    1. Install 2-3 random images
    2. Verify all installed images are listed in the show images
    3. Select a random installed image to be booted next
    4. Reboot dut and verify it booted with the corrected image
    5. Set the original image to boot next
    6. Reboot dut and make sure it bootes with the original image
    7. Uninstall all images that have been installed during the test
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Save original installed image name"):
        original_image = get_images(system)[CURRENT_IMG]
        logging.info("Original image: " + original_image)

    with allure.step("Get an available image to be installed"):
        image_name, image_path = get_image_to_install(release_name, original_image)
        image_id = image_name.replace("-amd64", "").replace(".bin", "")

    with allure.step("Verify output"):
        partition2_img = get_images(system)[PARTITION2_IMG]
        if partition2_img:
            expected_values = create_image_values_dictionary(original_image, partition2_img, original_image,
                                                             partition2_img, True)
        else:
            expected_values = create_image_values_dictionary(original_image, original_image, original_image, "", False)
        verify_output(system, expected_values)

    with allure.step("Install a random image '{}'".format(image_path)):
        do_installation(image_path, image_name, original_image, system)

    with allure.step("Set image {} to boot next".format(image_id)):
        set_next_boot_image(image_id, system)
        verify_show_output(system, original_image, image_id, original_image, image_id, True)

    with allure.step('Rebooting the dut after image installation'):
        reboot_dut()
        verify_show_output(system, image_id, image_id, original_image, image_id, True)

    with allure.step("Set the original image to be booted next"):
        set_next_boot_image(original_image, system)
        verify_show_output(system, image_id, original_image, original_image, image_id, True)

    with allure.step("Rebooting the dut after origin image installation'"):
        reboot_dut()
        verify_show_output(system, original_image, original_image, original_image, image_id, True)

    with allure.step("Uninstalling all images that have been installed during the test"):
        clear_installed_images(image_id, system)
        verify_show_output(system, original_image, original_image, original_image, None, True)


@pytest.mark.checklist
def test_images_cleanup(engines, release_name):
    """
    Cleanup installed images

    Test flow:
    1. Select 2-3 random images
    2. Install all selected images
    3. Cleanup installed images and make sure all of them were uninstalled
    """
    with allure.step("Create System object"):
        system = System()

    with allure.step("Save original installed image name"):
        original_image = get_images(system)[CURRENT_IMG]
        logging.info("Original image: " + original_image)
        verify_show_output(system, original_image, original_image, original_image, "", False)

    with allure.step("Get an available image to be installed"):
        image_name, image_path = get_image_to_install(release_name, original_image)
        image_id = image_name.replace("-amd64", "").replace(".bin", "")

    with allure.step("Install image: {}".format(image_path)):
        do_installation(image_path, image_name, original_image, system)

    with allure.step("Cleanup installed images"):
        cleanup_images(system, image_id)
        verify_show_output(system, original_image, image_id, original_image, image_id, True)

    with allure.step("Set the original image to be booted next"):
        set_next_boot_image(original_image, system)
        verify_show_output(system, original_image, original_image, original_image, image_id, True)

    with allure.step("Cleanup installed images"):
        cleanup_images(system, image_id)
        verify_show_output(system, original_image, original_image, original_image, None, True)


def verify_show_output(system, current_img, next_img, partition1_image, partition2_image, add_partition2=True):
    with allure.step("Verify output"):
        expected_values = create_image_values_dictionary(current_img, next_img, partition1_image,
                                                         partition2_image, add_partition2)
        verify_output(system, expected_values)


def create_image_values_dictionary(current_img, next_img, partition1_image, partition2_image, add_partition2=True):
    output_dictionary = {CURRENT_IMG: current_img.replace("-amd64", "").replace(".bin", ""),
                         NEXT_IMG: next_img.replace("-amd64", "").replace(".bin", ""),
                         PARTITION1_IMG: partition1_image.replace("-amd64", "").replace(".bin", "")}
    if add_partition2:
        output_dictionary.update({PARTITION2_IMG:
                                  partition2_image.replace("-amd64", "").replace(".bin", "") if partition2_image else None})
    return output_dictionary


def verify_output(system, expected_keys_values):
    output = get_images(system)
    for field, value in expected_keys_values.items():
        assert field in output.keys(), field + " can't be found int the output"
        assert value == output[field], "The value of {} is not {}".format(field, value)


def cleanup_images(system, image_name):
    logging.info("Cleanup installed images")
    system.images.action_cleanup()


def set_next_boot_image(image_name, system):
    logging.info("Setting image {} to boot next".format(image_name))
    system.images.action_boot_next(image_name)
    with allure.step("Verifying the boot next image updated successfully"):
        next_boot = get_images(system)[NEXT_IMG]
        assert next_boot == image_name, "Failed to set the new image to boot next"


def reboot_dut():
    system = System()
    logging.info("Rebooting dut")
    system.reboot.action_reboot()
    nvue_cli = NvueGeneralCli(TestToolkit.engines.dut)
    nvue_cli.verify_dockers_are_up()
    NvueGeneralCli.wait_for_nvos_to_become_functional(TestToolkit.engines.dut)


def clear_installed_images(image_name, system):
    logging.info("Uninstalling the new image")
    with allure.step("Uninstall " + image_name):
        system.images.action_uninstall(image_name)


def do_installation(image_path, image_name, origin_image_id, system):
    with allure.step("Copying image to dut"):
        path_on_switch = PATH_ON_SWITCH + image_name
        logging.info("Copy image from {src} to {dest}".format(src=image_path,
                                                              dest=path_on_switch))
        if not image_path.startswith('http'):
            image_path = '{}{}'.format(InfraConst.HTTP_SERVER, image_path)
        TestToolkit.engines.dut.run_cmd('sudo curl {} -o {}'.format(image_path, PATH_ON_SWITCH + image_name),
                                        validate=True)

    with allure.step("Installing image {}".format(path_on_switch)):
        logging.info("Installing image '{}'".format(path_on_switch))
        system.images.action_install(path_on_switch)

    with allure.step("Verify installed image"):
        expected_values = create_image_values_dictionary(origin_image_id, image_name, origin_image_id, image_name, True)
        verify_output(system, expected_values)


def get_images(system):
    with allure.step("Run show command to view 'next', 'current' and 'partition' system image"):
        logging.info("Run show command to view 'next', 'current' and 'partition' system image")
        images = system.images.get_image_field_values(['next', 'current', 'partition1', 'partition2'])
        return images


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


def get_image_to_install(release_name, current_installed_img):
    with allure.step("Get list of images"):
        with allure.step('Select random image'):
            logging.info("Select random image")
            relevant_directories = get_list_of_directories(current_installed_img, release_name)
            selected_directory = RandomizationTool.select_random_value(list(relevant_directories.keys()),
                                                                       None).get_returned_value()

            relevant_images = relevant_directories[selected_directory]
            image_name = relevant_images[0]
            image_path = selected_directory + relevant_images[0]
            logging.info("Selected image: " + image_path)

        return image_name, image_path
