
# aaa constants
class AaaConsts:
    USER = 'user'
    PASSWORD = 'password'
    ROLE = 'role'
    ADMIN = 'admin'
    MONITOR = 'monitor'
    USERNAME = 'username'

    STRONG_PASSWORD = 'x%]AZf[K_Ualon6'

    LOCAL_ONLY_TEST_USERS = [
        {
            USERNAME: 'localadmin',
            PASSWORD: STRONG_PASSWORD,
            ROLE: ADMIN
        },
        {
            USERNAME: 'localmonitor',
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
