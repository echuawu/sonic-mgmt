import pytest
import os
from ngts.constants.constants import P4ExamplesConsts
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_wrappers.sonic.sonic_p4_examples_clis import P4ExamplesCli
from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed


@pytest.fixture(scope="package", autouse=True)
def skipping_p4_examples_test_case(engines):
    """
    If p4-examples is not installed, skipping all p4-examples test cases execution
    :param engines: engines fixture
    """
    try:
        verify_app_container_up_and_repo_status_installed(engines.dut, P4ExamplesConsts.APP_NAME, "")
    except Exception:
        pytest.skip(f"Skipping {P4ExamplesConsts} test cases due to {P4ExamplesConsts.APP_NAME} is not installed.")


@pytest.fixture(scope='module')
def p4_example_default_feature():
    """
    Return the feature which will be started by default after the installation
    :return: the default feature name in p4 examples
    """
    return P4ExamplesConsts.VXLAN_BM_FEATURE_NAME


@pytest.fixture(scope='session', autouse=False)
def p4_examples_config(engines, run_test_only):
    """
    Fixture used to install the p4 examples and enable the application, and uninstall the application after test.
    :param engines: engines fixture
    :param run_test_only: run_test_only fixture
    """
    if not run_test_only:
        SonicAppExtensionCli.add_repository(engines.dut, P4ExamplesConsts.APP_NAME,
                                            repository_name=P4ExamplesConsts.REPO_NAME)
        SonicAppExtensionCli.install_app(engines.dut, P4ExamplesConsts.APP_NAME, version=P4ExamplesConsts.APP_VERSION)
        SonicAppExtensionCli.enable_app(engines.dut, P4ExamplesConsts.APP_NAME)
    yield
    if not run_test_only:
        SonicAppExtensionCli.disable_app(engines.dut, P4ExamplesConsts.APP_NAME)
        SonicAppExtensionCli.uninstall_app(engines.dut, P4ExamplesConsts.APP_NAME)
        SonicAppExtensionCli.remove_repository(engines.dut, P4ExamplesConsts.APP_NAME)


def verify_running_feature(engine, expected_feature):
    """
    Verify the feature running in the p4 docker is as expected
    :param engine: dut engine ssh object
    :param expected_feature: expected feature name
    """
    running_feature = P4ExamplesCli.get_p4_example_running_feature(engine)
    assert running_feature == expected_feature, \
        f"Expect no feature is running, but {running_feature} is running in the {P4ExamplesConsts.APP_NAME}"


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
                                                               "..", "..", "..", "..",
                                                               "tools", "loganalyzer",
                                                               "reboot_loganalyzer_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "..", "..", "..", "..",
                                                               "tools", "loganalyzer",
                                                               "loganalyzer_common_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)
