from ngts.constants.constants import InfraConst


class DatabaseConst:
    APPL_DB_NAME = "APPL_DB"
    ASIC_DB_NAME = "ASIC_DB"
    COUNTERS_DB_NAME = "COUNTERS_DB"
    CONFIG_DB_NAME = "CONFIG_DB"
    STATE_DB_NAME = "STATE_DB"

    APPL_DB_ID = 0
    ASIC_DB_ID = 1
    COUNTERS_DB_ID = 2
    CONFIG_DB_ID = 4
    STATE_DB_ID = 6
    '''
     for each database we need:
         database id : id in redis
         database dict : includes all the possible tables and expected quantity of each table
         for example in config database we need a "IB_PORT" table for each port so possible quantities are 40 and 60

     '''
    APPL_DB_TABLES_DICT = {
        "IB_PORT_TABLE:Infiniband": [40, 64],
        "ALIAS_PORT_MAP": [40, 64],
        "IB_PORT_TABLE:Port": [2]
    }
    ASIC_DB_TABLES_DICT = {
        "ASIC_STATE:SAI_OBJECT_TYPE_PORT": [41, 65],
        "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": [1],
        "LANES": [1],
        "VIDCOUNTER": [1],
        "RIDTOVID": [1],
        "HIDDEN": [1],
        "COLDVIDS": [1]
    }
    COUNTERS_DB_TABLES_DICT = {
        "COUNTERS_PORT_NAME_MAP": [1],
        "COUNTERS:oid": [40, 64]
    }
    CONFIG_DB_TABLES_DICT = {
        "IB_PORT": [40, 64],
        "BREAKOUT_CFG": [40, 64],
        "FEATURE": [12],
        "CONFIG_DB_INITIALIZED": [1],
        "DEVICE_METADATA": [1],
        "XCVRD_LOG": [1],
        "VERSIONS": [1],
        "KDUMP": [1]
    }


class NvosConst:

    PORT_STATUS_UP = 'up'
    PORT_STATUS_DOWN = 'down'

    DOCKER_STATUS_UP = 'Up'
    SERVICE_STATUS_ACTIVE = 'active'

    DOCKERS_LIST = ['pmon', 'syncd-ibv0', 'swss-ibv0', 'database']
    PORT_STATUS_LABEL = 'admin_status'
    PORT_CONFIG_DB_TABLES_PREFIX = "IB_PORT"
    IMAGES_PATH_ON_SWITCH = "/tmp/temp_nvos.bin"
    FM_PATH_ON_SWITCH = "/tmp/temp_fw.bin"

    ROOT_USER = 'root'
    ROOT_PASSWORD = '3tango'

    SONIC_MGMT = 'sonic_mgmt'

    DEFAULT_PASS = 'YourPaSsWoRd'


class ApiType:
    NVUE = "NVUE"
    OPENAPI = "OpenApi"


class OutputFormat:
    auto = 'auto'
    json = 'json'
    yaml = 'yaml'


class OpenApiReqType:
    GET = 'GET'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    APPLY = 'APPLY'
    ACTION = 'ACTION'


class ActionType:
    BOOT_NEXT = '@boot-next'
    CLEANUP = '@cleanup'
    CLEAR = '@clear'
    DISCONNECT = '@disconnect'
    GENERATE = '@generate'
    INSTALL = '@install'
    REBOOT = '@reboot'
    RENEW = '@renew'
    ROTATE = '@rotate'
    TURNOFF = '@turn-off'
    TURNON = '@turn-on'
    UNINSTALL = '@uninstall'
    FETCH = '@fetch'
    DELETE = '@delete'
    RENAME = '@rename'
    UPLOAD = '@upload'
    RESET = '@reset'


