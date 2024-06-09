from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts, AddressingType
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RadiusServerInfo
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class RadiusConstants:
    '''
    constants for Radius suit case
    '''
    # keys
    RADIUS_HOSTNAME = 'hostname'
    RADIUS_PASSWORD = 'secret'
    RADIUS_TIMEOUT = 'timeout'
    RADIUS_AUTH_PORT = 'port'
    RADIUS_AUTH_TYPE = 'auth-type'
    RADIUS_PRIORITY = 'priority'
    RADIUS_STATISTICS = 'statistics'
    RADIUS_DEFAULT_PRIORITY = 1
    RADIUS_DEFAULT_TIMEOUT = 3
    RADIUS_MAX_PRIORITY = 8
    RADIUS_MID_PRIORITY = 4
    RADIUS_MIN_PRIORITY = 1
    RADIUS_SERVER_USERS = 'users'
    RADIUS_SERVER_USERNAME = 'username'
    RADIUS_SERVER_USER_PASSWORD = 'password'
    AUTHENTICATION_FAILURE_MESSAGE = 'Authentication failure: unable to connect linux'
    AUTH_TYPES = ['chap', 'pap', 'mschapv2']

    VALID_VALUES = {
        AaaConsts.HOSTNAME: str,
        AaaConsts.TIMEOUT: list(range(1, 61)),
        AaaConsts.AUTH_TYPE: AUTH_TYPES,
        AaaConsts.SECRET: str,
        AaaConsts.PORT: list(range(AaaConsts.MIN_PORT, AaaConsts.MAX_PORT + 1)),
        AaaConsts.RETRANSMIT: list(range(11)),
        AaaConsts.PRIORITY: list(range(1, 9)),
        RADIUS_STATISTICS: [AaaConsts.DISABLED, AaaConsts.ENABLED]
    }

    DEFAULT_RADIUS_CONF = {
        AaaConsts.AUTH_TYPE: AaaConsts.MSCHAPV2,
        AaaConsts.HOSTNAME: {},
        AaaConsts.PORT: 1812,
        AaaConsts.SECRET: '*',
        AaaConsts.RETRANSMIT: 0,
        AaaConsts.TIMEOUT: 3,
        RADIUS_STATISTICS: AaaConsts.DISABLED
    }

    RADIUS_SERVERS_DICTIONARY = {
        'physical_radius_server': {
            'hostname': '10.7.34.20',
            'secret': 'testing-radius',  # TODO: change to volt once it is in
            'port': '1812',
            'auth-type': 'pap',
            'timeout': '5',
            'priority': 2,
            'users': [
                # the following users were chosen carefully for testing radius feature
                # please don't change them
                {
                    'username': 'admin',  # TODO: change to volt once it is in
                    'password': 'adminadmin',  # TODO: change to volt once it is in
                    'role': 'admin'
                },
                {
                    'username': 'testing',  # TODO: change to volt once it is in
                    'password': 'testing',  # TODO: change to volt once it is in
                    'role': 'monitor'
                }
            ],
            'special_user': [
                {
                    'username': 'root',
                    'password': 'root'
                }
            ]
        },

        'docker_radius_server': {
            'hostname': 'fit-l-vrt-60-086',  # TODO: change to volt once it is in
            'secret': 'testing123',  # TODO: change to volt once it is in
            'port': '1812',
            'auth-type': 'pap',
            'timeout': '5',
            'priority': 1,
            'users': [
                # the following users were chosen carefully for testing radius feature
                # please don't change them
                {
                    'username': 'rad1adm1',
                    'password': 'rad1adm1',
                    'role': 'admin'
                },
                {
                    'username': 'rad1mon1',
                    'password': 'rad1mon1',
                    'role': 'monitor'
                }
                # {
                #     'username': 'rad1adm2',
                #     'password': 'rad1adm2',
                #     'role': 'admin'
                # },
                # {
                #     'username': 'rad1mon2',
                #     'password': 'rad1mon2',
                #     'role': 'monitor'
                # }
                # # the following users were chosen carefully for testing radius feature
                # # please don't change them
                # {
                #     'username': 'azmy',  # TODO: change to volt once it is in
                #     'password': 'azmy',  # TODO: change to volt once it is in
                #     'role': 'admin'
                # },
                # {
                #     'username': 'admin1',  # TODO: change to volt once it is in
                #     'password': 'admin1',  # TODO: change to volt once it is in
                #     'role': 'monitor'
                # },
                # {
                #     'username': 'testing',  # TODO: change to volt once it is in
                #     'password': 'asdasd',  # TODO: change to volt once it is in
                #     'role': 'admin'
                # }
            ]
        }
    }

    SLEEP_TO_APPLY_CONFIGURATIONS = 5


class RadiusVmServer:
    USERS = [
        UserInfo(
            username='rad1adm1',
            password='rad1adm1',
            role=AaaConsts.ADMIN
        ),
        UserInfo(
            username='rad1mon1',
            password='rad1mon1',
            role=AaaConsts.MONITOR
        ),
    ]

    SERVER_IPV4 = RadiusServerInfo(
        hostname=AaaConsts.VM_AAA_SERVER_IPV4_ADDR,
        priority=1,
        secret='testing123',
        port=1812,
        timeout=5,
        auth_type=AaaConsts.PAP,
        users=USERS,
        ipv4_addr=AaaConsts.VM_AAA_SERVER_IPV4_ADDR,
    )
    SERVER_IPV6 = SERVER_IPV4.copy()
    SERVER_IPV6.hostname = AaaConsts.VM_AAA_SERVER_IPV6_ADDR
    SERVER_DN = SERVER_IPV4.copy()
    SERVER_DN.hostname = AaaConsts.VM_AAA_SERVER_DN

    SERVER_BY_ADDRESSING_TYPE = {
        AddressingType.IPV4: SERVER_IPV4,
        AddressingType.IPV6: SERVER_IPV6,
        AddressingType.DN: SERVER_DN
    }
