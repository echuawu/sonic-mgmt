import allure
import logging
import pytest
import re

from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.tests.push_build_tests.app_extension.app_extension_helper import \
    verify_app_container_up_and_repo_status_installed, gen_app_tarball, APP_INFO


logger = logging.getLogger()


@pytest.mark.app_ext
@pytest.mark.parametrize("upgrade_type", ["repo", "repo_force", "tarball"])
@allure.title('App package upgrade ')
def test_app_upgrade(pre_install_app, upgrade_type):
    """
    This test case is test app upgrade, it includes following sub test cases:
    1. Upgrade app to normal version
    2. Upgrade app to normal version using --force upgrade option
    3. Upgrade app to noraml version from tarball
    After upgrade, need check version is upgraded to specified one,
    and install status by spm list, and container status by docker ps

    """
    dut_engine, _ = pre_install_app
    app_name = APP_INFO["name"]
    version = APP_INFO["normal2"]["version"]
    app_repo = APP_INFO["repository"]
    try:
        with allure.step("Upgrade app {} with version {}".format(app_name, version)):
            if upgrade_type is "repo":
                SonicAppExtensionCli.upgrade_app(dut_engine, app_name, version)
            elif upgrade_type is "repo_force":
                SonicAppExtensionCli.upgrade_app(dut_engine, app_name, version, is_force_upgrade=True)
            elif upgrade_type is "tarball":
                tarball_name = gen_app_tarball(dut_engine, app_repo, app_name, version)
                SonicAppExtensionCli.upgrade_app_from_tarbll(dut_engine, tarball_name)
        with allure.step("Verify app version is upgraded to specified one, and status is correct"):
            verify_app_container_up_and_repo_status_installed(dut_engine, app_name, version)
    except Exception as err:
        raise AssertionError(err)


@pytest.mark.app_ext
@pytest.mark.parametrize(
    "app_name, version, expected_error_msg",
    [
        (APP_INFO["name"], APP_INFO["invalid_manifest"]["version"],
         "Failed to upgrade {}.*{}.*required field but it is missing".format(
             APP_INFO["name"], APP_INFO["invalid_manifest"]["version"])),
        (APP_INFO["name"], APP_INFO["missing_dependency"]["version"],
         "Failed to upgrade {}.*{}.*missing-dependency.*it is not installed".format(
             APP_INFO["name"], APP_INFO["missing_dependency"]["version"], APP_INFO["name"])),
        (APP_INFO["name"], APP_INFO["package_conflict"]["version"],
         "Failed to upgrade {}.*{}.*Package .*{}.*conflicts.*".format(
             APP_INFO["name"], APP_INFO["package_conflict"]["version"], APP_INFO["name"])),
    ],
)
@allure.title('App package upgrade with abnormal package ')
def test_app_upgrade_with_abnormal_package(pre_install_app, app_name, version, expected_error_msg):
    """
    This test case is test app upgrade with abnormal package
    1. App with a invalid manifest
    2. App with missing dependency
    3. App with package confict
    After upgrade, need check
    1. There are corresponding error message
    2. Original version still works well

    """
    dut_engine, old_version = pre_install_app

    try:
        with allure.step("Upgrade app {} with version {} using abnormal package".format(app_name, version)):
            output = SonicAppExtensionCli.upgrade_app(dut_engine, app_name, version, is_force_upgrade=False, validate=False)
            logger.info("Expected message is {}, actual message is {}".format(expected_error_msg, output))
            msg_pattern = re.compile(expected_error_msg)
            assert msg_pattern.match(output), "Error msg for upgrading abnormal app is not correct"
        with allure.step("Verify original verison still works well"):
            verify_app_container_up_and_repo_status_installed(dut_engine, app_name, old_version)
    except Exception as err:
        raise AssertionError(err)