import random
import pytest
import logging

from ngts.tests_nvos.general.security.security_test_tools.tool_classes.SecuritySshTool import SecuritySshTool
from ngts.tests_nvos.general.security.ssh_hardening.constants import SshHardeningConsts


@pytest.fixture(scope='function')
def generate_ssh_auth_keypairs():
    logging.info('Generate valid typed key pair')
    SecuritySshTool.generate_auth_keypair(key_type=random.choice(SshHardeningConsts.VALUES[SshHardeningConsts.AUTH_KEY_TYPES]),
                                          dst_path=SshHardeningConsts.VALID_AUTH_KEY_PATH)
    SecuritySshTool.generate_auth_keypair(
        key_type=random.choice(SshHardeningConsts.INVALID_VALUES[SshHardeningConsts.AUTH_KEY_TYPES]),
        dst_path=SshHardeningConsts.INVALID_AUTH_KEY_PATH)

    yield

    logging.info('Remove generated key pairs')
    SecuritySshTool.rm_auth_keypair(key_path=SshHardeningConsts.VALID_AUTH_KEY_PATH)
    SecuritySshTool.rm_auth_keypair(key_path=SshHardeningConsts.INVALID_AUTH_KEY_PATH)


@pytest.fixture(scope='function')
def upload_test_auth_keys_to_ssh_server(engines, generate_ssh_auth_keypairs):
    logging.info('Upload valid typed key to switch')
    SecuritySshTool.upload_auth_key_to_server(key_path=f'{SshHardeningConsts.VALID_AUTH_KEY_PATH}.pub',
                                              server_engine=engines.dut)
    SecuritySshTool.upload_auth_key_to_server(key_path=f'{SshHardeningConsts.INVALID_AUTH_KEY_PATH}.pub',
                                              server_engine=engines.dut)

    yield

    logging.info('Clear authorized keys on switch')
    engines.dut.run_cmd('rm -f ~/.ssh/authorized_keys')
