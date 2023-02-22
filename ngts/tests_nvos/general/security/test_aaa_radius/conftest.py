import logging
import pytest
from ngts.nvos_tools.system.System import System
from infra.tools.general_constants.constants import DefaultConnectionValues


def restore_original_engine_credentials(engines):
    '''
    @summary:
        in this fixture we will restore default credentials to dut engine
    '''
    logging.info("Restoring default credentials, and logging in to switch")
    engines.dut.update_credentials(username=DefaultConnectionValues.ADMIN,
                                   password=DefaultConnectionValues.DEFAULT_PASSWORD)


@pytest.fixture(scope='function')
def clear_all_radius_configurations(engines):
    '''
    @summary:
        in this fixture we want to clear all the radius configurations and disable the feature
    '''
    yield

    logging.info("re-adjusting auth. method back to local only")
    engines.dut.run_cmd('sudo config aaa authentication login local')
    engines.dut.run_cmd("sudo ln -s  /bin/bash /usr/bin/sonic-launch-shell")
    logging.info("Removing All radius configurations using unset command")
    system = System(None)
    system.aaa.radius.unset(apply=True, ask_for_confirmation=True)
