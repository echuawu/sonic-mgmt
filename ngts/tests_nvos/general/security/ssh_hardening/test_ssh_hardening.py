import pytest

from ngts.nvos_tools.infra.PexpectTool import PexpectTool
from ssh_hardening_test_utils import *


@pytest.mark.security
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
def test_ssh_auth_public_key_types(engines, upload_test_auth_keys_to_ssh_server):
    """
    @summary: verify the change of PubkeyAcceptedKeyTypes in sshd_config

        Steps:
        1. good flow: ssh the switch with key of valid type - expect success
        2. bad flow: ssh the switch with key of invalid type - expect fail
    """
    with allure.step('Good flow: ssh the switch with valid auth key. Expect success'):
        pexpect = PexpectTool(
            spawn_cmd=f'ssh -o StrictHostKeyChecking=no '
                      f'-i {SshHardeningConsts.VALID_AUTH_KEY_PATH} {engines.dut.username}@{engines.dut.ip}')
        pexpect.expect(f'{engines.dut.username}@.*~', error_message='Expected login success, but failed')
        pexpect.expect('.*')
        pexpect.sendline('logout')

    with allure.step('Bad flow: ssh the switch with valid auth key. Expect fail (enter password prompt)'):
        pexpect = PexpectTool(
            spawn_cmd=f'ssh -o StrictHostKeyChecking=no '
                      f'-i {SshHardeningConsts.INVALID_AUTH_KEY_PATH} {engines.dut.username}@{engines.dut.ip}')
        pexpect.expect('password:',
                       error_message='Login unexpectedly succeeded. Expected login fail (enter password prompt)')
