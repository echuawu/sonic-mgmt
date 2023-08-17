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


@pytest.fixture(scope='session', autouse=True)
def check_if_secure_boot_need_to_be_skip(cli_objects):
    """
    This fixture will check whether secure boot is enabled
    """
    boot_config_status = cli_objects.dut.general.get_bootctl_status()
    SonicSecureBootHelper.check_secure_boot_status(boot_config_status)


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
def non_secure_image_path(secure_boot_helper):
    """
    This fixture will extract the non secure image path from --non_signed_image parameter
    """
    return SecureBootHelper.get_non_secure_image_path()


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
    path = secure_boot_helper.get_restore_to_image_path(request)
    if not path:
        pytest.skip("Skip the test case for the restore image path is not provided.")
    else:
        return path


@pytest.fixture(scope='function')
def sig_mismatch_image_path(secure_boot_helper):
    """
    This fixture returns the path to restore image
    """
    return SecureBootHelper.get_sig_mismatch_image_path()


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
def restore_to_sonic(secure_boot_helper, restore_image_path):
    """
    This function will install image in onie mode and wait until it boot up
    """
    yield

    secure_boot_helper.boot_from_onie(restore_image_path)


@pytest.fixture(scope='function')
def recover_switch_after_secure_boot_violation_message(secure_boot_helper, restore_image_path, request):
    """
    This function will recover the switch after receiving a secure boot violation message appear
    """
    yield
    if not secure_boot_helper.restore_vmlinuz_signature():
        with allure.step("Recovering the switch"):
            logger.info("Disconnect engine connection")
            secure_boot_helper.cli_objects.dut.general.engine.disconnect()
            secure_boot_helper.login_into_onie_mode()

        if SonicSecureBootConsts.FWUTIL_ONIE_TEST_NAME in request.node.name:
            secure_boot_helper.remove_staged_onie_pkg()
            restore_image_path = None

        with allure.step("ONIE reboot and wait switch boot up"):
            secure_boot_helper.boot_from_onie(restore_image_path)


@pytest.fixture(scope="module", autouse=True)
def dut_secure_type(platform_params, engines):
    logger.info("Check the secure boot is dev or prod")
    device = engines.dut.run_cmd('ls /dev/mst/ | egrep mt.*_pciconf0')
    if not device:
        pytest.fail(f"The mst device is not found.")
    mst_info = engines.dut.run_cmd(f'sudo flint -d /dev/mst/{device} q full')
    if "Security Attributes:   secure-fw, dev" in mst_info:
        return 'dev'
    elif "Security Attributes:   secure-fw, prod" in mst_info:
        return 'prod'
    else:
        pytest.fail("Failed to get the secure type of the device.")
