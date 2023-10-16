import os
from ngts.constants.constants import InfraConst
from enum import Enum


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

    REDIS_DB_NUM_TO_NAME = {0: APPL_DB_NAME, 1: ASIC_DB_NAME, 2: COUNTERS_DB_NAME, 4: CONFIG_DB_NAME, 6: STATE_DB_NAME}
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
    DESCRIPTION = 'description'
    PORT_STATUS_UP = 'up'
    PORT_STATUS_DOWN = 'down'
    DOCKER_AUTO_RESTART = 'auto_restart'
    DOCKER_STATUS_ENABLED = 'enabled'
    DOCKER_STATUS_DISABLED = 'disabled'
    DOCKER_STATUS_UP = 'Up'
    SERVICE_STATUS_ACTIVE = 'active'

    DOCKERS_LIST = ['pmon', 'syncd-ibv0', 'swss-ibv0', 'database']
    DOCKER_PER_ASIC_LIST = ['syncd-ibv0', 'swss-ibv0', 'database']
    SYM_MGR_SERVICES = ['configmgrd.service', 'countermgrd.service', 'portsyncmgrd.service']
    PORT_STATUS_LABEL = 'admin_status'
    PORT_CONFIG_DB_TABLES_PREFIX = "IB_PORT"
    IMAGES_PATH_ON_SWITCH = "/tmp/temp_nvos.bin"
    FM_PATH_ON_SWITCH = "/tmp/temp_fw.bin"

    ROOT_USER = os.getenv("VM_USER")
    ROOT_PASSWORD = os.getenv("VM_PASSWORD")

    SONIC_MGMT = 'sonic_mgmt'

    DEFAULT_PASS = os.getenv("NVU_SWITCH_PASSWORD")

    REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {ip} -U {username} -P {password} chassis power cycle"

    DATE_TIME_REGEX = "\\w{3}\\s{1,2}\\d{1,2} \\d\\d:\\d\\d:\\d\\d(?:.\\d+)?"

    FW_DUMP_ME_SCRIPT_PATH = "/auto/sw_system_project/NVOS_INFRA/security/verification/fw_dump_me/sxd_api_crash_fw.py"
    DESTINATION_FW_SCRIPT_PATH = "/var/tmp/"
    SDK_DUMP_FOLDER = "/var/log/mellanox/sdk-dumps/"
    MARS_RESULTS_FOLDER = "/auto/sw_regression/system/NVOS/MARS/results/"

    HOST_HA = 'ha'
    HOST_HB = 'hb'


class ApiType:
    NVUE = "NVUE"
    OPENAPI = "OpenApi"
    # list of all api types
    ALL_TYPES = [NVUE, OPENAPI]


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
    CHANGE = '@change'
    CLEAR = '@clear'


