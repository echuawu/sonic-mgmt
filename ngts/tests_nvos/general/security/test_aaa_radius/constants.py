

class RadiusConstans:
    '''
    constants for Radius suit case
    '''
    # keys
    RADIUS_HOSTNAME = 'hostname'
    RADIUS_PASSWORD = 'password'
    RADIUS_TIMEOUT = 'timeout'
    RADIUS_AUTH_PORT = 'auth-port'
    RADIUS_AUTH_TYPE = 'auth-type'
    RADIUS_PRIORITY = 'priority'
    RADIUS_DEFAULT_PRIORITY = 1
    RADIUS_DEFAULT_TIMEOUT = 3

    RADIUS_SERVERS_DICTIONARY = {
        'physical_radius_server': {
            'hostname': '10.7.34.20',
            'password': 'testing-radius',  # TODO: change to volt once it is in
            'auth-port': '1812',
            'auth-type': 'pap',
            'timeout': '5',
            'is_docker': False,
            'users': [
                {
                    'username': 'dror',  # TODO: change to volt once it is in
                    'password': 'dror',  # TODO: change to volt once it is in
                    'role': 'monitor'
                }
            ]
        },

        '10.237.116.91': {
            'hostname': '10.237.116.91',  # TODO: change to volt once it is in
            'password': 'testing123',  # TODO: change to volt once it is in
            'auth-port': '1812',
            'auth-type': 'pap',
            'timeout': '5',
            'is_docker': False,
            'users': [
                {
                    'username': 'azmy',  # TODO: change to volt once it is in
                    'password': 'azmy',  # TODO: change to volt once it is in
                    'role': 'monitor'
                }
            ]
        }
    }
