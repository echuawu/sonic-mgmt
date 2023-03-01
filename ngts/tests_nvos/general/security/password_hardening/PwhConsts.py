
class PwhConsts:
    # pwh field names
    STATE = 'state'
    EXPIRATION = 'expiration'
    EXPIRATION_WARNING = 'expiration-warning'
    HISTORY_CNT = 'history-cnt'
    REJECT_USER_PASSW_MATCH = 'reject-user-passw-match'
    LEN_MIN = 'len-min'
    LOWER_CLASS = 'lower-class'
    UPPER_CLASS = 'upper-class'
    DIGITS_CLASS = 'digits-class'
    SPECIAL_CLASS = 'special-class'

    FIELDS = [STATE, EXPIRATION, EXPIRATION_WARNING, HISTORY_CNT, REJECT_USER_PASSW_MATCH, LEN_MIN, LOWER_CLASS,
              UPPER_CLASS, DIGITS_CLASS, SPECIAL_CLASS]

    # possible pwh field values
    ENABLED = 'enabled'
    DISABLED = 'disabled'

    # pwh field minimal values
    MIN = {     # todo: alonnn - verify defaults
        EXPIRATION: 1,
        EXPIRATION_WARNING: 1,
        HISTORY_CNT: 1,
        LEN_MIN: 6
    }

    # pwh field minimal values
    MAX = {     # todo: alonnn - verify defaults
        EXPIRATION: 365,
        EXPIRATION_WARNING: 30,
        HISTORY_CNT: 100,
        LEN_MIN: 32
    }

    # pwh valid field values
    VALID_VALUES = {     # todo: alonnn - verify defaults
        STATE: [ENABLED, DISABLED],
        EXPIRATION: list(map(str, list(range(MIN[EXPIRATION], MAX[EXPIRATION] + 1)) + [-1, 0])),
        EXPIRATION_WARNING: list(map(str, list(range(MIN[EXPIRATION_WARNING], MAX[EXPIRATION_WARNING] + 1)) + [-1, 0])),
        HISTORY_CNT: list(map(str, list(range(MIN[HISTORY_CNT], MAX[HISTORY_CNT] + 1)))),
        REJECT_USER_PASSW_MATCH: [ENABLED, DISABLED],
        LEN_MIN: list(map(str, list(range(MIN[LEN_MIN], MAX[LEN_MIN] + 1)))),
        LOWER_CLASS: [ENABLED, DISABLED],
        UPPER_CLASS: [ENABLED, DISABLED],
        DIGITS_CLASS: [ENABLED, DISABLED],
        SPECIAL_CLASS: [ENABLED, DISABLED]
    }

    # pwh default configuration
    DEFAULTS = {     # todo: alonnn - verify defaults
        STATE: ENABLED,
        EXPIRATION: '180',
        EXPIRATION_WARNING: '15',
        HISTORY_CNT: '10',
        REJECT_USER_PASSW_MATCH: ENABLED,
        LEN_MIN: '8',
        LOWER_CLASS: ENABLED,
        UPPER_CLASS: ENABLED,
        DIGITS_CLASS: ENABLED,
        SPECIAL_CLASS: ENABLED
    }

    # pwh configuration when feature (state) is disabled
    DISABLED_CONF = {     # todo: alonnn - verify defaults
        STATE: DISABLED,
        EXPIRATION: '99999',
        EXPIRATION_WARNING: '7',
        HISTORY_CNT: '0',
        REJECT_USER_PASSW_MATCH: DISABLED,
        LEN_MIN: '1',
        LOWER_CLASS: DISABLED,
        UPPER_CLASS: DISABLED,
        DIGITS_CLASS: DISABLED,
        SPECIAL_CLASS: DISABLED
    }

    SPECIAL_CLASS_CHARS = "`~!@#$%^&*()-_+=|[{}];:',<.>/"   # was also with "?"     # todo: alonnn - verify defaults

    # consts for tests
    ADMIN_TEST_USR = "test_admin"
    MONITOR_TEST_USR = "test_monitor"
    USER_OBJ = 'user_object'
    USER = 'user'
    PW = 'password'
    ROLE = 'role'
    MONITOR = 'monitor'
    ADMIN = 'admin'
    ERR_ITEM_NOT_EXIST = 'The requested item does not exist.'
