import random

import pytest

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.tests_nvos.general.security.tpm_attestation.helpers import *
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.tpm
def test_only_aik_file_at_first(engines):
    """
    Verify that tpm dir contains only AIK file, when no tpm actions done before.

    1. show tpm dir
    2. verify dir contains only AIK file
    """
    verify_only_aik_at_tpm_dir(engines)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_upload_bad_tpm_filename(test_api, engines, remote_engine):
    """
    Verify that upload with bad filename param fails

    1. upload with bad filename param
    2. verify upload fail
    """
    TestToolkit.tested_api = test_api

    with allure.step('upload with bad filename param'):
        bad_filename = 'zz'
        res = System().security.tpm.action_upload(bad_filename, get_scp_url(remote_engine, bad_filename))
    with allure.step('verify upload failed'):
        res.verify_result(False)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_upload_aik(test_api, engines, remote_engine):
    """
    Verify that upload AIK action works

    1. upload AIK file
    2. sanity check for uploaded file
    """
    TestToolkit.tested_api = test_api

    with allure.step('upload AIK file'):
        System().security.tpm.action_upload(AIK_FILENAME, get_scp_url(remote_engine, AIK_FILENAME)).verify_result()
    with allure.step('sanity check for uploaded file'):
        sanity_check_uploaded_file(engines, AIK_FILE_PATH, remote_engine.ip, remote_engine.username,
                                   remote_engine.password, f'{REMOTE_PATH}/{AIK_FILENAME}')


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_upload_quote_before_generate(test_api, engines, remote_engine):
    """
    Verify that upload quote fails when there is no generated quote

    1. upload quote
    3. verify failure
    """
    TestToolkit.tested_api = test_api

    with allure.step('upload quote'):
        res = System().security.tpm.action_upload(QUOTE_FILENAME, get_scp_url(remote_engine, QUOTE_FILENAME))
    with allure.step('verify upload fail'):
        res.verify_result(False)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_generate_quote_bad_param(test_api, engines):
    """
    Verify that generate quote with bad param fails and not producing any quote file

    1. attempt generate quote with bad param
    2. verify error
    3. verify no quote file generated
    """
    TestToolkit.tested_api = test_api

    with allure.step('attempt generate quote with bad param, expect error'):
        tpm = System().security.tpm
        valid_algo = random.choice(list(SUPPORTED_ALGORITHMS))
        invalid_algo = random.choice(list(UNSUPPORTED_ALGORITHMS))
        # empty param
        tpm.action_generate_quote().verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, algorithm=valid_algo).verify_result(False)
        tpm.action_generate_quote(nonce=VALID_NONCE_PARAM).verify_result(False)
        tpm.action_generate_quote(nonce=VALID_NONCE_PARAM, algorithm=valid_algo).verify_result(False)
        # bad param
        bad = 'zz'
        tpm.action_generate_quote(pcrs=bad, nonce=VALID_NONCE_PARAM).verify_result(False)
        tpm.action_generate_quote(pcrs=bad, nonce=VALID_NONCE_PARAM, algorithm=valid_algo).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=bad).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=bad, algorithm=valid_algo).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=VALID_NONCE_PARAM, algorithm=bad).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=VALID_NONCE_PARAM, algorithm=invalid_algo).verify_result(False)
        # too large nonce
        long_str = ''.join(['a' for _ in range(MAX_CHARS_NONCE + 1)])
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=long_str).verify_result(False)
        tpm.action_generate_quote(pcrs=VALID_PCRS_PARAM, nonce=long_str, algorithm=valid_algo).verify_result(False)
    with allure.step('verify no quote file generated'):
        verify_only_aik_at_tpm_dir(engines)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_generate_quote(test_api, engines, devices):
    """
    Verify that generate quote works

    1. generate quote
    2. verify success
    3. verify quote file generated
    4. sanity check for generated file
    """
    TestToolkit.tested_api = test_api

    with allure.step('generate quote'):
        tpm = System().security.tpm
        tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM).verify_result()
        for valid_algo in list(SUPPORTED_ALGORITHMS):
            tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM, algorithm=valid_algo).verify_result()
    with allure.step('verify quote file generated'):
        tpm_files = TpmTool(engines.dut).get_files_in_tpm_dir()
        assert QUOTE_FILENAME in tpm_files, \
            f'''quote file "{QUOTE_FILENAME}" was not generated
            tpm dir content: {tpm_files}'''
    with allure.step('sanity check for generated file'):
        sanity_check_generated_quote(engines, VALID_NONCE_PARAM)


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.tpm
def test_upload_quote(test_api, engines, remote_engine):
    """
    Verify that upload quote works

    1. generate quote
    2. upload quote
    3. sanity check for uploaded file
    """
    TestToolkit.tested_api = test_api

    with allure.step('generate quote'):
        tpm = System().security.tpm
        tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM).verify_result()
    with allure.step('upload quote'):
        tpm.action_upload(QUOTE_FILENAME, get_scp_url(remote_engine, QUOTE_FILENAME)).verify_result()
    with allure.step('sanity check for uploaded file'):
        sanity_check_uploaded_file(engines, QUOTE_FILE_PATH, remote_engine.ip, remote_engine.username,
                                   remote_engine.password, f'{REMOTE_PATH}/{QUOTE_FILENAME}')


