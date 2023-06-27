import logging
from ngts.tools.test_utils import allure_utils as allure
import pytest

from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts


def disable_ldap_feature(dut_engine):
    '''
    @summary: in this test case we want to remove ldap configuration as a remote aaa method
    '''
    logging.info("re-adjusting auth. method back to local only")
    dut_engine.run_cmd('nv set system aaa authentication order local')
    dut_engine.run_cmd("nv set system aaa authentication fallback disabled")
    dut_engine.run_cmd("nv set system aaa authentication fallback disabled")
    dut_engine.run_cmd("nv config apply -y")


@pytest.fixture(scope='function', autouse=False)
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


@pytest.fixture(scope='session', autouse=True)
def alias_docker_ldap_server_dns(engines):
    """
    @summary: To allow the switch work with the docker ldap server with certificate,
        we need to add an alias of the server's ip to a specific domain name.
        Also, as cleanup step, remove the line of the added alias after the tests.
    """
    with allure.step('Before tests: Verify that docker ldap server dns has alias in the switch'):
        output = engines.dut.run_cmd('cat /etc/hosts')
        if LdapConsts.DOCKER_LDAP_SERVER_HOST_ALIAS not in output:
            with allure.step('Switch does not have existing alias for the docker ldap server. Add the alias'):
                engines.dut.run_cmd(f'echo "{LdapConsts.DOCKER_LDAP_SERVER_HOST_ALIAS} " | sudo tee -a /etc/hosts')

            with allure.step('Verify alias wad added'):
                output = engines.dut.run_cmd('cat /etc/hosts')
                assert LdapConsts.DOCKER_LDAP_SERVER_HOST_ALIAS in output, \
                    f'Error: docker server alias was not found in /etc/hosts .\n' \
                    f'/etc/hosts content: {output}\n' \
                    f'Expected: {LdapConsts.DOCKER_LDAP_SERVER_HOST_ALIAS}'

    yield

    with allure.step('After tests: Remove docker ldap server alias from the switch'):
        engines.dut.run_cmd("sudo sed -i '$ d' /etc/hosts")
