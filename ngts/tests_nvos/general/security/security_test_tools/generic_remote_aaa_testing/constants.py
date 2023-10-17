from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusConstants


class RemoteAaaType:
    LDAP = 'ldap'
    RADIUS = 'radius'
    TACACS = 'tacacs'
    ALL_TYPES = [LDAP, RADIUS, TACACS]


class RemoteAaaConsts:
    WAIT_TIME_BEFORE_AUTH = 3
