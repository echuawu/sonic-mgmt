class RemoteAaaType:
    LDAP = 'ldap'
    RADIUS = 'radius'
    TACACS = 'tacacs'
    ALL_TYPES = [LDAP, RADIUS, TACACS]


class RemoteAaaConsts:
    WAIT_TIME_BEFORE_AUTH = 3


class ValidValues:
    PRIORITY = [1, 2, 3, 4, 5, 6, 7, 8]