class SystemConsts:
    HOSTNAME = 'hostname'
    REBOOT = 'reboot'
    BUILD = 'build'
    PLATFORM = 'platform'
    PRODUCT_NAME = 'product-name'
    PRODUCT_RELEASE = 'product-release'
    SWAP_MEMORY = 'swap-memory'
    SYSTEM_MEMORY = 'system-memory'
    UPTIME = 'uptime'
    TIMEZONE = 'timezone'
    VERSION = 'version'

    PRE_LOGIN_MESSAGE = 'pre-login'
    POST_LOGIN_MESSAGE = 'post-login'

    REBOOT_HISTORY = 'history'
    REBOOT_REASON = 'reason'

    VERSION_BUILD_DATE = 'build-date'
    VERSION_BUILT_BY = 'built-by'
    VERSION_IMAGE = 'image'
    VERSION_KERNEL = 'kernel'

    PROFILE_ADAPTIVE_ROUTING = 'adaptive-routing'
    PROFILE_ADAPTIVE_ROUTING_GROUPS = 'adaptive-routing-groups'
    PROFILE_BREAKOUT_MODE = 'breakout-mode'
    PROFILE_IB_ROUTING = 'ib-routing'
    PROFILE_NUMBER_OF_SWIDS = 'num-of-swids'
    PROFILE_OUTPUT_FIELDS = [PROFILE_ADAPTIVE_ROUTING, PROFILE_ADAPTIVE_ROUTING_GROUPS, PROFILE_BREAKOUT_MODE,
                             PROFILE_IB_ROUTING, PROFILE_NUMBER_OF_SWIDS]
    ADAPTIVE_ROUTING_DEFAULT_ADAPTIVE_GROUPS = 2048
    BREAKOUT_MODE_DEFAULT_ADAPTIVE_GROUPS = 1792
    DEFAULT_NUM_SWIDS = 1
    PROFILE_STATE_ENABLED = 'enabled'
    PROFILE_STATE_DISABLED = 'disabled'
    DEFAULT_SYSTEM_PROFILE_VALUES = [PROFILE_STATE_ENABLED, ADAPTIVE_ROUTING_DEFAULT_ADAPTIVE_GROUPS,
                                     PROFILE_STATE_DISABLED, PROFILE_STATE_DISABLED, DEFAULT_NUM_SWIDS]

    HOSTNAME_DEFAULT_VALUE = 'nvos'
    PRE_LOGIN_MESSAGE_DEFAULT_VALUE = "NVOS switch"
    POST_LOGIN_MESSAGE_DEFAULT_VALUE = "\\n \u2588\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2557   " \
                                       "\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 " \
                                       "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\\n " \
                                       "\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2551   " \
                                       "\u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557" \
                                       "\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\\n \u2588\u2588\u2554\u2588" \
                                       "\u2588\u2557 \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588" \
                                       "\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588" \
                                       "\u2557\\n \u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u255a" \
                                       "\u2588\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588" \
                                       "\u2551\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\\n \u2588\u2588\u2551 " \
                                       "\u255a\u2588\u2588\u2588\u2588\u2551" \
                                       " \u255a\u2588\u2588\u2588\u2588\u2554\u255d " \
                                       "\u255a\u2588\u2588\u2588\u2588\u2588" \
                                       "\u2588\u2554\u255d\u2588\u2588\u2588\u2588" \
                                       "\u2588\u2588\u2588\u2551\\n \u255a" \
                                       "\u2550\u255d  \u255a\u2550\u2550\u2550\u255d" \
                                       "  \u255a\u2550\u2550\u2550\u255d   \u255a\u2550\u2550\u2550\u2550\u2550\u255d" \
                                       " \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\\n\\n"
    ACTIONS_GENERATE_SINCE = 'since'

    DEFAULT_USER_ADMIN = 'admin'
    DEFAULT_USER_MONITOR = 'monitor'
    USER_ROLE = 'role'
    USER_STATE = 'state'
    USER_FULL_NAME = 'full-name'
    USER_ADMIN_DEFAULT_FULL_NAME = 'System Administrator'
    USER_MONITOR_DEFAULT_FULL_NAME = 'System Monitor'
    USER_STATE_ENABLED = 'enabled'
    USER_STATE_DISABLED = 'disabled'
    USER_PASSWORD = 'password'
    USER_HASHED_PASSWORD = 'hashed-password'
    USER_PASSWORDS_DEFAULT_VALUE = '*'
    ROLE_LABEL = USER_ROLE
    ROLE_CONFIGURATOR = 'admin'
    ROLE_VIEWER = 'monitor'
    ROLE_GROUPS = 'groups'
    ROLE_PERMISSIONS = 'permissions'
    ROLE_CONFIGURATOR_DEFAULT_GROUPS = 'apply,set,show'
    ROLE_VIEWER_DEFAULT_GROUPS = 'show'
    USERNAME_MAX_LEN = 32
    USERNAME_PASSWORD_HARDENING_STATE = 'state'
    USERNAME_VALID_CHARACTERS = list(map(chr, range(65, 91))) + list(map(chr, range(97, 123)))
    USERNAME_INVALID_CHARACTERS = list(map(chr, range(48, 57)))
    USERNAME_PASSWORD_DIGITS_LABEL = 'digits-class'
    USERNAME_PASSWORD_DIGITS_LIST = list(map(chr, range(48, 57)))
    USERNAME_PASSWORD_LENGTH_LABEL = 'len-min'
    USERNAME_PASSWORD_LENGTH_DEFAULT = 8
    USERNAME_PASSWORD_LOWER_LABEL = 'lower-class'
    USERNAME_PASSWORD_LOWER_LIST = list(map(chr, range(97, 123)))
    USERNAME_PASSWORD_UPPER_LABEL = 'upper-class'
    USERNAME_PASSWORD_UPPER_LIST = list(map(chr, range(65, 91)))
    USERNAME_PASSWORD_SPECIAL_LABEL = 'special-class'
    USERNAME_PASSWORD_SPECIAL_LIST = "_#)(^"   # noqa: E402 "#$%&'()*+,-./:;<=>@[\]^_`{|}~"
    PASSWORD_HARDENING_DEFAULT = [USERNAME_PASSWORD_DIGITS_LABEL, USERNAME_PASSWORD_LOWER_LABEL,
                                  USERNAME_PASSWORD_UPPER_LABEL, USERNAME_PASSWORD_SPECIAL_LABEL]
    PASSWORD_HARDENING_RUNNING_PROCESSES = 'Running processes'
    PASSWORD_HARDENING_LABEL = 'password-hardening'

    PASSWORD_HARDENING_DICT = {
        USERNAME_PASSWORD_DIGITS_LABEL: USERNAME_PASSWORD_DIGITS_LIST,
        USERNAME_PASSWORD_LOWER_LABEL: USERNAME_PASSWORD_LOWER_LIST,
        USERNAME_PASSWORD_UPPER_LABEL: USERNAME_PASSWORD_UPPER_LIST,
        USERNAME_PASSWORD_SPECIAL_LABEL: USERNAME_PASSWORD_SPECIAL_LIST
    }

    SHOW_VALUE_YES = 'yes'
    DHCP_SHOW_FIELDS = ['has-lease', 'is-running', 'set-hostname', 'state']
    DHCP_SHOW_DEFAULT_VALUES = [SHOW_VALUE_YES, SHOW_VALUE_YES, USER_STATE_ENABLED, USER_STATE_ENABLED]

    MEMORY_PHYSICAL_KEY = 'Physical'
    MEMORY_SWAP_KEY = 'Swap'
    MEMORY_PERCENT_THRESH_MIN = 0.0
    MEMORY_PERCENT_THRESH_MAX = 60.0

    CPU_CORE_COUNT_KEY = 'core-count'
    CPU_MODEL_KEY = 'model'
    CPU_UTILIZATION_KEY = 'utilization'
    CPU_PERCENT_THRESH_MIN = 0.0
    CPU_PERCENT_THRESH_MAX = 35.0


