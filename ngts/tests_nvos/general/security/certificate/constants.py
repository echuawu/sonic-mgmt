from typing import List

from ngts.tests_nvos.general.security.certificate.CertInfo import CertInfo

CERT_MGMT_CERTS = '/auto/sw_system_project/NVOS_INFRA/security/verification/cert_mgmt'
GNMI_CERTS = f'/auto/sw_system_project/NVOS_INFRA/security/verification/certs/gnmi'


class TestCert:
    """ constants describe existing test env certificate """
    cert_mgmt_test_cert = CertInfo(
        name='cert-mgmt-valid-cert-1',
        info='valid certificate for certificate mgmt test',
        private=f'{CERT_MGMT_CERTS}/certificate/certificate_private.pem',
        public=f'{CERT_MGMT_CERTS}/certificate/certificate_public.pem',
        p12_bundle=f'{CERT_MGMT_CERTS}/certificate/certificate_bundle.p12',
        p12_password='Test_2108',
        dn='localhost',
        ip='127.0.0.1',
        cacert=f'{CERT_MGMT_CERTS}/ca-certificate/certificate_public.pem'
    )

    cert_mgmt_test_cacert = CertInfo(
        name='cert-mgmt-valid-cacert-1',
        info='valid ca-certificate for certificate mgmt cacert test',
        private=None,
        public=f'{CERT_MGMT_CERTS}/ca-certificate/ca-certificate.crt',
        p12_bundle=None,
        p12_password=None,
        dn=None,
        ip=None,
        cacert=None
    )

    gnmi_cert_valid_1 = CertInfo(
        name='gnmi-valid-cert-1',
        info='valid certificate for gnmi test - from ca1',
        private=f'{GNMI_CERTS}/cert-from-ca1/service.key',
        public=f'{GNMI_CERTS}/cert-from-ca1/service.pem',
        p12_bundle=f'{GNMI_CERTS}/cert-from-ca1/service.p12',
        p12_password='secret',
        dn='nvos-dut',
        ip=None,
        cacert=f'{GNMI_CERTS}/ca1/ca.crt'
    )

    gnmi_cert_valid_2 = CertInfo(
        name='gnmi-valid-cert-2',
        info='valid certificate for gnmi test - from ca2',
        private=f'{GNMI_CERTS}/cert-from-ca2/service.key',
        public=f'{GNMI_CERTS}/cert-from-ca2/service.pem',
        p12_bundle=f'{GNMI_CERTS}/cert-from-ca2/service.p12',
        p12_password='secret',
        dn='nvos-dut',
        ip=None,
        cacert=f'{GNMI_CERTS}/ca2/ca.crt'
    )

    gnmi_cert_private_public_mismatch = CertInfo(
        name='gnmi-cert-private-public-mismatch',
        info="invalid certificate for gnmi test - public and private don't match",
        private=f'{GNMI_CERTS}/cert-from-ca1/service.key',
        public=f'{GNMI_CERTS}/cert-from-ca2/service.pem',
        p12_bundle=None,
        p12_password=None,
        dn='nvos-dut',
        ip=None,
        cacert=f'{GNMI_CERTS}/ca1/ca.crt'
    )

    gnmi_cert_ca_mismatch = CertInfo(
        name='gnmi-cert-ca-mismatch',
        info="certificate for gnmi test - valid certificate but don't match ca",
        private=f'{GNMI_CERTS}/cert-from-ca1/service.key',
        public=f'{GNMI_CERTS}/cert-from-ca1/service.pem',
        p12_bundle=f'{GNMI_CERTS}/cert-from-ca1/service.p12',
        p12_password='secret',
        dn='nvos-dut',
        ip=None,
        cacert=f'{GNMI_CERTS}/ca2/ca.crt'
    )

    gnmi_all_certs: List[CertInfo] = [gnmi_cert_valid_1, gnmi_cert_valid_2, gnmi_cert_private_public_mismatch,
                                      gnmi_cert_ca_mismatch]
