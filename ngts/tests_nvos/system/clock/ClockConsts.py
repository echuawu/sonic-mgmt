from ngts.nvos_constants.constants_nvos import SystemConsts


class ClockConsts:
    TIMEZONE = SystemConsts.TIMEZONE    # 'timezone'
    DATETIME = SystemConsts.DATE_TIME   # 'date-time'

    DATETIME_MARGIN = 9  # tune this to decide what diff (in seconds) is ok between timedatectl and nv show system
    DEFAULT_TIMEZONE = "Etc/UTC"  # todo: what's the def timezone?
    PATH_TIMEZONE_YAML = "/auto/sw_system_release/nos/nvos/alonn/timezone.yaml"   # todo: where is it?

    TIMEDATECTL_CMD = "timedatectl"
    TIMEDATECTL_TIMEZONE_FIELD_NAME = "Time zone"
    TIMEDATECTL_DATETIME_FIELD_NAME = "Local time"

    ERR_EMPTY_PARAM = ["Incomplete Command"]
    ERR_INVALID_TIMEZONE = ["is not one of"]  # ["Error at timezone:", "is not one of"]   # todo: what should be the error message? verify with meir
    ERR_INVALID_DATETIME = ["Invalid Command: action change system date-time"]   # todo: what should be the error message? verify with meir
    ERR_DATETIME_NTP = ["Unable to change date and time in case NTP is enabled"]  # "Action failed with the following issue"
    ERR_OPENAPI_DATETIME = ["Date-time internal error occurred"]

    NTP = 'ntp'
    STATE = 'state'
    ENABLED = 'enabled'
    DISABLED = 'disabled'

    WAIT_TIME = 6
    NUM_SAMPLES = 3  # configure how many samples in several tests

    MIN_SYSTEM_DATE = SystemConsts.MIN_SYSTEM_DATE  # todo: verify this
    MAX_SYSTEM_DATE = SystemConsts.MAX_SYSTEM_DATE  # todo: verify this
    MIN_SYSTEM_DATETIME = SystemConsts.MIN_SYSTEM_DATETIME     # todo: verify this
    MAX_SYSTEM_DATETIME = SystemConsts.MAX_SYSTEM_DATETIME     # todo: verify this
