import random

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
    verify_switch_ssh_property(
        engines=engines,
        property_name=SshHardeningConsts.PROTOCOL,
        expected_value=SshHardeningConsts.VALUES[SshHardeningConsts.PROTOCOL],
        value_extraction_function=get_ssh_server_protocol
    )


@pytest.mark.security
@pytest.mark.simx
def test_ssh_compression(engines):
    """
    @summary: verify the change of Compression in sshd_config

        Steps:
        1. Verify that the new configuration is set
    """
    verify_switch_ssh_property(
        engines=engines,
        property_name=SshHardeningConsts.COMPRESSION,
        expected_value=SshHardeningConsts.VALUES[SshHardeningConsts.COMPRESSION],
        value_extraction_function=get_ssh_server_compression_state
    )


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
    verify_switch_ssh_property(
        engines=engines,
        property_name=SshHardeningConsts.CIPHERS,
        expected_value=SshHardeningConsts.VALUES[SshHardeningConsts.CIPHERS],
        value_extraction_function=get_ssh_server_ciphers
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=True,
        option_to_check=SshHardeningConsts.CIPHERS
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=False,
        option_to_check=SshHardeningConsts.CIPHERS
    )


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
    verify_switch_ssh_property(
        engines=engines,
        property_name=SshHardeningConsts.MACS,
        expected_value=SshHardeningConsts.VALUES[SshHardeningConsts.MACS],
        value_extraction_function=get_ssh_server_macs
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=True,
        option_to_check=SshHardeningConsts.MACS
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=False,
        option_to_check=SshHardeningConsts.MACS
    )


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
    verify_switch_ssh_property(
        engines=engines,
        property_name=SshHardeningConsts.KEX_ALGOS,
        expected_value=SshHardeningConsts.VALUES[SshHardeningConsts.KEX_ALGOS],
        value_extraction_function=get_ssh_server_kex_algorithms
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=True,
        option_to_check=SshHardeningConsts.KEX_ALGOS
    )

    verify_ssh_with_option(
        engines=engines,
        good_flow=False,
        option_to_check=SshHardeningConsts.KEX_ALGOS
    )


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
