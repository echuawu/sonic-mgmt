import pytest

from ngts.tests_nvos.general.security.conftest import check_if_need_remote_reboot_to_recover_dut


@pytest.fixture(scope='session', autouse=True)
def prepare_scp_test(prepare_scp):
    return


@pytest.fixture(scope='function', autouse=True)
def recover_after_aaa(topology_obj, engines):
    yield
    check_if_need_remote_reboot_to_recover_dut(topology_obj, engines)
