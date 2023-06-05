

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
    LOGIN_ATTR = 'login-attribute'
    BIND_PASSWORD = 'password'
    TIMEOUT_BIND = 'timeout-bind'
    TIMEOUT = 'timeout-search'
    VERSION = 'version'
    # phase 2 show cmd fields
    SSL_MODE = 'mode'
    SSL_CERT_VERIFY = 'ssl-cert-verify'
    SSL_CA_LIST = 'ssl-ca-list'
    SSL_CIPHERS = 'ssl-ciphers'
    TLS_CRL_CHECK_FILE = 'tls-crl-check-file'
    TLS_CRL_CHECK_STATE = 'tls-crl-check-state'
    SSL_PORT = 'ssl-port'  # under open question

    LDAP_FIELDS = [PORT, BASE_DN, BIND_DN, GROUP_ATTR, LOGIN_ATTR, BIND_PASSWORD, TIMEOUT_BIND, TIMEOUT, VERSION,
                   SSL_MODE, SSL_CERT_VERIFY, SSL_CA_LIST, SSL_CIPHERS, TLS_CRL_CHECK_FILE, TLS_CRL_CHECK_STATE,
                   SSL_PORT]

    # possible values
    NONE = 'none'
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    START_TLS = 'start-tls'
    SSL = 'ssl'
    DEFAULT_CA_LIST = 'default-ca-list'
    TLS_1_2 = 'TLS1.2'
    TLS_1_3 = 'TLS1.3'
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
        LOGIN_ATTR: str,
        BIND_PASSWORD: str,
        TIMEOUT_BIND: list(range(1, 60 + 1)),
        TIMEOUT: list(range(1, 60 + 1)),
        VERSION: [2, 3],
        SSL_MODE: [NONE, START_TLS, SSL],
        SSL_CERT_VERIFY: [ENABLED, DISABLED],
        SSL_CA_LIST: [NONE, DEFAULT_CA_LIST],
        SSL_CIPHERS: [TLS_1_2, TLS_1_3],
        TLS_CRL_CHECK_FILE: [NONE, DEFAULT_CRL],
        TLS_CRL_CHECK_STATE: [ENABLED, DISABLED],
        SSL_PORT: TEST_PORTS
    }

    # default values
    DEFAULTS = {
        PORT: 389,
        BASE_DN: 'ou=users,dc=example,dc=com',
        BIND_DN: '',
        GROUP_ATTR: 'member',
        LOGIN_ATTR: 'cn',
        BIND_PASSWORD: '*',
        TIMEOUT_BIND: 5,
        TIMEOUT: 5,
        VERSION: 3,
        SSL_MODE: NONE,  # todo: verify phase 2 defaults
        SSL_CERT_VERIFY: DISABLED,
        SSL_CA_LIST: NONE,
        SSL_CIPHERS: TLS_1_2,
        TLS_CRL_CHECK_FILE: NONE,
        TLS_CRL_CHECK_STATE: DISABLED,
        SSL_PORT: PORT_389
    }

    PHYSICAL_LDAP_SERVER = {
        "hostname": "10.7.34.20",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        "login-attribute": "cn",
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
        "login-attribute": "cn",
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '2',
        "users": [
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            }
        ]
    }

    DOCKER_LDAP_SERVER_DNS = {
        "hostname": "fit-l-vrt-60-086",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        "login-attribute": "cn",
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "1",
        "timeout-search": "1",
        "version": '3',
        "priority": '3',
        "users": [
            {
                'username': 'monitoruser',  # TODO: change to volt once it is in
                'password': 'asd',  # TODO: change to volt once it is in
                'role': 'monitor'
            },
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            }
        ]
    }

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
        IPV4: PHYSICAL_LDAP_SERVER,
        IPV6: DOCKER_LDAP_SERVER,
        DNS: DOCKER_LDAP_SERVER_DNS
    }

    TLS = 'tls'
    CONNECTION_METHODS = [IPV4, IPV6, DNS]
    ENCRYPTION_MODES = [NONE, TLS, SSL]
