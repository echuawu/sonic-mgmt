from typing import Dict

from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import TacacsServerInfo
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class TacacsConsts:
    TIME_TILL_TACACS_CONF_TAKES_PLACE = 3

    AUTH_TYPES = [AaaConsts.PAP, AaaConsts.CHAP, AaaConsts.LOGIN]  # AaaConsts.MSCHAPV2

    VALID_VALUES = {
        AaaConsts.HOSTNAME: str,
        AaaConsts.TIMEOUT: list(range(1, 61)),
        AaaConsts.AUTH_TYPE: AUTH_TYPES,
        AaaConsts.SECRET: str,
        AaaConsts.PORT: list(range(AaaConsts.MIN_PORT, AaaConsts.MAX_PORT + 1)),
        # AaaConsts.RETRANSMIT: list(range(6)),
        AaaConsts.PRIORITY: list(range(1, 9))
    }

    DEFAULT_TACACS_CONF = {
        AaaConsts.AUTH_TYPE: AaaConsts.PAP,
        AaaConsts.HOSTNAME: {},
        AaaConsts.PORT: 49,
        AaaConsts.SECRET: '*',
        # AaaConsts.RETRANSMIT: 0,
        AaaConsts.TIMEOUT: 5,
    }

    DEFAULTS = {
        AaaConsts.TIMEOUT: 5,
        AaaConsts.AUTH_TYPE: AaaConsts.PAP,
        AaaConsts.PORT: 49,
        # AaaConsts.RETRANSMIT: 0,
        AaaConsts.PRIORITY: 1
    }

    FIELD_IS_NUMERIC = {
        AaaConsts.HOSTNAME: False,
        AaaConsts.TIMEOUT: True,
        AaaConsts.AUTH_TYPE: False,
        AaaConsts.SECRET: False,
        AaaConsts.PORT: True,
        # AaaConsts.RETRANSMIT: True,
        AaaConsts.PRIORITY: True
    }


class TacacsServers:
    PHYSICAL_SERVER = TacacsServerInfo(
        hostname=AaaConsts.PHYSICAL_AAA_SERVER_IPV4_ADDR,
        priority=1,
        secret='testing-tacacs',
        port=49,
        timeout=1,
        # retransmit=0,
        auth_type=AaaConsts.PAP,
        users=[  # todo: verify users on this server
            UserInfo(
                username='adminuser',
                password='adminadmin',
                role=AaaConsts.ADMIN
            ),
            UserInfo(
                username='monitoruser',
                password='testing',
                role=AaaConsts.MONITOR
            )
        ]
    )

    VM_SERVER_USERS = [
        UserInfo(
            username='adminuser',
            password='adminuser',
            role=AaaConsts.ADMIN
        ),
        UserInfo(
            username='monitoruser',
            password='monitoruser',
            role=AaaConsts.MONITOR
        )
    ]
    VM_SERVER_USERS_PAP = [UserInfo(user.username, user.password + '_pap', user.role) for user in VM_SERVER_USERS]
    VM_SERVER_USERS_CHAP = [UserInfo(user.username, user.password + '_chap', user.role) for user in VM_SERVER_USERS]
    VM_SERVER_USERS_LOGIN = [UserInfo(user.username, user.password + '_login', user.role) for user in VM_SERVER_USERS]
    VM_SERVER_USERS_BY_AUTH_TYPE = {
        AaaConsts.PAP: VM_SERVER_USERS_PAP,
        AaaConsts.CHAP: VM_SERVER_USERS_CHAP,
        AaaConsts.LOGIN: VM_SERVER_USERS_LOGIN
    }

    VM_SERVER_IPV4 = TacacsServerInfo(
        hostname=AaaConsts.VM_AAA_SERVER_IPV4_ADDR,
        priority=1,
        secret='secret',
        port=49,
        timeout=1,
        # retransmit=0,
        auth_type=AaaConsts.PAP,
        users=VM_SERVER_USERS_PAP
    )

    VM_SERVER_DN = VM_SERVER_IPV4.copy()
    VM_SERVER_DN.hostname = AaaConsts.VM_AAA_SERVER_DN

    VM_SERVERS: Dict[str, TacacsServerInfo] = {
        AaaConsts.IPV4: VM_SERVER_IPV4,
        AaaConsts.DN: VM_SERVER_DN
    }

    DOCKER_SERVER_IPV4 = VM_SERVER_IPV4.copy()
    DOCKER_SERVER_IPV4.port = 50
    DOCKER_SERVER_IPV6 = DOCKER_SERVER_IPV4.copy()
    DOCKER_SERVER_IPV6.hostname = AaaConsts.VM_AAA_SERVER_IPV6_ADDR
    DOCKER_SERVER_DN = VM_SERVER_DN.copy()
    DOCKER_SERVER_DN.port = 50

    DOCKER_SERVERS: Dict[str, TacacsServerInfo] = {
        AaaConsts.IPV4: DOCKER_SERVER_IPV4,
        AaaConsts.IPV6: DOCKER_SERVER_IPV6,
        AaaConsts.DN: DOCKER_SERVER_DN
    }
