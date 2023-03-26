"""
Secure Boot Suite case:

In this test file we introduce different cases for secure boot feature.
Secure Boot is a feature that validates secure boot and only signed modules are running.

In order to run this test, you need to specify the following argument: kernel_module_path

Secure Boot and Upgrade Test Cases

https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+SECURE+BOOT+AND+UPGRADE+Documentation
"""
import logging
import pytest

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.tests.nightly.secure.constants import SecureBootConsts

logger = logging.getLogger()
allure.logger = logger


def test_unsigned_shim_secure_boot(secure_boot_helper, secure_boot_consts, mount_uefi_disk_partition,
                                   test_server_engine, recover_switch_after_secure_boot_violation_message):
    """
    In this test case we want to simulate broken signature of shim
    by manually changing it and then do reboot/fast-reboot and see that it doesn't boot successfully
    """
    with allure.step("Test secure boot of shim validation"):
        secure_boot_helper.unsigned_file_secure_boot(secure_boot_consts.SHIM_FILEPATH,
                                                     test_server_engine,
                                                     secure_boot_consts.SHIM)


def test_unsigned_grub_secure_boot(secure_boot_helper, secure_boot_consts, mount_uefi_disk_partition,
                                   test_server_engine, recover_switch_after_secure_boot_violation_message):
    """
    In this test case we want to simulate broken signature of grub
    by manually changing it and then do reboot/fast-reboot and see that it doesn't boot successfully
    """
    with allure.step("Test secure boot of grub validation"):
        secure_boot_helper.unsigned_file_secure_boot(secure_boot_consts.GRUB_FILEPATH,
                                                     test_server_engine,
                                                     secure_boot_consts.GRUB)


def test_unsgined_vmlinuz_secure_boot(secure_boot_helper, secure_boot_consts, test_server_engine,
                                      vmiluz_filepath, recover_switch_after_secure_boot_violation_message):
    """
    In this test case we want to simulate broken signature of vmlinuz component
    by manually changing it and then do reboot/fast-reboot/warm-reboot and see that it doesn't boot successfully
    """
    with allure.step("Test secure boot of vmlinuz validation"):
        secure_boot_helper.unsigned_file_secure_boot(vmiluz_filepath, test_server_engine, secure_boot_consts.VMLINUZ)


def test_signed_kernel_module_load(secure_boot_helper):
    """
    In this test case we want to validate successful
    load of secured kernel module
    """
    with allure.step("Test secure boot of signed kernel module"):
        secure_boot_helper.signed_kernel_module_secure_boot()


def test_non_signed_kernel_module_load(secure_boot_helper, restore_kernel_module):
    """
    In this test case we want to validate unsuccessful load
    of unsigned kernel module
    """
    with allure.step("Test secure boot of unsigned kernel module"):
        secure_boot_helper.un_signed_kernel_module_secure_boot()


@pytest.mark.parametrize("image_path", SecureBootConsts.IMAGE_PATH)
def test_secure_boot_onie(secure_boot_helper, request, image_path, topology_obj, onie_install_and_wait_boot_up):
    """
    In this test case we want to validate unsuccessful load of unsigned image from onie
    """
    with allure.step("Test secure boot in onie mode"):
        secure_boot_helper.onie_secure_boot(request, image_path, topology_obj)
