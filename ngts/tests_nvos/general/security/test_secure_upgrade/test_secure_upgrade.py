"""
This test checks secure upgrade feature. If we have a secure system with secured image installed
on it, the system is expected to install only secured images on it. So trying to install non-secure image
will cause fail and a print of failure message to console indicating it is not a secured image.
This test case validates the error flow mentioned above.

In order to run this test, you need to specify the following argument:

    --target_image_list (to contain one non-secure image path e.g. /tmp/images/my_non_secure_img.bin)
"""
import logging

import pytest

from ngts.nvos_constants.constants_nvos import ImageConsts
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def keep_same_version_installed(engines):
    '''
    @summary: extract the current version installed as shown in the "show boot" output
    and restore original image installed after the test run
    :param duthost: device under test
    '''
    yield

    logger.info("Restoring original image by setting the boot-next to partition1, in case the non-signed "
                "image was installed")
    engines.dut.run_cmd("nv action boot-next system image partition1")


@pytest.fixture(scope='session')
def non_secure_image_path(target_version):
    '''
    @summary: will extract the non secure image path from --target_image_list parameter
    :return: given non secure image path
    '''
    assert target_version is not None, "No target image is specified"
    return str(target_version)


@pytest.fixture(scope='session')
def non_secure_image_name(non_secure_image_path):
    '''
    @summary: will extract the non secure image name from target_version
    :return: given non secure image path
    '''
    img_name = non_secure_image_path.split('/')[-1]
    return img_name


@pytest.fixture(scope='session')
def delete_fetched_image(non_secure_image_name):
    '''
    @summary: delete the fetched image
    :param non_secure_image_name:
    :return:
    '''
    yield

    logger.info("Deleting fetched image")
    system = System()
    system.image.files.file_name[non_secure_image_name].action_delete("Action succeeded")


@pytest.mark.secure_boot
@pytest.mark.checklist
def test_non_secure_boot_upgrade_failure(non_secure_image_path, keep_same_version_installed, non_secure_image_name,
                                         delete_fetched_image, is_secure_boot_enabled):
    """
    @summary: This test case validates non successful upgrade of a given non secure image
    """
    # system will be used for nv fetch/install
    system = System()

    # install non secure image
    with allure.step("install non secure image - expect fail, image path = {}".format(non_secure_image_path)):
        logger.info("install non secure image - expect fail, image path = {}".format(non_secure_image_path))

    with allure.step("Fetching the image"):
        logger.info("Fetching the image")
        remote_image_path = ImageConsts.SCP_PATH + non_secure_image_path
        system.image.action_fetch(remote_image_path)

    with allure.step("Attempting installing non secure image"):
        logger.info("Attempting installing non secure image")
        system.image.files.file_name[non_secure_image_name].action_file_install("Failed to verify image signature")
