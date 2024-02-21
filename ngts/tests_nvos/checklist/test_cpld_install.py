import logging
import pytest
import os.path

from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.cli_coverage.operation_time import OperationTime
from ngts.nvos_tools.infra.Fae import Fae
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.platform.Platform import Platform
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_constants.constants_nvos import ApiType, ImageConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.cpld
def test_cpld_upgrade(engines, devices):
    """
    @summary: test all these commands:
        nv show fae platform firmware cpld files
        nv action delete fae platform firmware cpld files <file-name>
        nv action fetch fae platform firmware cpld <remote-url-fetch>
        nv action install fae platform firmware cpld files <file-name> [force]
    Note: because the test takes a long time, half of it runs on NVUE and half on OpenAPI

    Test flow:
        1. Fetch old CPLD firmware images (two files: BURN and REFRESH)
        2. Assert the images exist now
        3. Install them (BURN, then REFRESH, then reboot system)
        4. Assert the current CPLD firmware version is the one just installed
        5. Delete the images that were used for installation
        6. Assert the images no longer exist
        7. Repeat steps 1-6 on for the new CPLD firmware image
    """
    TestToolkit.tested_api = ApiType.NVUE
    with allure.step('Create System objects'):
        platform = Platform()
        fae = Fae()
    try:
        with allure.step(f"Fetch, install and assert old CPLD version (through {TestToolkit.tested_api})"):
            _firmware_install_test(devices, fae, platform, devices.dut.previous_cpld_version)
    finally:
        TestToolkit.tested_api = ApiType.OPENAPI
        with allure.step(f"Fetch, install and assert original CPLD version (through {TestToolkit.tested_api})"):
            _firmware_install_test(devices, fae, platform, devices.dut.current_cpld_version)


def _get_file_list(fae: Fae):
    """Run `nv show fae platform firmware cpld files` and return output as a list of file names."""
    return OutputParsingTool.parse_show_files_to_names(fae.platform.firmware.cpld.show_files()).get_returned_value()


def _firmware_install_test(devices, fae: Fae, platform: Platform, image_consts: BaseSwitch.CpldImageConsts):
    burn_filename = os.path.basename(image_consts.burn_image_path)
    refresh_filename = os.path.basename(image_consts.refresh_image_path)
    with allure.step(f"Asserting the image files don't exist yet"):
        initial_files = _get_file_list(fae)
        assert burn_filename not in initial_files, f"Can't test `fetch` because file is already present: {burn_filename}"
        assert refresh_filename not in initial_files, f"Can't test `fetch` because file is already present: {refresh_filename}"

    with allure.step(f"Fetching BURN image"):
        fae.platform.firmware.cpld.action_fetch(image_consts.burn_image_path).verify_result()

    with allure.step(f"Fetching REFRESH image"):
        fae.platform.firmware.cpld.action_fetch(image_consts.refresh_image_path).verify_result()

    with allure.step(f"Asserting fetch was successful"):
        file_list = _get_file_list(fae)
        assert burn_filename in file_list, f"`show` command doesn't show the fetched burn-image {burn_filename}"
        assert refresh_filename in file_list, f"`show` command doesn't show the fetched refresh-image {refresh_filename}"
        assert set(file_list) == set(initial_files) | {burn_filename, refresh_filename}, \
            f"Expected only two new files {(burn_filename, refresh_filename)} but the old file list is {initial_files} " \
            f"and the new one is {file_list}"

    try:
        with allure.step(f"Installing BURN image (no reboot required) {burn_filename}"):
            result, _ = OperationTime.save_duration(
                "nv action install fae platform firmware cpld files (BURN)", burn_filename, test_cpld_upgrade.__name__,
                fae.platform.firmware.cpld.action_install,
                burn_filename, device=devices.dut, expect_reboot=False)
            result.verify_result()

        with allure.step(f"Installing REFRESH image (and rebooting) {refresh_filename}"):
            # todo: this doesn't work at openapi
            fae.platform.firmware.cpld.action_install(refresh_filename, device=devices.dut, expect_reboot=True
                                                      ).verify_result()

        with allure.step(f"Asserting install was successful"):
            firmware_shown = OutputParsingTool.parse_json_str_to_dictionary(platform.firmware.show()).get_returned_value()
            for cpld_number, expected_version in image_consts.version_names.items():
                actual_firmware = firmware_shown[cpld_number][ImageConsts.ACTUAL_FIRMWARE]
                assert actual_firmware == expected_version, \
                    f"Expected {cpld_number} version: {expected_version}. Actual version: {actual_firmware}"

    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")
        raise

    finally:
        with allure.step(f"Deleting BURN image file"):
            fae.platform.firmware.cpld.action_delete(burn_filename).verify_result()

        with allure.step(f"Deleting REFRESH image file"):
            fae.platform.firmware.cpld.action_delete(refresh_filename).verify_result()

        with allure.step(f"Asserting delete was successful"):
            final_file_list = _get_file_list(fae)
            assert set(initial_files) == set(final_file_list), (
                f"File list is expected to be the same at the start and end of the test, but the initial file list is:\n"
                f"{initial_files}\nAnd at the end of the test the list is:\n{final_file_list}")
