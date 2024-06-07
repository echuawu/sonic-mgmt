import random
import string

import pytest

import ngts.tools.test_utils.allure_utils as allure
from ngts.constants.constants import GnmiConsts
from ngts.nvos_constants.constants_nvos import TestFlowType, ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.conftest import local_adminuser
from ngts.tests_nvos.system.gnmi.constants import CERTIFICATE, DEFAULT_CERTIFICATE, GnmicErr, GNMI_TEST_CERT
from ngts.tests_nvos.system.gnmi.helpers import load_certificate_into_gnmi, verify_gnmi_client


@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('test_flow', TestFlowType.ALL_TYPES)
def test_gnmi_cert(test_flow, engines, local_adminuser, gnmi_cert_hostname, restore_gnmi_cert):
    """
    verify that gnmi works with certificate verification

    1. good-flow: load certificate into gnmi
        bad-flow: don't load certificate into gnmi
    2. run gnmi client without insecure flag
    3. good-flow: expect success
        bad-flow: expect fail
    """
    is_good_flow = test_flow == TestFlowType.GOOD_FLOW
    test_cert = GNMI_TEST_CERT
    if is_good_flow:
        with allure.step('load certificate into gnmi'):
            load_certificate_into_gnmi(engines.dut, test_cert)
    with allure.step(f'run gnmi client with{"" if is_good_flow else "out"} insecure flag - '
                     f'expect {"success" if is_good_flow else "fail"}'):
        verify_gnmi_client(test_flow, test_cert.dn or test_cert.ip, GnmiConsts.GNMI_DEFAULT_PORT,
                           local_adminuser.username,
                           local_adminuser.password, False, GnmicErr.CERT_VERIFY_FAIL)


@pytest.mark.TODO
@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('api', ApiType.ALL_TYPES)
def test_gnmi_cert_cli(api):
    """
    verify gnmi certificate related cli work properly

    1. verify in show that certificate field exists and is set to default
    2. set gnmi certificate
    3. verify in show the new certificate
    4. unset gnmi certificate
    5. verify in show the default certificate value
    6. set gnmi certificate (again)
    7. unset gnmi (entire endpoint)
    8. verify in show the default certificate value
    """
    TestToolkit.tested_api = api
    with allure.step('verify in show that certificate field exists and is set to default'):
        gnmi = System().gnmi_server
        out = OutputParsingTool.parse_json_str_to_dictionary(gnmi.show()).get_returned_value()
        assert CERTIFICATE in out, f'field "{CERTIFICATE}" was not found in show gnmi output\n{out}'
        assert out[CERTIFICATE] == DEFAULT_CERTIFICATE, (f'value of field "{CERTIFICATE}" not as expected (default)\n'
                                                         f'expected (default): {DEFAULT_CERTIFICATE}\n'
                                                         f'actual: {out[CERTIFICATE]}')
    with allure.step('set gnmi certificate'):
        rand_str = ''.join(random.choice(string.ascii_letters) for _ in range(6))
        gnmi.set(CERTIFICATE, rand_str, apply=True).verify_result()
    with allure.step('verify in show the new certificate'):
        out = OutputParsingTool.parse_json_str_to_dictionary(gnmi.show()).get_returned_value()
        assert out[CERTIFICATE] == rand_str, (f'value of field "{CERTIFICATE}" not as expected\n'
                                              f'expected: {rand_str}\n'
                                              f'actual: {out[CERTIFICATE]}')
    with allure.step('unset gnmi certificate'):
        gnmi.unset(CERTIFICATE, apply=True).verify_result()
    with allure.step('verify in show the default certificate value'):
        out = OutputParsingTool.parse_json_str_to_dictionary(gnmi.show()).get_returned_value()
        assert out[CERTIFICATE] == DEFAULT_CERTIFICATE, (f'value of field "{CERTIFICATE}" not as expected (default)\n'
                                                         f'expected (default): {DEFAULT_CERTIFICATE}\n'
                                                         f'actual: {out[CERTIFICATE]}')
    with allure.step('set gnmi certificate'):
        gnmi.set(CERTIFICATE, rand_str, apply=True).verify_result()
    with allure.step('unset gnmi (entire endpoint)'):
        gnmi.unset(apply=True).verify_result()
    with allure.step('verify in show the default certificate value'):
        out = OutputParsingTool.parse_json_str_to_dictionary(gnmi.show()).get_returned_value()
        assert out[CERTIFICATE] == DEFAULT_CERTIFICATE, (f'value of field "{CERTIFICATE}" not as expected (default)\n'
                                                         f'expected (default): {DEFAULT_CERTIFICATE}\n'
                                                         f'actual: {out[CERTIFICATE]}')


