import pytest

from ngts.tools.test_utils.switch_recovery import check_switch_connectivity


@pytest.fixture(scope='session', autouse=True)
def prepare_scp_test(prepare_scp):
    return


@pytest.fixture(scope='function', autouse=True)
def recover_after_aaa(topology_obj, engines):
    yield
    check_switch_connectivity(topology_obj, engines)
