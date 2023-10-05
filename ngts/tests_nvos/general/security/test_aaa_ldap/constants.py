
class LdapConsts:
    # keys
    HOSTNAME = 'hostname'
    PRIORITY = 'priority'
    SCOPE = 'scope'
    USERS = 'users'
    NESTED_USERS = "nested-users"
    USERNAME = 'username'
    PASSWORD = 'password'
    # show cmd fields
    PORT = 'auth-port'
    BASE_DN = 'base-dn'
    BIND_DN = 'bind-dn'
    GROUP_ATTR = 'group-attribute'
    # LOGIN_ATTR = 'login-attribute'  not supported now
    BIND_PASSWORD = 'password'
    TIMEOUT_BIND = 'timeout-bind'
    TIMEOUT = 'timeout-search'
    VERSION = 'version'
    # phase 2 show cmd fields
    SSL = 'ssl'
    SSL_CA_LIST = 'ca-list'
    SSL_CERT_VERIFY = 'cert-verify'
    SSL_MODE = 'mode'
    SSL_PORT = 'port'
    SSL_TLS_CIPHERS = 'tls-ciphers'
    SSL_CRL_LIST = 'crl-list'  # decided out of feature
    TLS_CRL_CHECK_FILE = 'tls-crl-check-file'  # decided out of feature
    TLS_CRL_CHECK_STATE = 'tls-crl-check-state'  # decided out of feature

    LDAP_FIELDS = [PORT, BASE_DN, BIND_DN, GROUP_ATTR, BIND_PASSWORD, TIMEOUT_BIND, TIMEOUT, VERSION]
    SSL_FIELDS = [SSL_CA_LIST, SSL_CERT_VERIFY, SSL_MODE, SSL_PORT, SSL_TLS_CIPHERS]

    # possible values
    NONE = 'none'
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    DEFAULT = 'default'
    START_TLS = 'start-tls'
    DEFAULT_CA_LIST = 'default-ca-list'
    TLS_1_2 = 'TLS1.2'
    TLS_1_3 = 'TLS1.3'
    ALL = 'all'
    DEFAULT_CRL = 'default-crl'
    PORT_389 = '389'
    PORT_636 = '636'
    PORT_TLS = PORT_389
    PORTS_SSL = [PORT_389, PORT_636]

    POSSIBLE_PORTS = list(range(1, 65535 + 1))
    TEST_PORTS = list(range(1001, 65535 + 1))  # don't use system ports so the test won't be blocked

    VALID_VALUES = {
        PORT: TEST_PORTS,
        BASE_DN: str,
        BIND_DN: str,
        GROUP_ATTR: str,
        # LOGIN_ATTR: str,  not supported now
        BIND_PASSWORD: str,
        TIMEOUT_BIND: list(range(1, 60 + 1)),
        TIMEOUT: list(range(1, 60 + 1)),
        VERSION: [2, 3]
    }

    VALID_VALUES_SSL = {
        SSL_CA_LIST: [DEFAULT, NONE],
        SSL_CERT_VERIFY: [ENABLED, DISABLED],
        SSL_CRL_LIST: [DEFAULT, NONE],
        SSL_MODE: [NONE, START_TLS, SSL],
        SSL_PORT: TEST_PORTS,
        SSL_TLS_CIPHERS: [ALL, TLS_1_2, TLS_1_3]
    }

    ALL_VALID_VALUES = VALID_VALUES.copy()
    ALL_VALID_VALUES.update(VALID_VALUES_SSL)
    ALL_VALID_VALUES[PORT] = POSSIBLE_PORTS
    ALL_VALID_VALUES[SSL_PORT] = POSSIBLE_PORTS
    ALL_VALID_VALUES[PRIORITY] = [1, 2, 3, 4, 5, 6, 7, 8]

    # default values
    DEFAULTS = {
        PORT: 389,
        BASE_DN: 'ou=users,dc=example,dc=com',
        BIND_DN: '',
        GROUP_ATTR: 'member',
        # LOGIN_ATTR: 'cn',  not supported now
        BIND_PASSWORD: '*',
        TIMEOUT_BIND: 5,
        TIMEOUT: 5,
        VERSION: 3,
        # ssl defaults
        SSL_CA_LIST: DEFAULT,
        SSL_CERT_VERIFY: ENABLED,
        SSL_MODE: NONE,
        SSL_PORT: 636,
        SSL_TLS_CIPHERS: ALL
    }

    DEFAULT_CONF = {
        PORT: 389,
        BASE_DN: 'ou=users,dc=example,dc=com',
        BIND_DN: '',
        GROUP_ATTR: 'member',
        # LOGIN_ATTR: 'cn',  not supported now
        BIND_PASSWORD: '*',
        TIMEOUT_BIND: 5,
        TIMEOUT: 5,
        VERSION: 3,
        HOSTNAME: {}
    }
    # ssl defaults
    SSL_DEFAULTS = {
        SSL_CA_LIST: DEFAULT,
        SSL_CERT_VERIFY: ENABLED,
        SSL_MODE: NONE,
        SSL_PORT: 636,
        SSL_TLS_CIPHERS: ALL
    }

    FIELD_IS_NUMERIC = {
        PORT: True,
        BASE_DN: False,
        BIND_DN: False,
        GROUP_ATTR: False,
        # LOGIN_ATTR: 'cn',  not supported now
        BIND_PASSWORD: False,
        TIMEOUT_BIND: True,
        TIMEOUT: True,
        VERSION: True,
        PRIORITY: True,
        # ssl defaults
        SSL_CA_LIST: False,
        SSL_CERT_VERIFY: False,
        SSL_CRL_LIST: False,
        SSL_MODE: False,
        SSL_PORT: True,
        SSL_TLS_CIPHERS: False
    }

    PHYSICAL_LDAP_SERVER = {
        "hostname": "10.7.34.20",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        # "login-attribute": "cn",  not supported now
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '1',
        "users": [
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'adminuser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'admin'
            }
        ],
        "nested-users": [
            {
                'username': 'nestedMonitorUser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'nestedAdminUser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            }
        ]
    }

    DOCKER_LDAP_SERVER = {
        "hostname": "fdfd:fdfd:10:237:250:56ff:fe1b:56",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        # "login-attribute": "cn",  not supported now
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '2',
        "users": [
            {
                'username': 'adminuser',  # TODO: change to volt once it is in
                'password': 'asdasd',  # TODO: change to volt once it is in
                'role': 'monitor'  # NOTE that adminuser in this server is with monitor permissions!
            },
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            },
            {
                'username': 'alon',  # TODO: change to volt once it is in
                'password': 'alon',  # TODO: change to volt once it is in
                'role': 'monitor'
            }
        ]
    }

    DOCKER_LDAP_SERVER_IPV4 = {
        "hostname": "10.237.0.86",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        # "login-attribute": "cn",  not supported now
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '2',
        "users": [
            {
                'username': 'adminuser',  # TODO: change to volt once it is in
                'password': 'asdasd',  # TODO: change to volt once it is in
                'role': 'monitor'  # NOTE that adminuser in this server is with monitor permissions!
            },
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            },
            {
                'username': 'alon',  # TODO: change to volt once it is in
                'password': 'alon',  # TODO: change to volt once it is in
                'role': 'monitor'
            }
        ]
    }

    DOCKER_LDAP_SERVER_DNS = {
        "hostname": "fit-l-vrt-60-086",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        # "login-attribute": "cn",  not supported now
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '3',
        "users": [
            {
                'username': 'adminuser',  # TODO: change to volt once it is in
                'password': 'asdasd',  # TODO: change to volt once it is in
                'role': 'monitor'  # NOTE that adminuser in this server is with monitor permissions!
            },
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            },
            {
                'username': 'alon',  # TODO: change to volt once it is in
                'password': 'alon',  # TODO: change to volt once it is in
                'role': 'monitor'
            }
        ]
    }

    DOCKER_LDAP_SERVER_DNS_WITH_CERT = {
        "hostname": "ldap.itzgeek.local",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        # "login-attribute": "cn", not supported now
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '3',
        "users": [
            {
                'username': 'adminuser',  # TODO: change to volt once it is in
                'password': 'asdasd',  # TODO: change to volt once it is in
                'role': 'monitor'  # NOTE that adminuser in this server is with monitor permissions!
            },
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            },
            {
                'username': 'alon',  # TODO: change to volt once it is in
                'password': 'alon',  # TODO: change to volt once it is in
                'role': 'monitor'
            }
        ]
    }

    DOCKER_LDAP_SERVER_HOST_ALIAS_IPV4 = '10.237.0.86 ldap.itzgeek.local'
    DOCKER_LDAP_SERVER_HOST_ALIAS_IPV6 = 'fdfd:fdfd:10:237:250:56ff:fe1b:56 ldap.itzgeek.local'

    LDAP_SERVERS_LIST = [
        PHYSICAL_LDAP_SERVER,
        DOCKER_LDAP_SERVER
    ]

    DEFAULT_PRIORTIY = 1
    LDAP_LOW_TIMOEUT = '1'
    LDAP_HIGH_TIMEOUT = '60'
    MAX_PRIORITY = '8'
    LDAP_SLEEP_TO_APPLY_CONFIGURATIONS = 10

    # connection modes
    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    DNS = 'dns'

    SERVER_INFO = {
        IPV4: DOCKER_LDAP_SERVER_IPV4,
        IPV6: DOCKER_LDAP_SERVER,
        DNS: DOCKER_LDAP_SERVER_DNS
    }

    TLS = 'tls'
    CONNECTION_METHODS = [IPV4, IPV6, DNS]
    ENCRYPTION_MODES = [NONE, TLS, SSL]

    DOCKER_LDAP_SERVER_CERT_PATH = \
        '/auto/sw_system_project/NVOS_INFRA/security/verification/ldap/custom_ldap_server_cert.pem'
    SWITCH_TMP_PATH = '/tmp'
    SERVER_CERT_FILE_IN_SWITCH = '/tmp/custom_ldap_server_cert.pem'
    SWITCH_CA_FILE = '/etc/ssl/certs/ca-certificates.crt'
    SWITCH_CA_BACKUP_FILE = '/tmp/backup_ca-certificates.crt'

    PERMISSION_DENIED = 'Permission denied'
