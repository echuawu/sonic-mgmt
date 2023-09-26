import pytest

from ngts.tests_nvos.general.security.ssh_hardening.constants import SshHardeningConsts
from ngts.tools.test_utils import allure_utils as allure
import logging
from ssh_hardening_test_utils import *


@pytest.mark.security
@pytest.mark.simx
def test_ssh_protocol(engines):
    """
    @summary: verify the change of Protocol in sshd_config

        Steps:
        1. Verify that the new configuration is set
    """
    with allure.step('Verify that new protocol is set'):
        with allure.step("Run verbose ssh (from client machine) to get switch ssh protocol"):
            protocol = get_ssh_server_protocol(engines.dut)
            logging.info(f'Protocol: {protocol}')

        with allure.step('Verify that protocol is 2'):
            assert protocol == SshHardeningConsts.PROTOCOL, f'Protocol not as expected\n' \
                                                            f'Expected: {SshHardeningConsts.PROTOCOL}\n' \
                                                            f'Actual: {protocol}'


@pytest.mark.security
@pytest.mark.simx
def test_ssh_compression(engines):
    """
    @summary: verify the change of Compression in sshd_config

        Steps:
        1. Verify that the new configuration is set
    """
    with allure.step('Verify from client that new protocol is set'):
        pass


@pytest.mark.security
@pytest.mark.simx
def test_ssh_ciphers(engines):
    """
    @summary: verify the change of Ciphers in sshd_config

        Steps:
        1. Verify that the new configuration is set
        2. good flow: ssh the switch with valid cipher - expect success
        3. bad flow: ssh the switch with invalid cipher - expect fail
    """
    pass


@pytest.mark.security
@pytest.mark.simx
def test_ssh_macs(engines):
    """
    @summary: verify the change of MACs in sshd_config

        Steps:
        1. Verify that the new configuration is set
        2. good flow: ssh the switch with valid MAC - expect success
        3. bad flow: ssh the switch with invalid MAC - expect fail
    """
    pass


@pytest.mark.security
@pytest.mark.simx
def test_ssh_kex_algorithms(engines):
    """
    @summary: verify the change of KexAlgorithms in sshd_config

        Steps:
        1. Verify that the new configuration is set
        2. good flow: ssh the switch with valid KEX-algorithm - expect success
        3. bad flow: ssh the switch with invalid KEX-algorithm - expect fail
    """
    pass


@pytest.mark.security
@pytest.mark.simx
def test_ssh_auth_public_key_types(engines):
    """
    @summary: verify the change of PubkeyAcceptedKeyTypes in sshd_config

        Steps:
        1. Verify that the new configuration is set
        2. good flow: ssh the switch with key of valid type - expect success
        3. bad flow: ssh the switch with key of invalid type - expect fail
    """
    pass


@pytest.mark.security
@pytest.mark.simx
def test_ssh_host_key_algorithms(engines):
    """
    @summary: verify the change of HostKeyAlgorithms in sshd_config

        Steps:
        1. Verify that the new configuration is set
    """
    pass
