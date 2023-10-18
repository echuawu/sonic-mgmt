from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import LdapServerInfo
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class LdapServers:
    GLOBAL_BASE_DN = 'dc=itzgeek,dc=local'
    GLOBAL_BIND_DN = 'cn=ldapadm,dc=itzgeek,dc=local'
    GLOBAL_GROUP_ATTR = 'member'
    GLOBAL_VERSION = 3

    PHYSICAL_SERVER = LdapServerInfo(
        hostname=AaaConsts.PHYSICAL_AAA_SERVER_IPV4_ADDR,
        priority=1,
        secret='secret',
        port=389,
        base_dn=GLOBAL_BASE_DN,
        bind_dn=GLOBAL_BIND_DN,
        group_attr=GLOBAL_GROUP_ATTR,
        timeout_bind=1,
        timeout_search=1,
        version=GLOBAL_VERSION,
        users=[
            UserInfo(
                username='adminuser',
                password='asd',
                role=AaaConsts.ADMIN
            ),
            UserInfo(
                username='monitoruser',
                password='asd',
                role=AaaConsts.MONITOR
            )
        ]
    )

    DOCKER_SERVER_IPV4 = LdapServerInfo(
        hostname=AaaConsts.VM_AAA_SERVER_IPV4_ADDR,
        priority=1,
        secret='secret',
        port=389,
        base_dn=GLOBAL_BASE_DN,
        bind_dn=GLOBAL_BIND_DN,
        group_attr=GLOBAL_GROUP_ATTR,
        timeout_bind=1,
        timeout_search=1,
        version=GLOBAL_VERSION,
        ssl_port=636,
        users=[
            # UserInfo(
            #     username='adminuser',
            #     password='asdasd',
            #     role=AaaConsts.ADMIN
            # ),
            # UserInfo(
            #     username='monitoruser',
            #     password='asd',
            #     role=AaaConsts.MONITOR
            # ),
            UserInfo(
                username='azmy',
                password='azmy',
                role=AaaConsts.ADMIN
            ),
            UserInfo(
                username='alon',
                password='alon',
                role=AaaConsts.MONITOR
            )
        ]
    )
    DOCKER_SERVER_IPV6 = DOCKER_SERVER_IPV4.copy()
    DOCKER_SERVER_IPV6.hostname = AaaConsts.VM_AAA_SERVER_IPV6_ADDR
    DOCKER_SERVER_DN = DOCKER_SERVER_IPV4.copy()
    DOCKER_SERVER_DN.hostname = AaaConsts.VM_AAA_SERVER_DN

    DOCKER_SERVERS = {
        AaaConsts.IPV4: DOCKER_SERVER_IPV4,
        AaaConsts.IPV6: DOCKER_SERVER_IPV6,
        AaaConsts.DN: DOCKER_SERVER_DN
    }

    DOCKER_SERVER_DN_WITH_CERT = DOCKER_SERVER_IPV4.copy()
    DOCKER_SERVER_DN_WITH_CERT.hostname = 'ldap.itzgeek.local'
