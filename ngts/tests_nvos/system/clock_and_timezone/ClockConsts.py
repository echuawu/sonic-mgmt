class ClockConsts:
    DESIGN_FINISHED = False  # todo: remove this after design finish implementation

    DATETIME_MARGIN = 5  # tune this to decide what diff (in seconds) is ok between timedatectl and nv show system
    DEFAULT_TIMEZONE = "Etc/UTC"  # todo: what's the def timezone?
    FILE_PATH_TIMEZONE_YAML = "/auto/sw_system_release/nos/nvos/alonn/timezone.yaml"   # todo: where is it?

    TIMEDATECTL_CMD = "timedatectl"
    TIMEDATECTL_TIMEZONE_FIELD_NAME = "Time zone"
    TIMEDATECTL_DATE_TIME_FIELD_NAME = "Local time"

    ERR_MSG_INVALID_TIMEZONE = "Invalid timezone arg"   # todo: what should be the error message? verify with meir