class SystemConsts:
    HOSTNAME = 'hostname'
    STATUS = 'status'
    STATUS_DEFAULT_VALUE = 'System is ready'
    STATUS_NOT_OK = 'System is not ready'
    STATUS_UP = 'UP'
    STATUS_DOWN = 'DOWN'
    STATUS_FAILS = ''
    FAE_SYSTEM_STATE = 'state'
    FAE_SYSTEM_STATE_DEFAULT_VALUE = 'enabled'
    REBOOT = 'reboot'
    BUILD = 'build'
    PLATFORM = 'platform'
    PRODUCT_NAME = 'product-name'
    PRODUCT_RELEASE = 'product-release'
    SWAP_MEMORY = 'swap-memory'
    SYSTEM_MEMORY = 'system-memory'
    UPTIME = 'uptime'
    TIMEZONE = 'timezone'
    DATE_TIME = 'date-time'
    VERSION = 'version'
    SECURITY = 'security'
    DATE_TIME = 'date-time'
    TECHSUPPORT_FILES_PATH = '/host/dump/'

    MIN_SYSTEM_YEAR = '1970'
    MAX_SYSTEM_YEAR = '2037'
    MIN_SYSTEM_DATE = MIN_SYSTEM_YEAR + "-01-01"
    MAX_SYSTEM_DATE = MAX_SYSTEM_YEAR + "-12-31"
    MIN_SYSTEM_DATETIME = MIN_SYSTEM_DATE + " 00:00:00"
    MAX_SYSTEM_DATETIME = MAX_SYSTEM_DATE + " 23:59:59"

    PRE_LOGIN_MESSAGE = 'pre-login'
    POST_LOGIN_MESSAGE = 'post-login'
    POST_LOGOUT_MESSAGE = 'post-logout'

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

    SNMP_REFRESH_INTERVAL = 'auto-refresh-interval'
    SNMP_IS_RUNNING = 'is-running'
    SNMP_LISTENING_ADDRESS = 'listening-address'
    SNMP_READONLY_COMMUNITY = 'readonly-community'
    SNMP_STATE = 'state'
    SNMP_SYSTEM_CONTACT = 'system-contact'
    SNMP_SYSTEM_LOCATION = 'system-location'
    SNMP_OUTPUT_FIELDS = [SNMP_IS_RUNNING, SNMP_LISTENING_ADDRESS, SNMP_READONLY_COMMUNITY, SNMP_STATE]
    SNMP_DEFAULT_STATE = 'disabled'
    SNMP_DEFAULT_REFRESH_INTERVAL = 60
    SNMP_DEFAULT_IS_RUNNING = 'no'
    SNMP_DEFAULT_LISTENING_ADDRESS = {}
    SNMP_DEFAULT_READONLY_COMMUNITY = {}
    SNMP_DEFAULT_VALUES = [SNMP_DEFAULT_IS_RUNNING, SNMP_DEFAULT_LISTENING_ADDRESS,
                           SNMP_DEFAULT_READONLY_COMMUNITY, SNMP_DEFAULT_STATE]

    SSH_CONFIG_AUTH_RETRIES = 'authentication-retries'
    SSH_CONFIG_INACTIV_TIMEOUT = 'inactivity-timeout'
    SSH_CONFIG_LOGIN_TIMEOUT = 'login-timeout'
    SSH_CONFIG_MAX_SESSIONS = 'max-sessions'
    SSH_CONFIG_PORTS = 'ports'
    SSH_CONFIG_OUTPUT_FIELDS = [SSH_CONFIG_AUTH_RETRIES, SSH_CONFIG_INACTIV_TIMEOUT, SSH_CONFIG_LOGIN_TIMEOUT,
                                SSH_CONFIG_MAX_SESSIONS, SSH_CONFIG_PORTS]
    SSH_CONFIG_DEFAULT_AUTH_RETRY = '6'
    SSH_CONFIG_DEFAULT_INACTIV_TIMEOUT = '15'
    SSH_CONFIG_DEFAULT_LOGIN_TIMEOUT = '120'
    SSH_CONFIG_DEFAULT_MAX_SESSION = '100'
    SSH_CONFIG_DEFAULT_PORTS = '22'
    SSH_CONFIG_MIN_MAX_SESSION = 3
    SSH_CONFIG_MAX_MAX_SESSION = 100
    SSH_CONFIG_MIN_INACTIV_TIMEOUT = 0
    SSH_CONFIG_MAX_INACTIV_TIMEOUT = 35000
    SSH_CONFIG_DEFAULT_VALUES = [SSH_CONFIG_DEFAULT_AUTH_RETRY, SSH_CONFIG_DEFAULT_INACTIV_TIMEOUT,
                                 SSH_CONFIG_DEFAULT_LOGIN_TIMEOUT, SSH_CONFIG_DEFAULT_MAX_SESSION,
                                 SSH_CONFIG_DEFAULT_PORTS]

    SERIAL_CONSOLE_INACTIV_TIMEOUT = 'inactivity-timeout'
    SERIAL_CONSOLE_SYSRQ_CAPABILITIES = 'sysrq-capabilities'
    SERIAL_CONSOLE_DEFAULT_INACTIV_TIMEOUT = '15'
    SERIAL_CONSOLE_DEFAULT_SYSRQ_CAPABILITIES = 'disabled'
    SERIAL_CONSOLE_ENABLED_SYSRQ_CAPABILITIES = 'enabled'

    HOSTNAME_DEFAULT_VALUE = 'nvos'
    PRE_LOGIN_MESSAGE_DEFAULT_VALUE = "NVOS switch"
    POST_LOGIN_MESSAGE_DEFAULT_VALUE = "\n \u2588\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2557   " \
                                       "\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 " \
                                       "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\n \u2588\u2588\u2588\u2588" \
                                       "\u2557  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588" \
                                       "\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550" \
                                       "\u2550\u2550\u255d\n \u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588" \
                                       "\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551   " \
                                       "\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\n " \
                                       "\u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u255a\u2588" \
                                       "\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551" \
                                       "\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\n \u2588\u2588\u2551 \u255a" \
                                       "\u2588\u2588\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2554\u255d " \
                                       "\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588" \
                                       "\u2588\u2588\u2588\u2588\u2551\n \u255a\u2550\u255d  \u255a\u2550\u2550" \
                                       "\u2550\u255d  \u255a\u2550\u2550\u2550\u255d   \u255a\u2550\u2550\u2550" \
                                       "\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\n"
    POST_LOGOUT_MESSAGE_DEFAULT_VALUE = ""
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
    USERNAME_PASSWORD_HARDENING_HISTORY_COUNT = 'history-cnt'
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
    MEMORY_PERCENT_THRESH_MAX = 70.0

    CPU_CORE_COUNT_KEY = 'core-count'
    CPU_MODEL_KEY = 'model'
    CPU_UTILIZATION_KEY = 'utilization'
    CPU_PERCENT_THRESH_MIN = 0.0
    CPU_PERCENT_THRESH_MAX = 60.0

    HEALTH_STATUS = "health-status"

    EXTERNAL_API_STATE = 'state'
    EXTERNAL_API_STATE_ENABLED = 'enabled'
    EXTERNAL_API_STATE_DISABLED = 'disabled'
    EXTERNAL_API_LISTEN = 'listening-address'
    EXTERNAL_API_PORT = 'port'
    EXTERNAL_API_RULE = 'rule'
    EXTERNAL_API_STATE_DEFAULT = 'enabled'
    EXTERNAL_API_PORT_DEFAULT = '443'
    EXTERNAL_API_PORT_NON_DEFAULT = '442'
    EXTERNAL_API_LISTEN_DEFAULT = {}
    EXTERNAL_API_LISTEN_LOCALHOST = 'localhost'


