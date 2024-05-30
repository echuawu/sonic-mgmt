class GnmiMode:
    ONCE = 'once'
    POLL = 'poll'
    STREAM = ''
    ALL_MODES = [ONCE, POLL, STREAM]


ERR_GNMIC_NOT_INSTALLED = 'gnmic: command not found'
ERR_GNMIC_AUTH_FAIL = 'Unauthenticated desc = Authentication failed'
