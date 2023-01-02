import pytest
import logging
import re
import os
from ngts.tests_nvos.general.security.test_login_ssh_notification.constants import LoginSSHNotificationConsts


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def login_source_ip_address(engines):
    '''
    @summary: extract ip address initiating the ssh connection
    '''
    logger.info("Extract login IP address")
    output = os.popen('ip -o route get {}'.format(engines.dut.ip)).read()
    src_ip = re.findall(LoginSSHNotificationConsts.SRC_IP_ADDRESS_REGEX, output)[0]
    logger.info("Login source IP address is {}".format(src_ip))
    return src_ip
