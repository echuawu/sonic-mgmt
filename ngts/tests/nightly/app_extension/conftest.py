import pytest
import logging
import allure

from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.tests.nightly.app_extension.app_extension_helper import \
    verify_add_app_to_repo, verify_app_container_up_and_repo_status_installed, APP_INFO, app_cleanup


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