@pytest.mark.TODO
@pytest.mark.system
@pytest.mark.gnmi
@pytest.mark.parametrize('test_flow', [TestFlowType.GOOD_FLOW])
def test_gnmi_cert_set_cert(test_flow, local_adminuser, gnmi_cert_hostname, gnmi_cert_id):
    """
    verify that set command loads the certificate into gnmi,
        so clients with the right CA crt can communicate with gnmi with/out skip-verify flag

    1. set gnmi cert
    2. run client without skip-verify flag, using right CA crt - expect success
    3. run client with skip-verify flag - expect success
    """
    with allure.step('set gnmi certificate'):
        System().gnmi_server.set(CERTIFICATE, gnmi_cert_id, apply=True).verify_result()
    with allure.step('run client without skip-verify flag, using right CA crt - expect success'):
        verify_gnmi_client(test_flow, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT, local_adminuser.username,
                           local_adminuser.password, False, GnmicErr.HANDSHAKE_FAIL)
    with allure.step('run client with skip-verify flag - expect success'):
        verify_gnmi_client(test_flow, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT, local_adminuser.username,
                           local_adminuser.password, True, GnmicErr.HANDSHAKE_FAIL)


@pytest.mark.TODO
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_cert_set_non_existing_cert(local_adminuser, gnmi_cert_hostname, gnmi_cert_id):
    """
    verify that when trying to set gnmi certificate with id of non-existing certificate, there is failure

    1. set non existing gnmi cert - expect command fails
    2. run client without skip-verify flag, using right CA crt - expect fail
    """
    with allure.step('set non existing gnmi certificate'):
        bad_cert_id = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        System().gnmi_server.set(CERTIFICATE, bad_cert_id, apply=True).verify_result(False)
    with allure.step('run client without skip-verify flag, using right CA crt - expect fail'):
        verify_gnmi_client(TestFlowType.BAD_FLOW, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT,
                           local_adminuser.username, local_adminuser.password, False, GnmicErr.HANDSHAKE_FAIL)


@pytest.mark.TODO
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_cert_set_cert(local_adminuser, gnmi_cert_hostname, gnmi_cert_id):
    """
    Verify that after unset gnmi certificate, client cannot communicate with gnmi using the CA that supports the cert

    1.	Unset gnmi cert
    2.	Run client with CA cert that supports the cleared cert
    3.	Expect fail
    4.	Set cert again
    5.	Unset entire gnmi
    6.	Run client with CA cert that supports that cert
    7.	Expect fail
    """
    with allure.step('set gnmi certificate'):
        gnmi = System().gnmi_server
        gnmi.set(CERTIFICATE, gnmi_cert_id, apply=True).verify_result()
    with allure.step('unset gnmi certificate'):
        gnmi.unset(CERTIFICATE, apply=True).verify_result()
    with allure.step('run client without skip-verify flag, using right CA crt - expect fail'):
        verify_gnmi_client(TestFlowType.BAD_FLOW, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT,
                           local_adminuser.username, local_adminuser.password, False, GnmicErr.HANDSHAKE_FAIL)
    with allure.step('set gnmi certificate'):
        gnmi.set(CERTIFICATE, gnmi_cert_id, apply=True).verify_result()
    with allure.step('unset all gnmi'):
        gnmi.unset(apply=True).verify_result()
    with allure.step('run client without skip-verify flag, using right CA crt - expect fail'):
        verify_gnmi_client(TestFlowType.BAD_FLOW, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT,
                           local_adminuser.username, local_adminuser.password, False, GnmicErr.HANDSHAKE_FAIL)


@pytest.mark.TODO
@pytest.mark.system
@pytest.mark.gnmi
def test_gnmi_cert_set_cert_after_unset(local_adminuser, gnmi_cert_hostname, gnmi_cert_id):
    """
    Verify that can set certificate after unset, and that it works

    1.	Unset gnmi cert
    2.	Set back gnmi cert
    3.	Run client with CA that supports that cert
    4.	Expect success
    """
    with allure.step('set gnmi certificate after unset'):
        with allure.step('set'):
            gnmi = System().gnmi_server
            gnmi.set(CERTIFICATE, gnmi_cert_id, apply=True).verify_result()
        with allure.step('unset'):
            gnmi.unset(CERTIFICATE, apply=True).verify_result()
        with allure.step('set'):
            gnmi.set(CERTIFICATE, gnmi_cert_id, apply=True).verify_result()
    with allure.step('run client without skip-verify flag, using right CA crt - expect success'):
        verify_gnmi_client(TestFlowType.GOOD_FLOW, gnmi_cert_hostname, GnmiConsts.GNMI_DEFAULT_PORT,
                           local_adminuser.username, local_adminuser.password, False, GnmicErr.HANDSHAKE_FAIL)
