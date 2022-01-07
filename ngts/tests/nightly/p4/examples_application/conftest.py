import pytest
import os
import json
from ngts.constants.constants import P4ExamplesConsts
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_wrappers.sonic.sonic_p4_examples_clis import P4ExamplesCli
from ngts.cli_wrappers.sonic.sonic_vxlan_clis import SonicVxlanCli
from ngts.tests.nightly.app_extension.app_extension_helper import verify_app_container_up_and_repo_status_installed


VXLAN_TUNNEL_NAME = "tunnel1"
TUNNEL_SRC_IP = "1.1.1.1"


@pytest.fixture(scope="session", autouse=False)
def skipping_p4_examples_test_case_for_spc1(platform_params):
    """
    If platform is SPC1, skip all p4 examples test cases
    :param platform_params: platform_params fixture
    """
    if not is_p4_examples_supported(platform_params):
        pytest.skip("Skipping p4-examples test cases as SPC1 does not support it")


def is_p4_examples_supported(platform_params):
    """
    If platform is SPC1,p4-examples dose not support
    :param platform_params: platform_params fixture
    :return: True is supported, else False
    """
    return 'SN2' not in platform_params.hwsku


@pytest.fixture(scope="session", autouse=False)
def skipping_p4_examples_test_case(engines, skipping_p4_examples_test_case_for_spc1):
    """
    If p4-examples is not installed, skipping all p4-examples test cases execution
    :param engines: engines fixture
    :param skipping_p4_examples_test_case_for_spc1: skipping_p4_examples_test_case_for_spc1 fixture
    """
    try:
        verify_app_container_up_and_repo_status_installed(engines.dut, P4ExamplesConsts.APP_NAME, "")
    except Exception:
        pytest.skip(f"Skipping {P4ExamplesConsts} test cases due to {P4ExamplesConsts.APP_NAME} is not installed.")


@pytest.fixture(scope='session')
def p4_example_default_feature():
    """
    Return the feature which will be started by default after the installation
    :return: the default feature name in p4 examples
    """
    return P4ExamplesConsts.VXLAN_BM_FEATURE_NAME


@pytest.fixture(scope='module', autouse=True)
def p4_examples_config(engines, skipping_p4_examples_test_case, run_test_only):
    """
    Fixture used to configure the vxlan on sonic switch which will be used to enable the vxlan_bm feature
    in the p4 examples.
    :param engines: engines fixture
    :param skipping_p4_examples_test_case: skipping_p4_examples_test_case fixture
    :param run_test_only: run_test_only fixture, after the reboot, the configure should not be configured again, and the
                            run_test_only will be set to true
    :return:
    """
    if not run_test_only:
        base_config_db = '{"VNET": {"Vnet1": {"vxlan_tunnel": "tunnel1","vni": "1"}}}'
        SonicVxlanCli.add_vtep(engines.dut, VXLAN_TUNNEL_NAME, TUNNEL_SRC_IP)
        engines.dut.run_cmd(f'sonic-cfggen -a {json.dumps(base_config_db)} --write-to-db')
    yield
    if not run_test_only:
        engines.dut.run_cmd('redis-cli -n 4 HDEL "VNET|Vnet1" "vni" "vxlan_tunnel"')
        SonicVxlanCli.del_vtep(engines.dut, VXLAN_TUNNEL_NAME)


@pytest.fixture(scope='session', autouse=False)
def p4_examples_installation(engines, run_test_only):
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


@pytest.fixture(autouse=False)
def ignore_loganalyzer_exceptions_withbugs(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of bug.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    # TODO: need to remove this fixture after the ticket resolved
    # #2919698: "ERR swss#orchagent: :- addOperation: Vxlan tunnel 'tunnel1' is already exists"
    # #2890809: "ERR syncd#SDK: [BRIDGE.ERR] __sdk_bridge_db_get_bridge failed (Entry Not Found)."
    # #2920504: "ERR swss#vxlanmgrd: :- doVxlanCreateTask: Cannot create vxlan Vxlan1"
    if loganalyzer:
        ignoreRegex = [
            ".*ERR syncd#SDK.*__sdk_bridge_db_get_bridge failed.*",
            ".*ERR swss#orchagent.*addOperation.*Vxlan tunnel .* is already exists",
            ".*ERR swss#vxlanmgrd.*doVxlanCreateTask: Cannot create vxlan.*"
        ]
        loganalyzer.ignore_regex.extend(ignoreRegex)
