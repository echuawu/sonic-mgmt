import pytest
import logging

from infra.tools.linux_tools.linux_tools import scp_file
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthConsts


@pytest.fixture(scope='session', autouse=True)
def upload_dummy_file_to_switch(engines):
    """
    @summary: Upload a dummy text file to the switch, that will be used in tests for scp verification
    """
    engines.dut.run_cmd('')
    logging.info('Upload a dummy text file to the switch')
    scp_file(engines.dut, AuthConsts.DUMMY_FILE_SHARED_LOCATION, AuthConsts.SWITCH_NON_PRIVILEGED_PATH)

    yield

    logging.info('Remove dummy file from the switch')
    engines.dut.run_cmd(f'rm -f {AuthConsts.SWITCH_NON_PRIVILEGED_PATH}/{AuthConsts.DUMMY_FILE_NAME}')