class ActionConsts:
    CLEANUP = "cleanup"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    BOOT_NEXT = "boot-next"
    GENERATE = "generate"
    FETCH = "fetch"


class IpConsts:
    MIN_IPV6_GROUP_VALUE = 0
    MAX_IPV6_GROUP_VALUE = 65535
    ARP_TIMEOUT = "arp-timeout"
    AUTOCONF = "autoconf"


class ConfigConsts:
    HISTORY_APPLY_ID = 'apply-id'
    HISTORY_USER = 'user'
    APPLY_YES = '-y'
    APPLY_ASSUME_YES = '--assume-yes'
    APPLY_ASSUME_NO = '--assume-no'
    APPLY_CONFIRM_NO = '--confirm-yes'
    APPLY_CONFIRM_YES = '--confirm-no'
    APPLY_CONFIRM_STATUS = '--confirm-status'


class PlatformConsts:
    PLATFORM_FW = "firmware"
    PLATFORM_ENVIRONMENT = "environment"
    PLATFORM_HW = "hardware"
    PLATFORM_SW = "software"
    PLATFORM_OUT_COMP = ["fan", "led", "psu", "temperature", "component", PLATFORM_HW, PLATFORM_ENVIRONMENT]
    PLATFORM_COMP = [PLATFORM_FW, PLATFORM_ENVIRONMENT, PLATFORM_HW, PLATFORM_SW]
    FW_BIOS = "BIOS"
    FW_CPLD = "CPLD"
    FW_ONIE = "ONIE"
    FW_SSD = "SSD"
    FW_COMP = [FW_BIOS, FW_ONIE, FW_SSD, FW_CPLD + '1', FW_CPLD + '2', FW_CPLD + '3']
    FW_FIELDS = ["actual-firmware", "installed-firmware", "part-number", "serial-number", "type"]
    ENV_FAN = "fan"
    ENV_LED = "led"
    ENV_UID = "UID"
    ENV_PSU = "psu"
    ENV_TEMP = 'temperature'
    ENV_COMP = [ENV_FAN, ENV_LED, ENV_PSU, ENV_TEMP]
    ENV_FAN_COMP = ["max-speed", "min-speed", "current-speed", "state"]
    ENV_LED_COLOR_LABEL = "color"
    ENV_LED_COLOR_GREEN = "green"
    ENV_LED_COLOR_RED = "red"
    ENV_LED_COLOR_BLUE = "blue"
    ENV_LED_COLOR_AMBER = "amber"
    ENV_LED_COLOR_OFF = "off"
    ENV_LED_TURN_ON = "on"
    ENV_LED_COLOR_OPTIONS = [ENV_LED_COLOR_GREEN, ENV_LED_COLOR_RED, ENV_LED_COLOR_OFF,
                             ENV_LED_COLOR_BLUE, ENV_LED_COLOR_AMBER]
    ENV_LED_COMP = ["PSU_STATUS", "STATUS", "UID"]
    ENV_PSU_PROP = ["capacity", "current", "power", "state", "voltage"]
    HW_ASIC_COUNT = "asic-count"
    HW_MODEL = "model"
    HW_MAC = "system-mac"
    HW_COMP = [HW_ASIC_COUNT, "cpu", "cpu-load-averages", "disk-size", "hw-revision", "manufacturer",
               "memory", HW_MODEL, "onie-version", "part-number", "product-name", "serial-number",
               HW_MAC, "system-uuid"]
    HW_COMP_SWITCH = "SWITCH"
    HW_COMP_LIST = ["hardware-version", HW_MODEL, "serial", "state", "type"]


