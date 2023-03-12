

class LDAPConsts:
    HOSTNAME = 'hostname'
    PRIORITY = 'priority'
    SCOPE = 'scope'
    BASE_DN = 'base-dn'
    BIND_DN = 'bind-dn'
    BIND_PASSWORD = 'bind-password'
    TIMEOUT_BIND = 'timeout-bind'
    TIMEOUT = 'timeout'
    PORT = 'port'
    VERSION = 'version'
    LOGIN_ATTR = 'login-attribute'
    GROUP_ATTR = 'group-attribute'
    LDAP_STATE_ENABLED = 'enabled'
    LDAP_STATE_DISABLED = 'disabled'
    USERS = 'users'

    PHYSICAL_LDAP_SERVER = {
        "hostname": "10.7.34.20",
        "base-dn": "dc=domain,dc=local",
        "bind-dn": "cn=ldap_admin,dc=domain,dc=local",
        "bind-password": "",
        "login-attribute": "cn",
        "group-attribute": "member",
        "scope": "subtree",
        "port": "389",
        "timeout-bind": "5",
        "timeout": "5",
        "version": 3,
        "priority": 1,
        "users": [
            {
                'username': 'azmy',  # TODO: change to volt once it is in
                'password': 'azmy',  # TODO: change to volt once it is in
                'role': 'admin'
            }
        ]
    }
