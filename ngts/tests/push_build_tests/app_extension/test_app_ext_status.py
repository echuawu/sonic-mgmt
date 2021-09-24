import pytest
import allure

from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


@pytest.mark.order(after='tests/push_build_tests/system/test_cpu_ram_hdd_usage.py')
@pytest.mark.app_ext
@pytest.mark.build
@pytest.mark.push_gate
def test_app_status(engines, shared_params, upgrade_params):
    """
    This test validates app container status is up and app is installed
    """
    # If below required in case when we did upgrade and the run nested pytest sessions during reboot/reload validations
    if upgrade_params.is_upgrade_required:
        base_image, target_image = SonicGeneralCli.get_base_and_target_images(engines.dut)
        if '202012' in base_image:
            pytest.skip('App ext during upgrade from 202012 image not supported')

    if not shared_params.app_ext_is_app_ext_supported:
        pytest.skip('This build not support app ext')

    with allure.step("Verify app up and status is installed"):
        verify_app_container_up_and_repo_status_installed(engines.dut, shared_params.app_ext_app_name,
                                                          shared_params.app_ext_version)