class DocumentsConsts:
    MIN_FILES_SIZE = 30000
    TYPE_EULA = 'EULA'
    TYPE_USER_MANUAL = 'User manual'
    TYPE_OPEN_SOURCE_LICENSES = 'Open source licenses'
    TYPE_RELEASE_NOTES = 'Release notes'
    PATH_EULA = "/usr/share/nginx/html/system_documents/eula/NVOS_EULA.pdf"
    PATH_USER_MANUAL = "/usr/share/nginx/html/system_documents/user_manual/NVOS_User_Manual.pdf"
    PATH_OPEN_SOURCE_LICENSES = "/usr/share/nginx/html/system_documents/open_source_licenses/Open_Source_Licenses.txt"
    PATH_RELEASE_NOTES = "/usr/share/nginx/html/system_documents/release_notes/NVOS_Release_Notes.pdf"
    FILE_NAME_EULA = "NVOS_EULA.pdf"
    FILE_NAME_USER_MANUAL = "NVOS_User_Manual.pdf"
    FILE_NAME_OPEN_SOURCE_LICENSES = "Open_Source_Licenses.txt"
    FILE_NAME_RELEASE_NOTES = "NVOS_Release_Notes.pdf"


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
    REVISION_ID = 'rev-id'
    REF = 'ref'
    HISTORY_USER = 'user'
    APPLY_YES = '-y'
    APPLY_ASSUME_YES = '--assume-yes'
    APPLY_ASSUME_NO = '--assume-no'
    APPLY_CONFIRM_NO = '--confirm-yes'
    APPLY_CONFIRM_YES = '--confirm-no'
    APPLY_CONFIRM_STATUS = '--confirm-status'


class PlatformConsts:
    PLATFORM_FW = "firmware"
    FM_PATH = "/auto/sw_system_project/MLNX_OS_INFRA/mlnx_os2/sx_mlnx_fw/"
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
    HARDWARE_TRANCEIVER_DIAGNOSTIC_STATUS = "diagnostics-status"
    HARDWARE_TRANCEIVER_NOT_EXIST = "Non present module"
    HARDWARE_TRANCEIVER_NOT_DDMI = "No Diagnostic Data Available. Module is not DDMI capable"
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
    ACTUAL_FIRMWARE = 'actual-firmware'
    INSTALLED_FIRMWARE = 'installed-firmware'
    TYPE = 'type'
    ASIC = 'asic'
    SWID = 'swid'
    FW_ASIC = 'ASIC'
    FW_STABLE_VERSION = 'rel-31_2010_4100-004-EVB.mfa'
    SCP_PATH = 'scp://{}:{}@{}'.format(NvosConst.ROOT_USER, NvosConst.ROOT_PASSWORD,
                                       'fit70')


