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

ETC_HOSTS = '/etc/hosts'

SERVICE_KEY = 'service.key'
SERVICE_PEM = 'service.pem'

ERR_GNMIC_NOT_INSTALLED = 'gnmic: command not found'
ERR_GNMIC_AUTH_FAIL = 'Authentication failed'
ERR_GNMIC_CERT = 'authentication handshake failed'
