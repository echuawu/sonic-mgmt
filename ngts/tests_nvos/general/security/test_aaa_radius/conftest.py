import logging
import pytest
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.conftest import check_if_need_remote_reboot_to_recover_dut


@pytest.fixture(scope='session', autouse=True)
def prepare_scp_test(prepare_scp):
    return


@pytest.fixture(scope='function', autouse=True)
def recover_after_aaa(topology_obj, engines):
    yield
    check_if_need_remote_reboot_to_recover_dut(topology_obj, engines)


@pytest.fixture(scope='function')
def clear_all_radius_configurations(engines):
    '''
    @summary:
        in this fixture we want to clear all the radius configurations and disable the feature
    '''
    yield

    logging.info("re-adjusting auth. method back to local only")
    engines.dut.run_cmd('nv set system aaa authentication order local')
    engines.dut.run_cmd("nv set system aaa authentication fallback disabled")
    engines.dut.run_cmd("nv set system aaa authentication fallback disabled")
    engines.dut.run_cmd("nv config apply -y")
    logging.info("Removing All radius configurations using unset command")
    system = System(None)
    system.aaa.radius.unset(apply=True, ask_for_confirmation=True)
