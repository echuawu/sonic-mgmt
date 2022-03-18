import logging
import pytest
import allure
from ngts.cli_wrappers.sonic.sonic_p4_examples_clis import P4ExamplesCli
from ngts.constants.constants import P4ExamplesConsts
from ngts.tests.nightly.p4.examples_application.conftest import verify_running_feature

logger = logging.getLogger()


@pytest.mark.build
@pytest.mark.p4_examples
def test_p4_examples_feature_state(engines, cli_objects, p4_example_default_feature):
    """
    Run the p4_examples_feature_state test
    :param engines: engines fixture
    :param p4_example_default_feature: p4_example_default_feature fixture
    """
    current_version = cli_objects.dut.app_ext.get_installed_app_version(P4ExamplesConsts.APP_NAME)
    with allure.step(f"Stop feature {P4ExamplesConsts.APP_NAME} in the p4 examples app"):
        P4ExamplesCli.stop_p4_example_feature(engines.dut)
    with allure.step("Check the feature started is stopped"):
        verify_running_feature(engines.dut, P4ExamplesConsts.NO_EXAMPLE)
    with allure.step(f"Start feature {p4_example_default_feature} in the p4 examples app"):
        P4ExamplesCli.start_p4_example_feature(engines.dut, p4_example_default_feature)
    with allure.step("Verify feature was started"):
        verify_running_feature(engines.dut, p4_example_default_feature)
    with allure.step("Uninstall the P4 examples App"):
        cli_objects.dut.app_ext.disable_app(P4ExamplesConsts.APP_NAME)
        cli_objects.dut.app_ext.uninstall_app(P4ExamplesConsts.APP_NAME)
    with allure.step("Re-install the P4 examples App"):
        cli_objects.dut.app_ext.install_app(P4ExamplesConsts.APP_NAME, version=f'{current_version}')
        cli_objects.dut.app_ext.enable_app(P4ExamplesConsts.APP_NAME)
    with allure.step("Check the feature is stopped after app is re-installed"):
        verify_running_feature(engines.dut, P4ExamplesConsts.NO_EXAMPLE)
