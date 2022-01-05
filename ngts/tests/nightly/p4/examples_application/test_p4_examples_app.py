import logging
import pytest
import allure
from ngts.cli_wrappers.sonic.sonic_p4_examples_clis import P4ExamplesCli
from ngts.constants.constants import P4ExamplesConsts
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.tests.nightly.p4.examples_application.conftest import verify_running_feature

logger = logging.getLogger()


@pytest.mark.build
@pytest.mark.p4_examples
@pytest.mark.usefixtures('ignore_loganalyzer_exceptions_withbugs')
def test_p4_examples_feature_state(engines, p4_example_default_feature):
    """
    Run the p4_examples_feature_state test
    :param engines: engines fixture
    :param p4_example_default_feature: p4_example_default_feature fixture
    """
    current_version = SonicAppExtensionCli.get_installed_app_version(engines.dut, P4ExamplesConsts.APP_NAME)
    with allure.step(f"Stop feature {P4ExamplesConsts.APP_NAME} in the p4 examples app"):
        P4ExamplesCli.stop_p4_example_feature(engines.dut)
    with allure.step("Check the feature started is stopped"):
        verify_running_feature(engines.dut, P4ExamplesConsts.NO_EXAMPLE)
    with allure.step(f"Start feature {p4_example_default_feature} in the p4 examples app"):
        P4ExamplesCli.start_p4_example_feature(engines.dut, p4_example_default_feature)
    with allure.step("Verify feature was started"):
        verify_running_feature(engines.dut, p4_example_default_feature)
    with allure.step("Uninstall the P4 examples App"):
        SonicAppExtensionCli.disable_app(engines.dut, P4ExamplesConsts.APP_NAME)
        SonicAppExtensionCli.uninstall_app(engines.dut, P4ExamplesConsts.APP_NAME)
    with allure.step("Re-install the P4 examples App"):
        SonicAppExtensionCli.install_app(engines.dut, P4ExamplesConsts.APP_NAME, version=f'{current_version}')
        SonicAppExtensionCli.enable_app(engines.dut, P4ExamplesConsts.APP_NAME)
    with allure.step("Check the feature is stopped after app is re-installed"):
        verify_running_feature(engines.dut, P4ExamplesConsts.NO_EXAMPLE)
