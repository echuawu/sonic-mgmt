
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

    DOCKERS_LIST = ['nvue', 'pmon', 'syncd-ibv0', 'swss-ibv0', 'database']
    PORT_STATUS_LABEL = 'admin_status'
    PORT_CONFIG_DB_TABLES_PREFIX = "IB_PORT"


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
    ACTIONS_GENERATE_SINCE = '--since'


class ActionConsts:
    CLEANUP = "cleanup"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    BOOT_NEXT = "boot-next"


class IpConsts:
    MIN_IPV6_GROUP_VALUE = 0
    MAX_IPV6_GROUP_VALUE = 65535
