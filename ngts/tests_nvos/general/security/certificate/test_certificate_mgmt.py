import pytest
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_constants.constants_nvos import CertificateFiles, SyslogConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import ApiType
import logging
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.certificate
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_certificate_commands(engines, test_api):
    """
    Test certificate mgmt commands:
        1. nv action import system security certificate <cert-id_1> uri-bundle <https://URI>
        2. nv action import system security certificate <cert-id_2> uri-public-key <scp://URI> uri-private-key <scp://URI>
        3. nv set system api certificate <cert-id_1>
        4. nv action delete system security certificate
    """
    TestToolkit.tested_api = test_api
    system = System()
    player = engines['sonic_mgmt']
    cert_id_bundle = 'cert_id_1'
    cert_id_public_private = "cert_id_2"
    cert_list = []

    with allure.step("Init test params"):
        system.security.certificate.set_certificate_type(CertificateFiles.CERTIFICATE)

    with allure.step('import system security certificate {cert_id_bundle} uri-bundle with URI'):
        bundle = system.security.certificate.generate_uri_for_type(player, CertificateFiles.URI_BUNDLE)
        system.security.certificate.import_certificate(import_type=CertificateFiles.URI_BUNDLE, cert_id=cert_id_bundle,
                                                       uri1=bundle,
                                                       passphrase=CertificateFiles.BUNDLE_CERTIFICATE_CURRENT_PASSWORD)
        verify_imported_certificate(engines, system, cert_id_bundle, CertificateFiles.URI_BUNDLE,
                                    CertificateFiles.PASSPHRASE)
        cert_list.append(cert_id_bundle)

    with allure.step('Import system security certificate {cert_id_public_private} with public and private key'):
        public, private = system.security.certificate.generate_uri_for_type(player, CertificateFiles.PUBLIC_PRIVATE)
        system.security.certificate.import_certificate(import_type=CertificateFiles.PUBLIC_PRIVATE,
                                                       cert_id=cert_id_public_private, uri1=public, uri2=private)
        verify_imported_certificate(engines, system, cert_id_public_private, CertificateFiles.PUBLIC_KEY_FILE,
                                    CertificateFiles.PRIVATE_KEY_FILE)
        cert_list.append(cert_id_public_private)

    with allure.step(f'Install certificate'):
        for cert in cert_list:
            system.api.certificate.set(cert, apply=True).verify_result()
            verify_show_api_output(system, cert)

    with allure.step("Verify certificate installation"):
        _verify_certificate(engines, system, cert_list)

    with allure.step(f'Unset certificates'):
        system.api.certificate.unset(op_param=cert_list[0], apply=True).verify_result()
        verify_show_api_output(system, CertificateFiles.DEFAULT_CERTIFICATE)

    with allure.step("Clear installed certificates"):
        _clear_certificates(system, cert_list)


@pytest.mark.system
@pytest.mark.certificate
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_ca_certificate_commands(engines, test_api):
    TestToolkit.tested_api = test_api
    system = System()
    player = engines['sonic_mgmt']
    ca_cert_id = "ca_cert_id"

    with allure.step("Init test params"):
        system.security.certificate.set_certificate_type(CertificateFiles.CA_CERTIFICATE)
        system.api.certificate.set_certificate_type(CertificateFiles.CA_CERTIFICATE)
        uri = system.security.certificate.generate_uri_for_type(player, CertificateFiles.URI)

    with allure.step('import system security certificate {cert_id_bundle} uri-bundle with URI'):
        system.security.certificate.import_certificate(import_type=CertificateFiles.URI, cert_id=ca_cert_id,
                                                       uri1=uri)
        verify_imported_certificate(engines, system, ca_cert_id, CertificateFiles.URI)

    with allure.step("Verify certificate installation"):
        _verify_certificate(engines, system, [ca_cert_id])

    with allure.step("Clear installed certificates"):
        _clear_certificates(system, [ca_cert_id])


def _verify_certificate(engines, system, cert_list):
    with allure.step('verify the show command output'):
        for cert in cert_list:
            verify_show_security_ouput(system, cert, True)

    with allure.step(f'Run show system security certificate "invalid_id" and verify error message'):
        show_output = system.security.certificate.show(op_param="invalid_id", should_succeed=False)
        assert "Error: The requested item does not exist." in show_output, f"Expected to find error message. " \
                                                                           f"Got: {show_output}"

    '''with allure.step("Run open api command using imported certificate"):
        send_open_api_cmd(engines.dut, cert_list[0], False)'''


def _clear_certificates(system, cert_list):
    with allure.step('Delete all certificates'):
        for cert in cert_list:
            system.security.certificate.action_delete(cert)
            verify_show_security_ouput(system, cert, False)

    with allure.step('Verify the show command output after delete'):
        show_output = system.security.certificate.show()
        assert '{}' in show_output, f"Expected to see 'No Data' after deleting all certificates. " \
                                    "\nActual output: {show_output}"


def send_open_api_cmd(dut_engine, cert_id, should_pass):
    url = f"curl --cacert {cert_id} " \
          f"-u {dut_engine.username}" \
          f" -X GET https://{dut_engine.ip}/nvue_v1/system/version"

    output = dut_engine.run_cmd(url)
    if should_pass:
        assert "version" in output, "Failed to send open api command using ca-certificate"
    else:
        assert "Failed" in output, "Open api command passed while expected to fail"


def verify_show_api_output(system, expected_cert_id):
    show_api_output = OutputParsingTool.parse_json_str_to_dictionary(system.api.show()).get_returned_value()
    certificate_value = show_api_output.get(CertificateFiles.CERTIFICATE, None)
    assert certificate_value, f"{CertificateFiles.CERTIFICATE} not found in the output"
    assert certificate_value == expected_cert_id, \
        f'Expected: "{CertificateFiles.CERTIFICATE}": "{expected_cert_id} \n " \
            Got: "{CertificateFiles.CERTIFICATE}": "{certificate_value}"'


def verify_show_security_ouput(system, cert_id, should_exist):
    with allure.step(f"Verify {cert_id} exists in show output"):
        show_output = system.security.certificate.show()
        if should_exist:
            assert cert_id in show_output, f"Expected to find {cert_id} in show output. Got: {show_output}"
        else:
            assert cert_id not in show_output, f"Expected not to find {cert_id} in show output. Got: {show_output}"


def verify_imported_certificate(engines, system, cert_id, first_arg, second_arg=""):
    verify_show_security_ouput(system, cert_id, True)

    with allure.step('verify the password is hidden in the logs'):
        with allure.step('Check history command'):
            history_output = engines.dut.run_cmd('history 4')
            str_to_serach = f"{first_arg} *" + (f" {second_arg} *" if second_arg else "")
            assert str_to_serach in history_output, "the password is not hidden in 'history' command"
        with allure.step('Check logs'):
            logs_output = engines.dut.run_cmd(f'tail -4 {SyslogConsts.NVUE_LOG_PATH}')
            logs_output_1 = engines.dut.run_cmd(f'tail -4 {SyslogConsts.NVUE_LOG_PATH}.1')
            assert str_to_serach in logs_output or str_to_serach in logs_output_1, "the password is not hidden in syslog"
