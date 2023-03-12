import logging
import allure
import pytest
from ngts.nvos_tools.system.System import System


@pytest.fixture(scope='function')
def remove_ldap_configurations(engines):
    '''
    @summary: remove all ldap configurations
    '''
    yield

    logging.info("re-adjusting auth. method back to local only")
    engines.dut.run_cmd('nv set system aaa authentication order local')
    engines.dut.run_cmd("nv set system aaa authentication fallback disabled")
    engines.dut.run_cmd("nv set system aaa authentication fallback disabled")
    engines.dut.run_cmd("nv config apply -y")
    with allure.step("Removing ldap configurations"):
        logging.info("Removing ldap configurations")
        system = System()
        system.aaa.ldap.unset(apply=True, ask_for_confirmation=True)
