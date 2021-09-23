import pytest
import allure

from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed


@pytest.mark.order(after='tests/push_build_tests/system/test_cpu_ram_hdd_usage.py')
@pytest.mark.app_ext
@pytest.mark.build
@pytest.mark.push_gate
def test_app_status(engines, pre_app_ext):
    """
    This test validates app container status is up and app is installed
    """
    is_support_app_ext, app_name, version, _ = pre_app_ext

    if not is_support_app_ext:
        pytest.skip('This build not support app ext')

    with allure.step("Verify app up and status is installed"):
        verify_app_container_up_and_repo_status_installed(engines.dut, app_name, version)