class NtpConsts:
    class Authentication(Enum):
        ENABLED = 'enabled'
        DISABLED = 'disabled'

    class Dhcp(Enum):
        ENABLED = 'enabled'
        DISABLED = 'disabled'

    class State(Enum):
        ENABLED = 'enabled'
        DISABLED = 'disabled'

    class Trusted(Enum):
        YES = 'yes'
        NO = 'no'

    class AssociationType(Enum):
        SERVER = 'server'
        PEER = 'peer'
        POOL = 'pool'

    class Status(Enum):
        SYNCHRONISED = 'synchronised'
        UNSYNCHRONISED = 'unsynchronised'

    class Vrf(Enum):
        DEFAULT = 'default'
        MGMT = 'mgmt'

    class Version(Enum):
        VERSION_3 = '3'
        VERSION_4 = '4'

    class AggressivePolling(Enum):
        ON = 'on'
        OFF = 'off'

    class KeyType(Enum):
        MD5 = 'md5'
        SHA1 = 'sha1'

    class Listen(Enum):
        ETH0 = 'eth0'

    AUTHENTICATION = 'authentication'
    DHCP = 'dhcp'
    LISTEN = 'listen'
    OFFSET = 'offset'
    REFERENCE = 'reference'
    SERVER = 'server'
    STATE = 'state'
    DHCP = 'dhcp'
    STATUS = 'status'
    VRF = 'vrf'
    KEY = 'key'
    VALUE = 'value'
    TYPE = 'type'
    RESOLVE_AS = 'resolve-as'
    ASSOCIATION_TYPE = 'association-type'
    AGGRESSIVE_POLLING = 'aggressive-polling'
    VERSION = 'version'
    TRUSTED = 'trusted'
    SERVER_ID = 'server-id'
    KEY_1 = '6'
    KEY_2 = '09876'
    KEY_VALUE = 'v1234'
    KEY1_VALUE = 'temp_value'
    KEY2_VALUE = 'temp_value123'
    SERVER1_IPV4 = '10.7.77.134'
    SERVER2_IPV4 = '10.7.77.135'
    HOSTNAME_SUFFIX = '.lab.mtl.com'
    SERVER2_HOSTNAME = 'l-coreslave' + HOSTNAME_SUFFIX
    SERVER3_IPV4 = '10.7.77.136'
    DUMMY_SERVER1 = 'server1'
    DUMMY_SERVER2 = 'server2'
    DUMMY_SERVER3 = 'server3'
    DUMMY_SERVER4 = 'server4'
    DUMMY_SERVER5 = 'server5'
    DUMMY_SERVER6 = 'server6'
    DUMMY_SERVER7 = 'server7'
    DUMMY_SERVER8 = 'server8'
    SERVER_FAILED = 'DNS resolution failed'
    MULTIPLE_SERVERS_NUMBER = 11
    CONFIG_TIME_DIFF_THRESHOLD = 2.0  # [sec]
    SHOW_TIME_DIFF_THRESHOLD = 0.5  # [sec]
    SYNCHRONIZATION_MAX_TIME = 100  # [sec]
    SYNCHRONIZATION_TIME_AFTER_REBOOT = 60  # [sec]
    NUMBER_OF_ITERATION = 5
    OLD_DATE = '2 OCT 2006 18:00:00'  # [Date and Time]
    NTP_MAX_DIFF_TIME = 180  # [sec]
    NTP_SERVER_FILES = "/auto/sw_system_project/NVOS_INFRA/verification/ntp/*"

    INVALID_STATE = 'enable1'
    INVALID_AUTHENTICATION = 'disable1'
    INVALID_LISTEN = 'eth1'
    INVALID_DHCP = 'enabled1'
    INVALID_VRF = 'temp_str'
    INVALID_HIGHER_KEY = '65536'
    INVALID_LOWER_KEY = '0'
    INVALID_KEY_TYPE = '0'
    INVALID_KEY_TRUSTED = 'noo'
    INVALID_SERVER = '1234.1234'
    INVALID_SERVER_ASSOCIATION_TYPE = 'server1'
    INVALID_SERVER_STATE = 'disable2'
    INVALID_SERVER_HIGHER_KEY = '100000'
    INVALID_SERVER_LOWER_KEY = '-565'
    INVALID_SERVER_TRUSTED = 'server2'
    INVALID_SERVER_VERSION = '5'

    LOG_MSG_UNSET_NTP = "NtpCfg: Set global config: {'authentication': 'disabled', 'dhcp': 'disabled', " \
                        "'server_role': 'disabled', 'src_intf': 'eth0', 'state': 'disabled', 'vrf': 'default'}"
    LOG_MSG_SERVER_CONFIG = "servers: {'10.7.77.134': {'association_type': 'server', 'iburst': 'off', " \
                            "'resolve_as': '10.7.77.134', 'state': 'enabled', 'trusted': 'no', 'version': '4'}}"
    LOG_MSG_SERVER_CONFIG_UPDATE = "servers: {'10.7.77.134': {'association_type': 'server', 'iburst': 'off', " \
                                   "'key': '6', 'resolve_as': '10.7.77.134', 'state': 'disabled', " \
                                   "'trusted': 'yes', 'version': '3'}}"
    LOG_MSG_SERVER_CONFIG_KEY = "NtpCfg: Set keys: {'6': {'trusted': 'yes', 'type': 'SHA1'}}"
