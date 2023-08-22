
# aaa constants
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class AaaConsts:
    USER = 'user'
    PASSWORD = 'password'
    ROLE = 'role'
    ADMIN = 'admin'
    MONITOR = 'monitor'
    USERNAME = 'username'

    LOCALADMIN = 'localadmin'
    LOCALMONITOR = 'localmonitor'
    STRONG_PASSWORD = 'Your_password1'

    LOCAL_TEST_ADMIN = UserInfo(LOCALADMIN, STRONG_PASSWORD, ADMIN)
    LOCAL_TEST_MONITOR = UserInfo(LOCALMONITOR, STRONG_PASSWORD, MONITOR)

    LOCAL_ONLY_TEST_USERS = [
        {
            USERNAME: LOCALADMIN,
            PASSWORD: STRONG_PASSWORD,
            ROLE: ADMIN
        },
        {
            USERNAME: LOCALMONITOR,
            PASSWORD: STRONG_PASSWORD,
            ROLE: MONITOR
        }
    ]

    HOSTNAME = 'hostname'
    TIMEOUT = 'timeout'
    AUTH_TYPE = 'auth-type'
    SECRET = 'secret'
    PORT = 'port'
    RETRANSMIT = 'retransmit'
    PRIORITY = 'priority'

    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    DN = 'dn'

    MIN_PORT = 1
    MAX_PORT = 65535

    PAP = 'pap'
    CHAP = 'chap'
    MSCHAPV2 = 'mschapv2'
    LOGIN = 'login'

    PHYSICAL_AAA_SERVER_IPV4_ADDR = '10.7.34.20'
    VM_AAA_SERVER_IPV4_ADDR = '10.237.0.86'
    VM_AAA_SERVER_IPV6_ADDR = 'fdfd:fdfd:10:237:250:56ff:fe1b:56'
    VM_AAA_SERVER_DN = 'fit-l-vrt-60-086'

    ENABLED = 'enabled'
    DISABLED = 'disabled'


# aaa authentication constants
class AuthConsts:
    ORDER = 'order'
    LOCAL = 'local'
    LDAP = 'ldap'
    RADIUS = 'radius'
    TACACS = 'tacacs'
    FALLBACK = 'fallback'
    FAILTHROUGH = 'failthrough'

    SHOW_COMMAND = 'nv show system'
    SET_COMMAND = 'nv set system security password-hardening len-min 6'
    SWITCH_PROMPT_PATTERN = '.+@.+:.+\\$'
    PERMISSION_ERROR = 'Error: You do not have permission to execute that command.'

    LOGIN_FAIL_ERR = 'login fail'
    SHOW_FAIL_ERR = 'show fail'
    SET_FAIL_ERR = 'set fail'
    UNSET_FAIL_ERR = 'unset fail'

    USERS = 'users'

    # possible authentication mediums
    SSH = 'SSH'
    OPENAPI = 'OpenApi'
    RCON = 'RCON'
    SCP = 'SCP'
    AUTH_MEDIUMS = [SSH, OPENAPI, RCON, SCP]

    # path consts
    SECURITY_VERIFICATION_SHARED_LOCATION = '/auto/sw_system_project/NVOS_INFRA/security/verification'
    DUMMY_FILE_NAME = 'scp_test_file.txt'
    DUMMY_FILE_SHARED_LOCATION = f'{SECURITY_VERIFICATION_SHARED_LOCATION}/scp/{DUMMY_FILE_NAME}'
    DOWNLOADED_FILES_SHARED_LOCATION = f'{SECURITY_VERIFICATION_SHARED_LOCATION}/scp/downloaded'
    SWITCH_NON_PRIVILEGED_PATH = '/tmp'
    SWITCH_PRIVILEGED_PATH = '/var/log'  # todo: check its admin only!

    LOGIN_FAIL_ERR = 'login fail'
    SHOW_FAIL_ERR = 'show fail'
    SET_FAIL_ERR = 'set fail'
    UNSET_FAIL_ERR = 'unset fail'

    USERS = 'users'

    # possible authentication mediums
    SSH = 'SSH'
    OPENAPI = 'OpenApi'
    RCON = 'RCON'
    SCP = 'SCP'
    AUTH_MEDIUMS = [SSH, OPENAPI, RCON, SCP]
