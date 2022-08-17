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


@pytest.mark.checklist
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
                                                             ["current", "installed", "next"]).verify_result()
            logging.info("All expected fields were found")

        current_image = output_dictionary["current"]
        next_image = output_dictionary["next"]
        installed_images = {}
        for image_label, image_row in output_dictionary["installed"].items():
            for image_name in image_row.keys():
                installed_images[image_name] = {}

    with allure.step("Verify image name using 'show system images current'"):
        logging.info("Verify image name using 'show system images current'")
        current_image_temp = get_current_image_name(system)
        ValidationTool.compare_values(current_image, current_image_temp).verify_result()

    with allure.step("Verify image name using  'show system version'"):
        logging.info("Verify image name using  'show system version'")
        show_system_version_res = system.show("version")
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_system_version_res).get_returned_value()
        ValidationTool.compare_values(output_dictionary, {}, False).verify_result()

        current_image_temp = output_dictionary["image"]
        ValidationTool.compare_values(current_image, current_image_temp).verify_result()

    with allure.step("Verify next image name using 'show system images next'"):
        logging.info("Verify next image name using 'show system images next'")
        next_image_temp = get_next_image_name(system)
        ValidationTool.compare_values(next_image, next_image_temp).verify_result()

    if not is_redmine_issue_active([3113687]):
        with allure.step("Verify installed images using 'show system images installed'"):
            logging.info("Verify installed images using 'show system images installed'")
            installed_images_temp = get_installed_images(system)

            for key in installed_images_temp.keys():
                assert key in installed_images.keys(), "{} can't be found in the installed images list".format(key)


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
        original_image = get_current_image_name(system)
        logging.info("Original image: " + original_image)

    with allure.step("Get an available image to be installed"):
        image_name, image_path = get_image_to_install(release_name, original_image)
        image_id = image_name.replace("-amd64", "").replace(".bin", "")

    with allure.step("Install a random image '{}'".format(image_path)):
        do_installation(image_path, image_name, system)

    with allure.step("Set image {} to boot next".format(image_id)):
        set_next_boot_image(image_id, system)

    with allure.step('Rebooting the dut after image installation'):
        reboot_dut()

    with allure.step('Verifying dut booted with correct image'):
        current_image = get_current_image_name(system)
        assert current_image == image_id, "Installation failed - the current image is not the expected one"

    with allure.step("Set the original image to be booted next"):
        set_next_boot_image(original_image, system)

    with allure.step("Rebooting the dut after origin image installation'"):
        reboot_dut()

    with allure.step("Verify installation completed successfully"):
        verify_current_image_name(system, original_image, True)

    with allure.step("Uninstalling all images that have been installed during the test"):
        clear_installed_images(image_id, system)


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
        original_image = get_current_image_name(system)
        logging.info("Original image: " + original_image)

    with allure.step("Get an available image to be installed"):
        image_name, image_path = get_image_to_install(release_name, original_image)
        image_id = image_name.replace("-amd64", "").replace(".bin", "")

    with allure.step("Install image: {}".format(image_path)):
        do_installation(image_path, image_name, system)

    with allure.step("Rebooting the dut after origin image installation'"):
        reboot_dut()

    with allure.step("Cleanup installed images"):
        cleanup_images(system, image_id)


def cleanup_images(system, image_name):
    logging.info("Cleanup installed images")
    system.images.action_cleanup()

    with allure.step("Verify all images have been uninstalled"):
        verify_image_name_in_installed_list(image_name, system, False)


def set_next_boot_image(image_name, system):
    logging.info("Setting image {} to boot next".format(image_name))
    system.images.action_boot_next(image_name)
    with allure.step("Verifying the boot next image updated successfully"):
        next_boot = get_next_image_name(system)
        assert next_boot == image_name, "Failed to set the new image to boot next"


def reboot_dut():
    logging.info("Rebooting dut")
    TestToolkit.engines.dut.reload(['sudo reboot'])
    nvue_cli = NvueGeneralCli(TestToolkit.engines.dut)
    nvue_cli.verify_dockers_are_up()
    NvueGeneralCli.wait_for_nvos_to_become_functional(TestToolkit.engines.dut)


def verify_current_image_name(system, expected_value, should_equal):
    logging.info('Verifying dut booted with correct image')
    current_image = get_current_image_name(system)
    assert current_image == expected_value and should_equal, "The current image is not the expected one"


def clear_installed_images(image_name, system):
    logging.info("Uninstalling the new image")
    with allure.step("Uninstall " + image_name):
        system.images.action_uninstall(image_name)
        with allure.step("Verify the image was uninstalled"):
            verify_image_name_in_installed_list(image_name, system, False)


def do_installation(image_path, image_name, system):
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

    with allure.step("Verifying installation completed successfully"):
        verify_image_name_in_installed_list(image_name, system, True)


def verify_image_name_in_installed_list(image_name, system, should_exist):
    logging.info("Verifying that the installed image {} in 'show images installed' output".format(
        "exists" if should_exist else "doesn't exist"))
    if not is_redmine_issue_active([3113687]):
        show_output = system.images.show("installed")
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.verify_field_exist_in_json_output(output_dictionary, [image_name], should_exist)


def get_current_image_name(system):
    with allure.step("Run show command to view 'current' system image"):
        logging.info("Run show command to view 'current' system image")
        show_output = system.images.show("current")

        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_output).get_returned_value()
        ValidationTool.compare_values(output_dictionary, {}, False).verify_result()

        current_image = list(output_dictionary.keys())[0]
        logging.info("Current installed image: {}".format(current_image))
        return current_image


def get_next_image_name(system):
    with allure.step("Run show command to view 'next' system image"):
        logging.info("Run show command to view 'next' system image")
        show_system_version_res = system.images.show("next")
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_system_version_res).get_returned_value()
        ValidationTool.compare_values(output_dictionary, {}, False).verify_result()
        next_image_temp = list(output_dictionary.keys())[0]
        return next_image_temp


def get_installed_images(system):
    with allure.step("Run show command to view 'installed' system image"):
        logging.info("Run show command to view 'installed' system image")
        show_system_version_res = system.images.show("installed")
        output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(show_system_version_res).get_returned_value()
        ValidationTool.compare_values(output_dictionary, {}, False).verify_result()
        return output_dictionary


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