#   LOG_MSG_SERVER_CONFIG_VRF = "..."  # Currently not supported

    NTP_DEFAULT_DICT = {
        AUTHENTICATION: Authentication.DISABLED.value,
        DHCP: Dhcp.ENABLED.value,
        LISTEN: Listen.ETH0.value,
        SERVER: {},
        STATE: State.ENABLED.value,
        STATUS: Status.UNSYNCHRONISED.value,
        VRF: Vrf.DEFAULT.value
    }
    NTP_STATUS_DEFAULT_DICT = {}
    SERVER_DEFAULT_VALUES_DICT = {
        AGGRESSIVE_POLLING: AggressivePolling.OFF.value,
        ASSOCIATION_TYPE: AssociationType.SERVER.value,
        RESOLVE_AS: SERVER_FAILED,
        STATE: State.ENABLED.value,
        TRUSTED: Trusted.NO.value,
        VERSION: Version.VERSION_4.value
    }
    SERVER1_DEFAULT_VALUES_DICT = {
        AGGRESSIVE_POLLING: AggressivePolling.OFF.value,
        ASSOCIATION_TYPE: AssociationType.SERVER.value,
        RESOLVE_AS: SERVER1_IPV4,
        STATE: State.ENABLED.value,
        TRUSTED: Trusted.NO.value,
        VERSION: Version.VERSION_4.value
    }
    SERVER2_DEFAULT_VALUES_DICT = {
        AGGRESSIVE_POLLING: AggressivePolling.OFF.value,
        ASSOCIATION_TYPE: AssociationType.SERVER.value,
        RESOLVE_AS: SERVER2_IPV4,
        STATE: State.ENABLED.value,
        TRUSTED: Trusted.NO.value,
        VERSION: Version.VERSION_4.value
    }
    MULTIPLE_SERVERS_DEFAULT_DICT = {
        SERVER1_IPV4: {},
        SERVER2_HOSTNAME: {},
        DUMMY_SERVER1: {},
        DUMMY_SERVER2: {},
        DUMMY_SERVER3: {},
        DUMMY_SERVER4: {},
        DUMMY_SERVER5: {},
        DUMMY_SERVER6: {},
        DUMMY_SERVER7: {},
        DUMMY_SERVER8: {},
    }
    MULTIPLE_SERVERS_CONFIG_DICT = {
        SERVER1_IPV4: SERVER1_DEFAULT_VALUES_DICT,
        SERVER2_HOSTNAME: SERVER2_DEFAULT_VALUES_DICT,
        DUMMY_SERVER1: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER2: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER3: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER4: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER5: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER6: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER7: SERVER_DEFAULT_VALUES_DICT,
        DUMMY_SERVER8: SERVER_DEFAULT_VALUES_DICT,
    }
    SERVER_NONE_DEFAULT_VALUES_DICT = {
        AGGRESSIVE_POLLING: AggressivePolling.ON.value,
        ASSOCIATION_TYPE: AssociationType.SERVER.value,
        KEY: KEY_1,
        RESOLVE_AS: SERVER1_IPV4,
        STATE: State.DISABLED.value,
        TRUSTED: Trusted.YES.value,
        VERSION: Version.VERSION_3.value
    }
    SERVER_DISABLED_DICT = {
        AGGRESSIVE_POLLING: AggressivePolling.OFF.value,
        ASSOCIATION_TYPE: AssociationType.SERVER.value,
        KEY: KEY_1,
        RESOLVE_AS: SERVER1_IPV4,
        STATE: State.DISABLED.value,
        TRUSTED: Trusted.YES.value,
        VERSION: Version.VERSION_3.value
    }
    KEY_DEFAULT_DICT = {}
    KEY_CONFIGURED_DICT = {
        TRUSTED: Trusted.NO.value,
        TYPE: KeyType.MD5.value,
        VALUE: '*'
    }


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