@pytest.mark.tpm
def test_generate_quote_overrides_file(engines):
    """
    Verify generate quote overrides an existing quote file

    1. generate dummy file as quote file
    2. generate quote again
    3. verify the original quote file was overridden
    """
    with allure.step('generate dummy file as "original quote"'):
        dummy_quote_content = 'abcalonxyz'
        engines.dut.run_cmd(f'echo {dummy_quote_content} > /tmp/{QUOTE_FILENAME}')
        engines.dut.run_cmd(f'sudo mv /tmp/{QUOTE_FILENAME} {QUOTE_FILE_PATH}')
    with allure.step('generate quote again'):
        System().security.tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM).verify_result()
    with allure.step('verify the original quote file was overridden'):
        cur_quote_content = TpmTool(engines.dut).get_quote_file_content()
        assert cur_quote_content != dummy_quote_content, \
            f'''quote file content same as original dummy quote (probably was not overridden)
            content: {dummy_quote_content}'''


@pytest.mark.tpm
def test_tpm_reboot_cases(engines, devices, save_local_timezone):
    """
    Verify that:
        1. AIK file is re-generated in every boot
        2. reboot keeps quote file

     1. before reboot
         1. get AIK file creation time
         2. generate quote
     2. reboot
     3. checks after reboot
        1. verify boot generated new AIK file
            1. get new AIK file creation time
            2. verify creation times are different
        2. verify reboot keeps quote file
    """
    with allure.step('steps before reboot'):
        with allure.step('get current AIK file creation time'):
            aik_time1 = get_file_creation_time(engines.dut, AIK_FILE_PATH)
        with allure.step('generate quote'):
            system = System()
            system.security.tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM).verify_result()
            quote_time1 = get_file_creation_time(engines.dut, QUOTE_FILE_PATH)
    with allure.step('reboot'):
        system.action('reboot', 'force', expect_reboot=True, output_format='')
    with allure.step('checks after reboot'):
        with allure.step('verify boot generated new AIK file'):
            with allure.step('get new AIK file creation time'):
                aik_time2 = get_file_creation_time(engines.dut, AIK_FILE_PATH)
            with allure.step('verify creation times are different'):
                assert aik_time1 != aik_time2, \
                    f'''creation times are equal but expected to be different.
                    before reboot: {aik_time1}
                    after reboot: {aik_time2}'''
        with allure.step('verify quote file kept after reboot'):
            quote_time2 = get_file_creation_time(engines.dut, QUOTE_FILE_PATH)
            assert quote_time1 == quote_time2, \
                f'''creation times are different but expected to be equal.
                before reboot: {quote_time1}
                after reboot: {quote_time2}'''


# TODO: understand how to upgrade here
@pytest.mark.skip(reason='Skipped until there is GA version with the feature')
@pytest.mark.tpm
def test_tpm_upgrade_cases(engines, devices):
    """
    Verify that quote is removed after upgrade

     1. before upgrade
         1. generate quote
     2. upgrade
     3. checks after upgrade
        1. verify quote file is removed
    """
    with allure.step('before upgrade steps'):
        with allure.step('generate quote'):
            system = System()
            system.security.tpm.action_generate_quote(VALID_PCRS_PARAM, VALID_NONCE_PARAM).verify_result()
    with allure.step('upgrade'):
        pass  # TODO: understand how
    with allure.step('checks after upgrade'):
        with allure.step('verify quote file is removed'):
            verify_only_aik_at_tpm_dir(engines)
