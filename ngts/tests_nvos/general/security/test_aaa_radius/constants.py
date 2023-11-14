

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
    RADIUS_DEFAULT_PRIORITY = 1
    RADIUS_DEFAULT_TIMEOUT = 3
    RADIUS_MAX_PRIORITY = 8
    RADIUS_MID_PRIORITY = 4
    RADIUS_MIN_PRIORITY = 1
    RADIUS_SERVER_USERS = 'users'
    RADIUS_SERVER_USERNAME = 'username'
    RADIUS_SERVER_USER_PASSWORD = 'password'
    AUTHENTICATION_FAILURE_MESSAGE = 'Authentication failure: unable to connect linux'
    AUTH_TYPES = ['chap', 'pap']

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
                    'username': 'azmy',  # TODO: change to volt once it is in
                    'password': 'azmy',  # TODO: change to volt once it is in
                    'role': 'admin'
                },
                {
                    'username': 'admin1',  # TODO: change to volt once it is in
                    'password': 'admin1',  # TODO: change to volt once it is in
                    'role': 'monitor'
                },
                {
                    'username': 'testing',  # TODO: change to volt once it is in
                    'password': 'asdasd',  # TODO: change to volt once it is in
                    'role': 'admin'
                }
            ]
        }
    }

    SLEEP_TO_APPLY_CONFIGURATIONS = 5
