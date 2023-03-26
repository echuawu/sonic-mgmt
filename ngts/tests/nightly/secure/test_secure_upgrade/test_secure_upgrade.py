"""
This test checks secure upgrade feature. If we have a secure system with secured image installed
on it, the system is expected to install only secured images on it. So trying to install non-secure image
will cause fail and a print of failure message to console indicating it is not a secured image.
This test case validates the error flow mentioned above.

In order to run this test, you need to specify the following argument:

    --target_version (to contain a non-secure image path e.g. /tmp/images/my_non_secure_img.bin)
    --sig_mismatch_image (to contain a signature mismatched image path e.g. /tmp/images/my_sig_mismatch_secure_img.bin)

Secure Boot and Upgrade Test Cases

https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+SECURE+BOOT+AND+UPGRADE+Documentation
"""
import logging
import pytest

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.tests.nightly.secure.constants import SecureUpgradeConsts

logger = logging.getLogger()
allure.logger = logger


@pytest.mark.parametrize("image_path", SecureUpgradeConsts.IMAGE_PATH)
def test_secure_upgrade_block(secure_boot_helper, request, image_path, keep_same_version_installed):
    """
    This test case validates non successful upgrade of a given non secure or signature mismatched image
    """
    secure_boot_helper.validate_secure_upgrade_sonic_installer(request, image_path)
