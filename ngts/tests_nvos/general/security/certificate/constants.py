from ngts.tests_nvos.general.security.certificate.CertInfo import CertInfo

TEST_CERTS_DIR = '/auto/sw_system_project/NVOS_INFRA/security/verification/certs'


class TestCert:
    """ constants describe existing test env certificate """

    gnmi_cert = CertInfo(
        info='gnmi test certificate',
        key=f'{TEST_CERTS_DIR}/gnmi/service.key',
        cert=f'{TEST_CERTS_DIR}/gnmi/service.pem',
        p12_bundle=f'{TEST_CERTS_DIR}/service.p12',
        dn='nvos-dut',
        ip=None,
        cacert=f'{TEST_CERTS_DIR}/gnmi/ca.crt'
    )
