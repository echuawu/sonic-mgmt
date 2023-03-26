import pytest
import logging

from ngts.tests.nightly.secure.constants import SonicSecureBootConsts
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.helpers.secure_boot_helper import SecureBootHelper, SonicSecureBootHelper


logger = logging.getLogger()
allure.logger = logger


@pytest.fixture(scope='session')
def secure_boot_helper(serial_engine, engines, cli_objects):
    """
    This fixture will return the secure boot helper for sonic
    """
    return SonicSecureBootHelper(serial_engine, engines, cli_objects)


@pytest.fixture(scope='session')
def secure_boot_consts():
    """
    This fixture will return the secure boot constants for sonic
    """
    return SonicSecureBootConsts()


def pytest_addoption(parser):
    """
    secure boot and upgrade pytest options
    """
    SecureBootHelper.pytest_addoption(parser)


@pytest.fixture(scope='session')
def serial_engine(topology_obj):
    """
    This fixture will return the serial connection
    """
    return SecureBootHelper.get_serial_engine(topology_obj)


@pytest.fixture(scope='session')
def non_secure_image_path(request, secure_boot_helper):
    """
    This fixture will extract the non secure image path from --non_signed_image parameter
    """
    return secure_boot_helper.get_non_secure_image_path(request)


@pytest.fixture(scope='session')
def keep_same_version_installed(secure_boot_helper):
    """
    @summary: extract the current version installed as shown in the "show boot" output
    and restore original image installed after the test run
    """
    current_image = secure_boot_helper.get_image_version()

    yield

    secure_boot_helper.set_default_image(current_image)


@pytest.fixture(scope='function')
def restore_image_path(request, secure_boot_helper):
    """
    This fixture returns the path to restore image
    """
    return secure_boot_helper.get_restore_to_image_path(request)


@pytest.fixture(scope='function')
def sig_mismatch_image_path(secure_boot_helper, request):
    """
    This fixture returns the path to restore image
    """
    return secure_boot_helper.get_sig_mismatch_image_path(request)


@pytest.fixture(scope='function')
def test_server_engine(secure_boot_helper):
    """
    This fixture will return the sonic-mgmt-test server engine
    """
    return secure_boot_helper.get_test_server_engine()


@pytest.fixture(scope='function')
def vmiluz_filepath(secure_boot_helper):
    """
    This fixture will return the file path of vmlinuz
    """
    return secure_boot_helper.get_vmiluz_file_path()


@pytest.fixture(scope='function')
def mount_uefi_disk_partition(secure_boot_helper):
    """
    This fixture will load the uefi disk partition
    """
    secure_boot_helper.mount_uefi_disk_partition()


@pytest.fixture(scope='function')
def restore_kernel_module(secure_boot_helper):
    """
    This function will restore kernel module installation status
    """
    yield

    secure_boot_helper.restore_kernel_module()


@pytest.fixture(scope='function')
def onie_install_and_wait_boot_up(secure_boot_helper, restore_image_path):
    """
    This function will install image in onie mode and wait until it boot up
    """
    yield

    secure_boot_helper.onie_install_wait_boot_up(restore_image_path)


@pytest.fixture(scope='function')
def recover_switch_after_secure_boot_violation_message(secure_boot_helper, restore_image_path):
    """
    This function will recover the switch after receiving a secure boot violation message appear
    """
    yield

    secure_boot_helper.recover_switch_after_secure_boot(restore_image_path)
