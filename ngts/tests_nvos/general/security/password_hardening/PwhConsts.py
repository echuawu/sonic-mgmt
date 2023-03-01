
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

    # pwh field default values
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
