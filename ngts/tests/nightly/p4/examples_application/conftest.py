import pytest
import json

from ngts.constants.constants import P4ExamplesConsts
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
def skipping_p4_examples_test_case(cli_objects, skipping_p4_examples_test_case_for_spc1):
    """
    If p4-examples is not installed, skipping all p4-examples test cases execution
    :param cli_objects: cli_objects fixture
    :param skipping_p4_examples_test_case_for_spc1: skipping_p4_examples_test_case_for_spc1 fixture
    """
    try:
        verify_app_container_up_and_repo_status_installed(cli_objects.dut, P4ExamplesConsts.APP_NAME, "")
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
def p4_examples_config(cli_objects, engines, skipping_p4_examples_test_case, run_test_only):
    """
    Fixture used to configure the vxlan on sonic switch which will be used to enable the vxlan_bm feature
    in the p4 examples.
    :param cli_objects: cli_objects fixture
    :param engines: engines fixture
    :param skipping_p4_examples_test_case: skipping_p4_examples_test_case fixture
    :param run_test_only: run_test_only fixture, after the reboot, the configure should not be configured again, and the
                            run_test_only will be set to true
    :return:
    """
    if not run_test_only:
        base_config_db = '{"VNET": {"Vnet1": {"vxlan_tunnel": "tunnel1","vni": "1"}}}'
        cli_objects.dut.vxlan.add_vtep(VXLAN_TUNNEL_NAME, TUNNEL_SRC_IP)
        engines.dut.run_cmd(f'sonic-cfggen -a {json.dumps(base_config_db)} --write-to-db')
    yield
    if not run_test_only:
        engines.dut.run_cmd('redis-cli -n 4 HDEL "VNET|Vnet1" "vni" "vxlan_tunnel"')
        cli_objects.dut.vxlan.del_vtep(VXLAN_TUNNEL_NAME)


@pytest.fixture(scope='session', autouse=False)
def p4_examples_installation(engines, cli_objects, run_test_only):
    """
    Fixture used to install the p4 examples and enable the application, and uninstall the application after test.
    :param engines: engines fixture
    :param run_test_only: run_test_only fixture
    :param cli_objects: cli_objects fixture
    """
    if not run_test_only:
        cli_objects.dut.app_ext.add_repository(P4ExamplesConsts.APP_NAME, repository_name=P4ExamplesConsts.REPO_NAME)
        cli_objects.dut.app_ext.install_app(P4ExamplesConsts.APP_NAME, version=P4ExamplesConsts.APP_VERSION)
        cli_objects.dut.app_ext.enable_app(P4ExamplesConsts.APP_NAME)
    yield
    if not run_test_only:
        cli_objects.dut.app_ext.disable_app(P4ExamplesConsts.APP_NAME)
        cli_objects.dut.app_ext.uninstall_app(P4ExamplesConsts.APP_NAME)
        cli_objects.dut.app_ext.remove_repository(P4ExamplesConsts.APP_NAME)


def verify_running_feature(expected_feature, cli_obj):
    """
    Verify the feature running in the p4 docker is as expected
    :param expected_feature: expected feature name
    :param cli_obj: cli_obj object
    """
    running_feature = cli_obj.p4_examples.get_p4_example_running_feature()
    assert running_feature == expected_feature, \
        f"Expect no feature is running, but {running_feature} is running in the {P4ExamplesConsts.APP_NAME}"
