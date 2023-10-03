import pytest
import logging

from infra.tools.linux_tools.linux_tools import scp_file
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthConsts


@pytest.fixture(scope='session', autouse=True)
def prepare_scp_test(engines):
    """
    @summary: Upload a dummy text file to the switch, that will be used in tests for scp verification
    """
    admin_monitor_mutual_group = 'adm'

    logging.info('Prepare directory for admin users only')
    engines.dut.run_cmd(f'mkdir {AuthConsts.SWITCH_SCP_TEST_DIR}')
    engines.dut.run_cmd(f'mkdir {AuthConsts.SWITCH_ADMINS_DIR}')
    engines.dut.run_cmd(f'chmod 770 {AuthConsts.SWITCH_ADMINS_DIR}')
    engines.dut.run_cmd(f'echo "Alon The King" > {AuthConsts.SWITCH_ADMIN_SCP_DOWNLOAD_TEST_FILE}')

    logging.info('Prepare non-privileged directory')
    engines.dut.run_cmd(f'mkdir {AuthConsts.SWITCH_MONITORS_DIR}')
    engines.dut.run_cmd(f'chgrp {admin_monitor_mutual_group} {AuthConsts.SWITCH_MONITORS_DIR}')
    engines.dut.run_cmd(f'chmod 770 {AuthConsts.SWITCH_MONITORS_DIR}')
    engines.dut.run_cmd(f'echo "Alon The King" > {AuthConsts.SWITCH_MONITOR_SCP_DOWNLOAD_TEST_FILE}')
    engines.dut.run_cmd(f'chgrp {admin_monitor_mutual_group} {AuthConsts.SWITCH_MONITOR_SCP_DOWNLOAD_TEST_FILE}')
    engines.dut.run_cmd(f'chmod 770 {AuthConsts.SWITCH_MONITOR_SCP_DOWNLOAD_TEST_FILE}')

    yield

    logging.info('Clean scp test files')
    engines.dut.run_cmd(f'rm -rf {AuthConsts.SWITCH_SCP_TEST_DIR}')
