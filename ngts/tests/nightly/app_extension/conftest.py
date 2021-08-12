import pytest
import logging
import allure
import os

from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.tests.nightly.app_extension.app_extension_helper import \
    verify_add_app_to_repo, verify_app_container_up_and_repo_status_installed, APP_INFO, app_cleanup
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.constants.constants import InfraConst

logger = logging.getLogger()


@pytest.fixture(scope='function', autouse=False)
def add_app_into_repo(engines):
    """
    :parm engines: ssh engines fixture

    """
    dut_engine = engines.dut
    app_name = APP_INFO["name"]
    app_repository_name = APP_INFO["repository"]
    version = APP_INFO["normal1"]["version"]
    app_cleanup(dut_engine, app_name)
    SonicAppExtensionCli.add_repository(dut_engine, app_name, app_repository_name, version=version)
    verify_add_app_to_repo(dut_engine, app_name, app_repository_name)

    yield dut_engine, app_name, version

    with allure.step('App package cleanup'):
        app_cleanup(dut_engine, app_name)


@pytest.fixture(scope='function', autouse=False)
def pre_install_app(engines, add_app_into_repo):
    """
    :parm engines: ssh engines fixture

    """
    dut_engine, app_name, version = add_app_into_repo
    with allure.step("Prerequisite: Install app with {}, version={}".format(app_name, version)):
        SonicAppExtensionCli.install_app(dut_engine, app_name, version)
        status = GeneralCliCommon.get_container_status(dut_engine, app_name)
        assert not status, "Excepted container status is None, actual container status is {}".format(status)
        logger.info("Enable feature of {}".format(app_name))
        SonicAppExtensionCli.enable_app(dut_engine, app_name)
        verify_app_container_up_and_repo_status_installed(dut_engine, app_name, version)

    yield dut_engine, version


@pytest.fixture(scope="package", autouse=True)
def skipping_app_ext_test_case(engines):
    """
    If app ext feature is not ready, skipping all app ext test cases execution
    """
    if not SonicAppExtensionCli.verify_version_support_app_ext(engines.dut):
        pytest.skip("Skipping app ext test cases due to that app ext feature is not ready")


@pytest.fixture(scope='function', autouse=False)
def pre_install_base_image(topology_obj, upgrade_params, engines):
    """
    According to the upgrade_params, judge if do upgrade test.
    If do upgrade
    1. Install base image by deploy_image
    2. After test is over, need to recovery image to old image

    """
    if not upgrade_params.is_upgrade_required:
        pytest.skip('This platform not configure base and target version')
    dut_engine = engines.dut

    _, old_target_image = SonicGeneralCli.get_base_and_target_images(dut_engine)
    base_version = upgrade_params.base_version
    target_version = upgrade_params.target_version
    if not base_version.startswith('http'):
        base_version = '{}{}'.format(InfraConst.HTTP_SERVER, base_version)
    if not target_version.startswith('http'):
        target_version = '{}{}'.format(InfraConst.HTTP_SERVER, target_version)
    with allure.step("Prerequisite: Install base image {}".format(base_version)):
        SonicGeneralCli.deploy_image(topology_obj, base_version)

    yield base_version, target_version

    with allure.step("Recovery old target image {}".format(old_target_image)):
        current_base_version, current_target_version = SonicGeneralCli.get_base_and_target_images(dut_engine)
        if old_target_image != current_target_version:
            if current_base_version == old_target_image:
                switch_version_by_set_default_image(engines.dut, target_version)
            else:
                SonicGeneralCli.deploy_image(topology_obj, target_version)


def switch_version_by_set_default_image(dut_engine, version):
    """
    Switch version by setting default image and check if switch success or not
    """
    with allure.step("Set {} as default image".format(version)):
        SonicGeneralCli.set_default_image(dut_engine, version)
    with allure.step('Rebooting the dut'):
        dut_engine.reload(['sudo reboot'])
    with allure.step('Verifying dut booted with correct image'):
        # installer flavor might change after loading a different version
        delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)
        image_list = SonicGeneralCli.get_sonic_image_list(dut_engine, delimiter)
        assert 'Current: {}'.format(version) in image_list
    with allure.step("Verify basic container is up"):
        SonicGeneralCli.verify_dockers_are_up(dut_engine)


@pytest.fixture(autouse=False)
def ignore_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "..", "..", "..",
                                                               "tools", "loganalyzer", "reboot_loganalyzer_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


@pytest.fixture(autouse=False)
def ignore_temp_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests
    because of some expected bugs which causes exceptions in log
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "temp_log_analyzer_ignores.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)
