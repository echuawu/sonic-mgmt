
# aaa constants
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


# aaa authentication constants
class AuthConsts:
    ORDER = 'order'
    LOCAL = 'local'
    LDAP = 'ldap'
    RADIUS = 'radius'
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
    SECURITY_VERIFICATION_SHARED_LOCATION = '/auto/sw_system_project/NVOS_INFRA/security/verification/'
    DUMMY_FILE_SHARED_LOCATION = f'{SECURITY_VERIFICATION_SHARED_LOCATION}/scp/scp_test_file.txt'
    SWITCH_NON_PRIVILEGED_PATH = '/tmp'
    SWITCH_PRIVILEGED_PATH = '/var/log'  # todo: check its admin only!