class IbConsts:
    MAX_NODES = 'max-nodes'
    MAX_NODES_DEFAULT_VALUE = '2048'
    IS_RUNNING = 'is-running'
    IS_RUNNING_NO = 'no'
    IS_RUNNING_YES = 'yes'
    SM_STATE = 'state'
    SM_STATE_ENABLE = 'enabled'
    SM_STATE_DISABLE = 'disabled'
    SM_PRIORITY = 'sm-priority'
    SM_SL = 'sm-sl'
    PRIO_SL_DEFAULT_VALUE = '0'
    FILES = 'files'
    SIGNAL_DEGRADE_STATE = "state"
    SIGNAL_DEGRADE_ACTION = "action"
    SIGNAL_DEGRADE_STATE_ENABLED = "enabled"
    SIGNAL_DEGRADE_STATE_DISABLED = "disabled"
    SIGNAL_DEGRADE_ACTION_SHUTDOWN = "shutdown"
    SIGNAL_DEGRADE_ACTION_NO_SHUTDOWN = "no-shutdown"
    SIGNAL_DEGRADE = "signal-degrade"
    DEVICE_ASIC_PREFIX = 'ASIC'
    DEVICE_SYSTEM = 'SYSTEM'
    DEVICE_ASIC_LIST = ['guid', 'lid', 'subnet', 'type']
    DEVICE_SYSTEM_LIST = ['guid']
    GUID_FORMAT = "[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){6}$"
    IBDIAGNET_PATH = '/var/tmp/ibdiagnet2'
    IBDIAGNET_ZIPPED_FOLDER_PATH = '/host/ibdiagnet'
    IBDIAGNET_COMMAND = 'ibdiagnet'
    IBDIAGNET_FILE_NAME = 'ibdiagnet2_output.tgz'
    IBDIAGNET_LOG_FINE_MIN_LINES = 50
    IBDIAGNET_PHY_INFO = '--get_phy_info'
    IBDIAGNET_CABLE_INFO = '--get_cable_info'
    IBDIAGNET_EXPECTED_FILES_LIST = ['ibdiagnet2.db_csv', 'ibdiagnet2.ibnetdiscover', 'ibdiagnet2.log', 'ibdiagnet2.lst',
                                     'ibdiagnet2.net_dump', 'ibdiagnet2.nodes_info', 'ibdiagnet2.pkey', 'ibdiagnet2.pm',
                                     'ibdiagnet2.sm', 'ibdiagnet2.vports', 'ibdiagnet2.vports_pkey']
    IBDIAGNET_EXPECTED_MESSAGE = 'ibdiagnet output files were archived into ibdiagnet2_output.tgz'