class HealthConsts:
    OK = "OK"
    NOT_OK = "Not OK"
    IGNORED = "Ignored"
    STATUS = "status"
    STATUS_LED = "status-led"
    LED_OK_STATUS = "green"
    LED_NOT_OK_STATUS = "amber"
    MONITOR_LIST = "monitor-list"
    HEALTH_FIRST_FILE = "health_history"
    HEALTH_SECOND_FILE = "health_history.1"
    HEALTH_MONITOR_CONFIG_FILE_PATH = "/usr/share/sonic/device/{}/system_health_monitoring_config.json"
    ISSUES = "issues"
    SUMMARY_REGEX_OK = "INFO {} : Summary: {}".format(NvosConst.DATE_TIME_REGEX, OK)
    SUMMARY_REGEX_NOT_OK = "ERROR {} : Summary: {}".format(NvosConst.DATE_TIME_REGEX, NOT_OK)
    ADD_STATUS_TO_SUMMARY_REGEX = NvosConst.DATE_TIME_REGEX + " : Summary:.*"
    HEALTH_ISSUE_REGEX = "ERROR {time_regex} : {component}: (?:is )?{issue}"
    HEALTH_FIX_REGEX = "INFO {time_regex} : Cleared: {component}: (?:is )?{issue}"
    SYSTEM_LOG_HEALTH_REGEX = '.* Health DB change cache.* new data.*\'summary\': \'{}\''


class OperationTimeConsts:
    OPERATION_COL = 'operation'
    PARAMS_COL = 'params'
    DURATION_COL = 'duration'
    SETUP_COL = 'setup_name'
    VERSION_COL = 'version'
    TYPE_COL = 'machine_type'
    RELEASE_COL = 'release'
    TEST_NAME_COL = 'test_name'
    SESSION_ID_COL = 'session_id'
    DATE_COL = 'date'


class StatsConsts:
    class State(Enum):
        ENABLED = 'enabled'
        DISABLED = 'disabled'

    SLEEP_15_SECONDS = 15  # [sec]
    SLEEP_1_MINUTE = 60  # [sec]
    SLEEP_3_MINUTES = 180  # [sec]
    SLEEP_5_MINUTES = 300  # [sec]
    STATE = 'state'
    STATE_DEFAULT = State.ENABLED.value
    INTERVAL = 'interval'
    INTERVAL_DEFAULT = '5'  # [min]
    INTERVAL_MIN = '1'  # [min]
    HISTORY_DURATION = 'history-duration'
    HISTORY_DURATION_DEFAULT = '365'  # [days]
    HISTORY_DURATION_MIN = '1'  # [days]
    GENERATE_ALL_TIME_MAX = 2  # [sec]
    CATEGORY_STATE_DISABLED = {STATE: State.DISABLED.value}
    CATEGORY_MIN_DICT = {
        STATE: STATE_DEFAULT,
        INTERVAL: INTERVAL_MIN,
        HISTORY_DURATION: HISTORY_DURATION_MIN
    }
    CATEGORY_MIN_DISABLED_DICT = {
        STATE: State.DISABLED.value,
        INTERVAL: INTERVAL_MIN,
        HISTORY_DURATION: HISTORY_DURATION_MIN
    }

    LOG_MSG_UNSET_STATS = "PATCH /nvue_v1/system/stats"
    LOG_MSG_SET_CATEGORY1 = "INFO stats-reportd: got config change "
    LOG_MSG_SET_CATEGORY2 = ": {'enabled': 'true', 'history_duration': '365', 'interval': '1'}"
    LOG_MSG_PATCH_CATEGORY = "PATCH /nvue_v1/system/stats/category/"

    LOG_MSG_ERROR_DB = "..."  # TODO: Update message (parameter not found in redis DB)...

    INVALID_CATEGORY_NAME = 'invalid_category_name'
    ALL_CATEGORIES = 'all'
    INVALID_STATE = 'invalid_state'
    INVALID_INTERVAL_LOW = 0
    INVALID_INTERVAL_HIGH = 1441
    INVALID_HISTORY_DURATION_LOW = 0
    INVALID_HISTORY_DURATION_HIGH = 366
    INVALID_FILE_NAME = 'file_not_exists.csv'
    INVALID_SHOW_CATEGORY = 'The requested item does not exist.'

    TEMP_PATH = '/auto/rdmzsysgwork/shared/test_utilities/tmp/5b5931e6aac04bd39499372ef73fbf31'
    INTERNAL_PATH = "/tmp"
    OLD_SAMPLES_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/old_samples/"
    BIG_FILE_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/big_file/"
    HUGE_FILE_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/huge_file/"
    NO_HEADER_FILE_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/no_header_file/"
    MAX_SIZE_FILE_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/max_size/"
    GENERATED_FILE_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/generated/"
    RESULTS_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/stats/results/"
    INTERNAL_CAT_PATH = "/var/stats"
    TEMP_FOLDER = "/auto/sw_regression/system/NVOS/MARS/results/"
    HEADER_HOSTNAME = "# Hostname:         "
    HEADER_GROUP = "# Statistic group:  "
    HEADER_TIME = "# Started sampling: "
    TIMESTAMP_FORMAT = "%b-%d %Y %H:%M:%S"
    SYSTEM_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    MAX_ROWS_TO_SCAN = 300
    CONST_HEADER_ROWS = 8
    BIG_FILE_NUM_OF_LINES = 600026
    FUN_HEADER_NUM_OF_LINES = 12
    POWER_HEADER_NUM_OF_LINES = 13
    TEMPERATURE_HEADER_NUM_OF_LINES = 11

    TEMP_MIN = 15  # [Celsius]
    TEMP_MAX = 90  # [Celsius]
    MGMT_INT_MIN = 0  # [Bytes/sec]
    MGMT_INT_MAX = 10000  # [Bytes/sec]
    FAN_MIN = 0  # [%]
    FAN_MAX = 100  # [%]
    PWR_PSU_VOLT_MIN = 0  # [V] TODO: Update
    PWR_PSU_VOLT_MAX = 300  # [V] TODO: Update
    PWR_PSU_CUR_MIN = 0  # [A] TODO: Update
    PWR_PSU_CUR_MAX = 100  # [A] TODO: Update
    CPU_FREE_RAM_MIN = 30  # [%]
    CPU_FREE_RAM_MAX = 100  # [%]
    CPU_UTIL_MIN = 0  # [%]
    CPU_UTIL_MAX = 50  # [%]
    CPU_REBOOT_CNT_MIN = 0
    CPU_REBOOT_CNT_MAX = 100
    DISK_FREE_SPACE_MIN = 60  # [%]
    DISK_FREE_SPACE_MAX = 95  # [%]
    DISK_RMN_LIFE_MIN = 70  # [%]
    DISK_RMN_LIFE_MAX = 100  # [%]
    DISK_FAIL_CNT_MIN = 0
    DISK_FAIL_CNT_MAX = 0
    DISK_TOTAL_LBA_RW_MIN = 10000
    DISK_TOTAL_LBA_RW_MAX = 4294967295
    VOLTAGE_GENERAL_MIN = 0
    VOLTAGE_GENERAL_MAX = 16
    VOLTAGE_PSU_MIN = 0
    VOLTAGE_PSU_MAX = 300

    GENERATE = 'generate'
    DELETE = 'delete'
    UPLOAD = 'upload'
    CLEAR = 'clear'


