

class LDAPConsts:
    HOSTNAME = 'hostname'
    PRIORITY = 'priority'
    SCOPE = 'scope'
    BASE_DN = 'base-dn'
    BIND_DN = 'bind-dn'
    BIND_PASSWORD = 'password'
    TIMEOUT_BIND = 'timeout-bind'
    TIMEOUT = 'timeout-search'
    PORT = 'auth-port'
    VERSION = 'version'
    LOGIN_ATTR = 'login-attribute'
    GROUP_ATTR = 'group-attribute'
    LDAP_STATE_ENABLED = 'enabled'
    LDAP_STATE_DISABLED = 'disabled'
    USERS = 'users'
    NESTED_USERS = "nested-users"
    USERNAME = 'username'
    PASSWORD = 'password'

    PHYSICAL_LDAP_SERVER = {
        "hostname": "10.7.34.20",
        "base-dn": "dc=itzgeek,dc=local",
        "bind-dn": "cn=ldapadm,dc=itzgeek,dc=local",
        "password": "secret",
        "login-attribute": "cn",
        "group-attribute": "member",
        # "scope": "subtree", not supported now
        "auth-port": "389",
        "timeout-bind": "5",
        "timeout-search": "5",
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
        "timeout-bind": "4",
        "timeout-search": "4",
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
        "timeout-bind": "6",
        "timeout-search": "6",
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

    LDAP_SERVERS_LIST = [
        PHYSICAL_LDAP_SERVER,
        DOCKER_LDAP_SERVER
    ]

    LDAP_LOW_TIMOEUT = '1'
    LDAP_HIGH_TIMEOUT = '60'
    MAX_PRIORITY = '8'
    LDAP_SLEEP_TO_APPLY_CONFIGURATIONS = 5
