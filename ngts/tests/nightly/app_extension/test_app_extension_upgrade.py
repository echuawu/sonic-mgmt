import allure
import logging
import pytest
import re

from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.tests.nightly.app_extension.app_extension_helper import \
    verify_app_container_up_and_repo_status_installed, verify_app_container_down_and_repo_status_na, APP_INFO
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@pytest.mark.app_ext
@pytest.mark.parametrize("upgrade_type", ["repo", "repo_force"])
@allure.title('App package upgrade ')
def test_app_upgrade(pre_install_app, upgrade_type):
    """
    This test case is test app upgrade, it includes following sub test cases:
    1. Upgrade app to normal version
    2. Upgrade app to normal version using --force upgrade option
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
        with allure.step("Verify app version is upgraded to specified one, and status is correct"):
            verify_app_container_up_and_repo_status_installed(dut_engine, app_name, version)
    except Exception as err:
        raise AssertionError(err)


@pytest.mark.app_ext
@pytest.mark.parametrize(
    "app_name, version, expected_error_msg",
    [
        (APP_INFO["name"], APP_INFO["invalid_manifest"]["version"],
         "Failed to install {}.*{}.*required field but it is missing".format(
             APP_INFO["name"], APP_INFO["invalid_manifest"]["version"])),
        (APP_INFO["name"], APP_INFO["missing_dependency"]["version"],
         "Failed to install {}.*{}.*missing-dependency.*it is not installed".format(
             APP_INFO["name"], APP_INFO["missing_dependency"]["version"], APP_INFO["name"])),
        (APP_INFO["name"], APP_INFO["package_conflict"]["version"],
         "Failed to install {}.*{}.*Package .*{}.*conflicts.*".format(
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


@pytest.mark.app_ext
@allure.title('Sonic upgrade to sonic with skipping migrating package')
def test_sonic_to_sonic_upgrade_with_sipping_migrating_package(pre_install_base_image, pre_install_app, skipping_migrating_package):
    """
    This test case is to test sonic upgrade to sonic without package migrating, after upgrade verify app is clean

    """
    base_version, target_version = pre_install_base_image
    dut_engine, version = pre_install_app
    app_name = APP_INFO["name"]

    try:
        with allure.step("Upgrade from sonic base:{} to sonic target:{}. Skipping migrating is {}".format(
                base_version, target_version, skipping_migrating_package)):
            SonicGeneralCli().deploy_sonic(dut_engine, target_version, skipping_migrating_package)
        with allure.step("Verify basic container is up"):
            SonicGeneralCli().verify_dockers_are_up(dut_engine)
        with allure.step("Verify app:{} is clean".format(app_name)):
            verify_app_container_down_and_repo_status_na(dut_engine, app_name)

    except Exception as err:
        raise AssertionError(err)
