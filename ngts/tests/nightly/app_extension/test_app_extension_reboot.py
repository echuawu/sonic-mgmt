import allure
import logging
import pytest
import time

from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.constants.constants import SonicConst
from ngts.tests.nightly.app_extension.app_extension_helper import \
    verify_app_container_up_and_repo_status_installed, APP_INFO, verify_app_container_start_delay

logger = logging.getLogger()


@pytest.mark.reboot_reload
@pytest.mark.app_ext
@allure.title('App delay to start after reboot ')
def test_app_start_delay_after_reboot(add_app_into_repo):
    """
    This test case is app delay to start after reboot, when manifest include the following info:
        {
            "package": {
                "delayed": true
            }
        }
    1. Install app with delayed true
    2. Save config and reboot
    3. Verify app container delay to start(currently the default value is 3 mins or half and 3 mins )
    """
    delay_time = 180
    dut_engine, app_name, _ = add_app_into_repo
    version_with_delay_true = APP_INFO["delay_true"]["version"]
    try:
        with allure.step("Install app {} with version {}".format(app_name, version_with_delay_true)):
            SonicAppExtensionCli.install_app(dut_engine, app_name, version_with_delay_true)
            SonicAppExtensionCli.enable_app(dut_engine, app_name)
        with allure.step("Save config and reboot"):
            SonicGeneralCli().save_configuration(dut_engine)
            dut_engine.reload(['sudo reboot '], wait_after_ping=45)
            SonicGeneralCli().verify_dockers_are_up(dut_engine, SonicConst.DOCKERS_LIST)
            logger.info("Wait {} seconds to verify {} container is up".format(delay_time, app_name))
            time.sleep(delay_time)
            SonicGeneralCli().verify_dockers_are_up(dut_engine, [app_name])
        with allure.step("Verify app container is delay {} to start".format(delay_time)):
            verify_app_container_start_delay(dut_engine, app_name, delay_time)
    except Exception as err:
        raise AssertionError(err)
