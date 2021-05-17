import pytest
import allure

from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed


def test_app_status_after_upgrade(upgrade_params, engines, pre_app_ext):
    """
    This test is to test container status of app is still up and app is still installed after upgrade
    """
    if not upgrade_params.is_upgrade_required:
        pytest.skip('Upgrade was not ran, no need to check')

    is_support_app_ext, app_name, version, _ = pre_app_ext

    if not is_support_app_ext:
        pytest.skip('This build not support app ext')

    with allure.step("Verify app up and status is installed, "
                     "after migrate app from base image:{} to target image:{}".format(upgrade_params.base_version, upgrade_params.target_version)):
        verify_app_container_up_and_repo_status_installed(engines.dut, app_name, version)