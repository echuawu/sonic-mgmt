
SONIC_MARS_BASE_PATH = "/.autodirect/sw_regression/system/SONIC/MARS"

SONIC_MGMT_DEVICE_ID = "SONIC_MGMT"
NGTS_PATH_PYTEST = "/ngts_venv/bin/pytest"
NGTS_PATH_PYTHON = "/ngts_venv/bin/python"
TEST_SERVER_DEVICE_ID = "TEST_SERVER"
NGTS_DEVICE_ID = "NGTS"
DUT_DEVICE_ID = "DUT"
FANOUT_DEVICE_ID = "FANOUT"
SONIC_MGMT_DIR = '/root/mars/workspace/sonic-mgmt/'
UPDATED_FW_TAR_PATH = 'tests/platform_tests/fwutil/updated-fw.tar.gz'
HTTP_SERVER_NBU_NFS = 'http://nbu-nfs.mellanox.com'

DOCKER_SONIC_MGMT_IMAGE_NAME = "docker-sonic-mgmt"
DOCKER_NGTS_IMAGE_NAME = "docker-ngts"

SONIC_MGMT_REPO_URL = "http://10.7.77.140:8080/switchx/sonic/sonic-mgmt"
SONIC_MGMT_MOUNTPOINTS = {
    '/.autodirect/mswg/projects': '/.autodirect/mswg/projects',
    '/auto/sw_system_project': '/auto/sw_system_project',
    '/auto/sw_system_release': '/auto/sw_system_release',
    '/.autodirect/sw_system_release/': '/.autodirect/sw_system_release/',
    '/auto/sw_regression/system/SONIC/MARS': '/auto/sw_regression/system/SONIC/MARS',
    '/.autodirect/sw_regression/system/SONIC/MARS': '/.autodirect/sw_regression/system/SONIC/MARS',
    '/workspace': '/workspace',
    '/.autodirect/LIT/SCRIPTS': '/.autodirect/LIT/SCRIPTS',
    '/auto/sw_regression/system/NVOS/MARS': '/auto/sw_regression/system/NVOS/MARS',
    '/.autodirect/sw_regression/system/NVOS/MARS': '/.autodirect/sw_regression/system/NVOS/MARS',
    '/etc/localtime': '/etc/localtime'
}

SONIC_MGMT_MOUNTPOINTS_MTBC = {
    '/auto/sw_regression/mtbcsw/system/SONIC/MARS': '/auto/sw_regression/mtbcsw/system/SONIC/MARS',
    '/.autodirect/sw_regression/mtbcsw/system/SONIC/MARS': '/.autodirect/sw_regression/mtbcsw/system/SONIC/MARS'
}
MTBC_SERVER_LIST = ['dev-r730-01', '10.75.206.120', 'dev-r730-02', '10.75.207.40', 'dev-r730-03', '10.75.207.5']
VER_SDK_PATH = "/opt/ver_sdk"
EXTRA_PACKAGE_PATH_LIST = ["/usr/lib64/python2.7/site-packages"]

TOPO_ARRAY = ("t0", "t1-lag", "ptf32", "t0-64", "t1-64-lag", "t0-56", "t0-56-po2vlan")
REBOOT_TYPES = {
    "reboot": "reboot",
    "fast-reboot": "fast-reboot",
    "warm-reboot": "warm-reboot"
}

DOCKER_REGISTRY = "harbor.mellanox.com/sonic"

DUT_LOG_BACKUP_PATH = "/.autodirect/sw_system_project/sonic/dut_logs"

BRANCH_PTF_MAPPING = {'master': 'latest',
                      '202012': '42007',
                      '202106': '42007'
                      }
