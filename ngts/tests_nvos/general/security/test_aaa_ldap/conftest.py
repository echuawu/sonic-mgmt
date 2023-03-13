import logging
import allure
import pytest
from ngts.nvos_tools.system.System import System


def disable_ldap_feature(dut_engine):
    '''
    @summary: in this test case we want to remove ldap configuration as a remote aaa method
    '''
    logging.info("re-adjusting auth. method back to local only")
    dut_engine.run_cmd('nv set system aaa authentication order local')
    dut_engine.run_cmd("nv set system aaa authentication fallback disabled")
    dut_engine.run_cmd("nv set system aaa authentication fallback disabled")
    dut_engine.run_cmd("nv config apply -y")


@pytest.fixture(scope='function')
def remove_ldap_configurations(engines):
    '''
    @summary: remove all ldap configurations
    '''
    yield

    disable_ldap_feature(engines.dut)
    with allure.step("Removing ldap configurations"):
        logging.info("Removing ldap configurations")
        system = System()
        system.aaa.ldap.unset(apply=True, ask_for_confirmation=True)