class ImageConsts:
    NEXT_IMG = 'next'
    CURRENT_IMG = 'current'
    PARTITION1_IMG = 'partition1'
    PARTITION2_IMG = 'partition2'
    SCP_PATH = 'scp://{}:{}@{}'.format(NvosConst.ROOT_USER, NvosConst.ROOT_PASSWORD,
                                       InfraConst.HTTP_SERVER.replace("http://", ""))


class SyslogConsts:
    FORMAT = 'format'
    FIREWAL_NAME = 'firewall-name'
    TRAP = 'trap'
    SERVER = 'server'
    SERVER_ID = 'server-id'
    FILTER = 'filter'
    EXCLUDE = 'exclude'
    INCLUDE = 'include'
    PORT = 'port'
    VRF = 'vrf'
    PROTOCOL = 'protocol'
    STANDARD = 'standard'
    WELF = 'welf'
    DEFAULT_PORT = 514
    MODULE_LINE = "module(load=\"im{protocol}\")"
    PORT_LINE = "input(type=\"im{protocol}\" port=\"{port}\")"
    RSYSLOG_CONF_FILE = '/etc/rsyslog.conf'
    MULTIPLE_SERVERS_NUMBER = 10
    CONFIG_TIME_DIFF_THRESHOLD = 1.0      # [sec]
    SHOW_TIME_DIFF_THRESHOLD = 1.0        # [sec]
    CPU_UTILIZATION_DIFF_THRESHOLD = 5.0  # [percent]


class SyslogSeverityLevels:
    NONE = 'none'
    CRIT = 'crit'
    CRITICAL = 'critical'
    ERROR = 'error'
    WARN = 'warn'
    NOTICE = 'notice'
    INFO = 'info'
    DEBUG = 'debug'
    SEVERITY_LEVEL_LIST = [DEBUG, INFO, NOTICE, WARN, ERROR, CRITICAL]
    SEVERITY_LEVEL_DICT = {DEBUG: DEBUG,   # key : severity level to configure, value: priority level to send msg, and show commands
                           INFO: INFO,
                           NOTICE: NOTICE,
                           WARN: WARN,
                           ERROR: ERROR,
                           CRITICAL: CRIT}
