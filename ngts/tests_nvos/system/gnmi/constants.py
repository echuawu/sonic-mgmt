from ngts.tests_nvos.general.security.certificate.CertInfo import CertInfo
from ngts.tests_nvos.general.security.certificate.constants import TestCert


class GnmiMode:
    ONCE = 'once'
    POLL = 'poll'
    STREAM = ''
    ALL_MODES = [ONCE, POLL, STREAM]


DUT_HOSTNAME_FOR_CERT = 'nvos-dut'
NFS_GNMI_CERTS_DIR = '/auto/sw_system_project/NVOS_INFRA/security/verification/certs/gnmi'
NFS_GNMI_CACERT_FILE = f"{NFS_GNMI_CERTS_DIR}/ca.crt"
DUT_GNMI_CERTS_DIR = '/tmp/gnmi-certs'
DOCKER_CERTS_DIR = '/etc/netq/cert'

DUT_MOUNT_GNMI_CERT_DIR = '/etc/gnmi/cert'

ETC_HOSTS = '/etc/hosts'

SERVICE_KEY = 'service.key'
SERVICE_PEM = 'service.pem'

MAX_GNMI_SUBSCRIBERS = 10

CERTIFICATE = 'certificate'
DEFAULT_CERTIFICATE = 'self-signed'

GNMI_TEST_CERT: CertInfo = TestCert.gnmi_cert


class GnmicErr:
    GNMIC_NOT_INSTALLED = 'gnmic: command not found'
    AUTH_FAIL = 'Authentication failed'
    CERT_VERIFY_FAIL = 'failed to verify certificate'
    HANDSHAKE_FAIL = 'authentication handshake failed'
    AUTH_SERVICE_UNAVAILABLE = 'authentication service is unavailable'
    REQUEST_FAILED = 'request failed'
    NO_SUBSCRIBER_SLOT_AVAILABLE = 'no subscriber slot available'
    RCV_ERROR = 'rcv error'
    RPC_ERROR = 'rpc error'
    ALL_ERRS = [GNMIC_NOT_INSTALLED, AUTH_FAIL, HANDSHAKE_FAIL, AUTH_SERVICE_UNAVAILABLE,
                REQUEST_FAILED, NO_SUBSCRIBER_SLOT_AVAILABLE, RCV_ERROR, RPC_ERROR]