class MultiPlanarConsts:
    INTERNAL_PATH = "/tmp"
    SIMULATION_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/xdr/simulation/"
    ORIGIN_FILES_PATH = "/auto/sw_system_project/NVOS_INFRA/verification/xdr/origin/"
    SIMULATION_FILE = "platform.json"
    PLATFORM_PATH = "/usr/share/sonic/device/x86_64-mlnx_mqm9700-r0/"
    MULTI_PLANAR_KEYS = ['asic', 'parent-alias', 'parent-port', 'plane']

    PHYSICAL_STATE_PARAM = 'SAI_PORT_STAT_INFINIBAND_PHYSICAL_STATE'
    PHYSICAL_DISABLED = '0'  # disabled
    PHYSICAL_SLEEP = '1'  # sleep
    PHYSICAL_POLLING = '2'  # polling
    PHYSICAL_LINKUP = '3'  # linkup
    LOGICAL_STATE_PARAM = 'SAI_PORT_STAT_INFINIBAND_LOGICAL_STATE'
    LOGICAL_DOWN = '0'  # down
    LOGICAL_INIT = '1'  # init
    LOGICAL_ARMED = '2'  # armed
    LOGICAL_ACTIVE = '3'  # active
    SYNC_TIME = 5  # [sec]
    PHYSICAL_STATE_AGG_TABLE = [{"p1": 'PHYSICAL_DISABLED', "p2": 'PHYSICAL_DISABLED', "exp": 'PHYSICAL_DISABLED'},
                                {"p1": 'PHYSICAL_DISABLED', "p2": 'PHYSICAL_SLEEP', "exp": 'PHYSICAL_DISABLED'},
                                {"p1": 'PHYSICAL_DISABLED', "p2": 'PHYSICAL_POLLING', "exp": 'PHYSICAL_DISABLED'},
                                {"p1": 'PHYSICAL_DISABLED', "p2": 'PHYSICAL_LINKUP', "exp": 'PHYSICAL_DISABLED'},
                                {"p1": 'PHYSICAL_SLEEP', "p2": 'PHYSICAL_SLEEP', "exp": 'PHYSICAL_SLEEP'},
                                {"p1": 'PHYSICAL_SLEEP', "p2": 'PHYSICAL_POLLING', "exp": 'PHYSICAL_SLEEP'},
                                {"p1": 'PHYSICAL_SLEEP', "p2": 'PHYSICAL_LINKUP', "exp": 'PHYSICAL_SLEEP'},
                                {"p1": 'PHYSICAL_POLLING', "p2": 'PHYSICAL_POLLING', "exp": 'PHYSICAL_POLLING'},
                                {"p1": 'PHYSICAL_POLLING', "p2": 'PHYSICAL_LINKUP', "exp": 'PHYSICAL_POLLING'},
                                {"p1": 'PHYSICAL_LINKUP', "p2": 'PHYSICAL_LINKUP', "exp": 'PHYSICAL_LINKUP'}]
    LOGICAL_STATE_AGG_TABLE = [{"p1": 'LOGICAL_DOWN', "p2": 'LOGICAL_DOWN', "exp": 'LOGICAL_DOWN'},
                               {"p1": 'LOGICAL_DOWN', "p2": 'LOGICAL_INIT', "exp": 'LOGICAL_DOWN'},
                               {"p1": 'LOGICAL_DOWN', "p2": 'LOGICAL_ARMED', "exp": 'LOGICAL_DOWN'},
                               {"p1": 'LOGICAL_DOWN', "p2": 'LOGICAL_ACTIVE', "exp": 'LOGICAL_DOWN'},
                               {"p1": 'LOGICAL_INIT', "p2": 'LOGICAL_INIT', "exp": 'LOGICAL_INIT'},
                               {"p1": 'LOGICAL_INIT', "p2": 'LOGICAL_ARMED', "exp": 'LOGICAL_INIT'},
                               {"p1": 'LOGICAL_INIT', "p2": 'LOGICAL_ACTIVE', "exp": 'LOGICAL_INIT'},
                               {"p1": 'LOGICAL_ARMED', "p2": 'LOGICAL_ARMED', "exp": 'LOGICAL_ARMED'},
                               {"p1": 'LOGICAL_ARMED', "p2": 'LOGICAL_ACTIVE', "exp": 'LOGICAL_ARMED'},
                               {"p1": 'LOGICAL_ACTIVE', "p2": 'LOGICAL_ACTIVE', "exp": 'LOGICAL_ACTIVE'}]
    CONFIG_MANAGER_SERVICE = 'configmgrd'
    SERVICE_RECOVERY_MAX_TIME = 60  # [sec] TODO: update to accurate value
    NON_AGGREGATED_PORT_CONFIG_TIME = 2.5  # [sec] TODO: - update time measured in Gorilla.
    DATABASE_TABLES = ['APPL_DB', 'ASIC_DB', 'COUNTERS_DB', 'COUNTERS_DB_1',
                       'COUNTERS_DB_2', 'CONFIG_DB', 'STATE_DB', 'FLEX_COUNTER_DB']
    LOG_MSG_UNSET_FAE_INTERFACE = "PATCH..."  # TODO: complete
    LOG_MSG_SET_FAE_INTERFACE = "PATCH..."  # TODO: complete
    LOG_MSG_ACTION_CLEAR_FAE_INTERFACE = "PATCH..."  # TODO: complete


class FastRecoveryConsts:
    STATE = 'state'
    STATE_ENABLED = 'enabled'
    STATE_DISABLED = 'disabled'
    STATE_DEFAULT = 'enabled'
    TRIGGER = 'trigger'
    TRIGGER_EVENT = 'event'
    TRIGGER_CREDIT_WATCHDOG = 'credit-watchdog'
    TRIGGER_EFFECTIVE_BER = 'effective-ber'
    TRIGGER_RAW_BER = 'raw-ber'
    TRIGGER_SYMBOL_BER = 'symbol-ber'
    TRIGGERS = [TRIGGER_CREDIT_WATCHDOG, TRIGGER_EFFECTIVE_BER, TRIGGER_RAW_BER, TRIGGER_SYMBOL_BER]
    SEVERITY_DEFAULT = 'error'
    SEVERITY_WARNING = 'warning'
