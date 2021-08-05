class PytestConst:
    run_config_only_arg = '--run_config_only'
    run_test_only_arg = '--run_test_only'
    run_cleanup_only_arg = '--run_cleanup_only'
    alluredir_arg = '--alluredir'
    disable_loganalyzer = '--disable_loganalyzer'


class SonicConst:
    FEC_RS_MODE = 'rs'
    FEC_FC_MODE = 'fc'
    FEC_NONE_MODE = 'none'
    DOCKERS_LIST = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']

    CPU_RAM_CHECK_PROCESS_LIST = ['sx_sdk', 'syncd', 'redis-server', 'snmpd', 'zebra', 'bgpd', 'bgpcfgd', 'bgpmon',
                                  'fpmsyncd', 'orchagent', 'ntpd', 'neighsyncd', 'vlanmgrd', 'intfmgrd', 'portmgrd',
                                  'buffermgrd', 'vrfmgrd', 'nbrmgrd', 'vxlanmgrd', 'sensord']

    SONIC_CONFIG_FOLDER = '/etc/sonic/'
    PORT_CONFIG_INI = 'port_config.ini'
    CONFIG_DB_JSON = 'config_db.json'
    EXTENDED_CONFIG_DB_PATH = "extended_config_db.json"
    CONFIG_DB_JSON_PATH = SONIC_CONFIG_FOLDER + CONFIG_DB_JSON
    PLATFORM_JSON_PATH = "/usr/share/sonic/device/{PLATFORM}/platform.json"

    BREAKOUT_MODE_WITH_DIFF_LANE_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G\(\d\)\+\dx\d+G\(\d\)"  # i.e, 2x25G(2)+1x50G(2)

    BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G\[[\d+G,]+\]"  # 1x100G[50G,25G,1G]
    BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G"  # 2x50G

    BREAKOUT_MODES_REGEX = "{}|{}|{}".format(BREAKOUT_MODE_WITH_DIFF_LANE_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX)

    MINIGRAPH_XML = 'minigraph.xml'
    MINIGRAPH_XML_PATH = SONIC_CONFIG_FOLDER + MINIGRAPH_XML


class InfraConst:
    HTTP_SERVER = 'http://fit69'
    MARS_TOPO_FOLDER_PATH = '/auto/sw_regression/system/SONIC/MARS/conf/topo/'
    REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'
    METADATA_PATH = "/.autodirect/sw_regression/system/SONIC/MARS/metadata/"

    MYSQL_SERVER = '10.208.1.11'
    MYSQL_USER = 'sonic'
    MYSQL_PASSWORD = 'sonic11'
    MYSQL_DB = 'sonic'
    RC_SUCCESS = 0
    NGTS_PATH_PYTEST = '/ngts_venv/bin/pytest'
    SLEEP_BEFORE_RRBOOT = 5
    SLEEP_AFTER_RRBOOT = 35
    IP = 'ip'
    MASK = 'mask'

    ALLURE_SERVER_IP = '10.215.11.120'
    ALLURE_SERVER_PORT = '5050'
    ALLURE_SERVER_URL = 'http://{}:{}'.format(ALLURE_SERVER_IP, ALLURE_SERVER_PORT)
    ALLURE_REPORT_DIR = '/tmp/allure-results'


class LinuxConsts:
    CONF_FEC = "Configured FEC encodings"
    ACTIVE_FEC = "Active FEC encoding"
    FEC_AUTO_MODE = 'auto'
    error_exit_code = 1
    linux = 'linux'


class TopologyConsts:
    engine = 'engine'
    players = 'players'
    ports = 'ports'
    interconnects = 'interconnects'
    ports_names = 'ports_names'


class ConfigDbJsonConst:
    PORT = 'PORT'
    ALIAS = 'alias'
    FEATURE = 'FEATURE'
    LLDP = 'lldp'
    STATUS = 'status'
    ENABLED = 'enabled'
    DEVICE_METADATA = "DEVICE_METADATA"
    MGMT_INTERFACE = "MGMT_INTERFACE"
    MGMT_INTERFACE_VALUE = '''{"eth0|%s/%s": {"gwaddr": "%s"}}'''
    LOCALHOST = "localhost"
    TYPE = 'type'
    TOR_ROUTER = 'ToRRouter'
    HOSTNAME = "hostname"
    MAC = "mac"
    HWSKU = "hwsku"


class IpIfaceAddrConst:
    IPV4_ADDR_MASK_KEY = 'IPv4 address/mask'
    IPV6_ADDR_MASK_KEY = 'IPv6 address/mask'


class AutonegCommandConstants:
    INTERFACE = "Interface"
    AUTONEG_MODE = "Auto-Neg Mode"
    SPEED = "Speed"
    ADV_SPEED = "Adv Speeds"
    TYPE = "Type"
    ADV_TYPES = "Adv Types"
    OPER = "Oper"
    ADMIN = "Admin"
    FEC = "FEC"
    WIDTH = "Width"
    REGEX_PARSE_EXPRESSION_FOR_MLXLINK = {
        ADMIN: ("State\s*:\s*(\w*)", "Active", "up", "down"),
        OPER: ("Physical state\s*:\s*(.*)", "LinkUp|ENABLE", "up", "down"),
        SPEED: ("Speed\s*:\s*(\d+G)", None, None, None),
        WIDTH: ("Width\s*:\s*(\d+)x", None, None, None),
        FEC: ("FEC\s*:\s*(.*)", "No FEC", "none", None),
        AUTONEG_MODE: ("Auto Negotiation\s*:\s*(\w*)", "ON", "enabled", "disabled")
    }


SPC = {
    '25GBASE-CR': ['10G', '25G'],
    '50GBASE-CR2': ['50G'],
    '40GBASE-CR4': ['40G'],
    '100GBASE-CR4': ['100G'],
    'SR': ['10G', '25G'],
    'SR2': ['50G'],
    'SR4': ['40G', '100G'],
    'LR': ['10G'],
    'LR4': ['40G', '100G'],
    'KR': ['10G', '25G'],
    'KR2': ['20G', '50G'],
    'KR4': ['40G', '56G', '100G'],
    'CAUI': ['100G'],
    'GMII': ['1G'],
    'SFI': ['10G'],
    'XLAUI': ['40G'],
    'CAUI4': ['100G'],
    'XAUI': ['10G'],
    'XFI': ['10G']
}
SPC2_3 = {
    '1000BASE-CX': ['1G'],
    '25GBASE-CR': ['1G', '10G', '25G'],
    '50GBASE-CR': ['50G'],
    '50GBASE-CR2': ['50G'],
    '40GBASE-CR4': ['40G'],
    '100GBASE-CR2': ['100G'],
    '100GBASE-CR4': ['100G'],
    '200GBASE-CR4': ['200G'],
    '400GBASE-CR8': ['400G'],
    'CR': ['1G', '10G', '25G', '50G'],
    'CR2': ['50G', '100G'],
    'CR4': ['40G', '100G', '200G', '400G'],
    'SR': ['1G', '10G', '25G', '50G'],
    'SR2': ['50G', '100G'],
    'SR4': ['40G', '100G', '200G', '400G'],
    'LR': ['1G', '10G', '25G', '50G'],
    'LR4': ['40G', '100G', '200G', '400G'],
    'KR': ['1G', '10G', '25G', '50G'],
    'KR2': ['50G', '100G'],
    'KR4': ['40G', '100G', '200G', '400G'],
    'CAUI': ['100G'],
    'GMII': ['1G'],
    'SFI': ['10G'],
    'XLAUI': ['40G'],
    'CAUI4': ['100G'],
    'XFI': ['10G']
}


class PlatformConstants:
    ANACONDA = "SN3700"
    TIGRIS = "SN3800"
    LIGER = "SN4600"
    LEOPARD = "SN4700"


class FecConstants:
    PORT_SPLIT_NUM_1 = 1
    PORT_SPLIT_NUM_2 = 2
    PORT_SPLIT_NUM_4 = 4

    FEC_MODES_SPC_SPEED_SUPPORT = {
        SonicConst.FEC_FC_MODE: {
            PORT_SPLIT_NUM_1: {'10G': ['CR'],
                               '25G': ['CR'],
                               '40G': ['CR4'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_2: {'10G': ['CR'],
                               '25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_4: {'10G': ['CR'],
                               '25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               }
        },
        SonicConst.FEC_RS_MODE: {
            PORT_SPLIT_NUM_1: {'25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_2: {'25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_4: {'25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
        },
        SonicConst.FEC_NONE_MODE: {
            PORT_SPLIT_NUM_1: {'10G': ['CR'],
                               '25G': ['CR'],
                               '40G': ['CR4'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_2: {'10G': ['CR'],
                               '25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               },
            PORT_SPLIT_NUM_4: {'10G': ['CR'],
                               '25G': ['CR'],
                               '50G': ['CR2'],
                               '100G': ['CR4']
                               }
        }
    }
    FEC_MODES_SPC2_SPEED_SUPPORT = {
        PlatformConstants.ANACONDA: {
            SonicConst.FEC_FC_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   }
            },
            SonicConst.FEC_RS_MODE: {
                PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4'],
                                   '200G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                   '50G': ['CR'],
                                   },
            },
            SonicConst.FEC_NONE_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR']
                                   }
            }
        },
        PlatformConstants.TIGRIS: {
            SonicConst.FEC_FC_MODE: {
                PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {
                    '25G': ['CR'],
                    '50G': ['CR2']
                }
            },
            SonicConst.FEC_RS_MODE: {
                PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   },
                PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                   '50G': ['CR'],
                                   },
            },
            SonicConst.FEC_NONE_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'1G': ['CR'],
                                   '10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR']
                                   }
            }
        }
    }
    FEC_MODES_SPC3_SPEED_SUPPORT = {
        PlatformConstants.LIGER: {
            SonicConst.FEC_FC_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   }
            },
            SonicConst.FEC_RS_MODE: {
                PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4'],
                                   },
                PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   },
                PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                   },
            },
            SonicConst.FEC_NONE_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'1G': ['CR'],
                                   '10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR']
                                   }
            }
        },
        PlatformConstants.LEOPARD: {
            SonicConst.FEC_FC_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   }
            },
            SonicConst.FEC_RS_MODE: {
                PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4'],
                                   '200G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                   '50G': ['CR2'],
                                   '100G': ['CR2'],
                                   '200G': ['CR4']
                                   },
                PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                   '50G': ['CR'],
                                   '100G': ['CR2']
                                   },
            },
            SonicConst.FEC_NONE_MODE: {
                PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2'],
                                   '100G': ['CR4']
                                   },
                PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '40G': ['CR4'],
                                   '50G': ['CR2']
                                   },
                PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                   '25G': ['CR'],
                                   '50G': ['CR2']
                                   }
            }
        }
    }


FEC_MODES_TO_ETHTOOL = {
    SonicConst.FEC_FC_MODE: "baser",
    SonicConst.FEC_RS_MODE: SonicConst.FEC_RS_MODE,
    SonicConst.FEC_NONE_MODE: "off",
    LinuxConsts.FEC_AUTO_MODE: LinuxConsts.FEC_AUTO_MODE
}


class P4SamplingEntryConsts:
    ENTRY_PRIORITY_HEADERS = ['PRIO']
    COUNTER_PACKETS_HEADERS = ['Packets']
    COUNTER_BYTES_HEADERS = ['Bytes']
    FLOW_ENTRY_KEY_HEADERS = ['Key SIP', 'Key DIP', 'Key PROTO', 'Key L4 SPORT', 'Key L4 DPORT',
                              'Key Checksum Value/Mask']
    PORT_ENTRY_KEY_HEADERS = ['Key Port', 'Key Checksum Value/Mask']
    FLOW_ENTRY_ACTION_HEADERS = [
        'Action',
        'Action Mirror Port',
        'Action SMAC',
        'Action DMAC',
        'Action SIP',
        'Action DIP',
        'Action VLAN',
        'Action Is Trunc',
        'Action Trunc Size']

    PORT_ENTRY_ACTION_HEADERS = [
        'Action',
        'Action Mirror Port',
        'Action SMAC',
        'Action DMAC',
        'Action SIP',
        'Action DIP',
        'Action VLAN',
        'Action Is Trunc',
        'Action Trunc Size']
    dutha1_ip = '10.0.0.1'
    duthb1_ip = '50.0.0.1'
    dutha2_ip = '10.0.1.1'
    duthb2_ip = '50.0.1.1'

    hadut1_ip = "10.0.0.2"
    hbdut1_ip = "50.0.0.2"
    hadut2_ip = '10.0.1.2'
    hbdut2_ip = '50.0.1.2'

    hadut1_network = "10.0.0.0"
    hbdut1_network = "50.0.0.0"
    hadut2_network = '10.0.0.0'
    hbdut2_network = '50.0.1.0'


class P4SamplingConsts:
    APP_NAME = 'p4-sampling'
    REPOSITORY = 'urm.nvidia.com/sw-nbu-sws-sonic-docker/p4-sampling'
    VERSION = '0.1.0'
    UPGRADE_TARGET_VERSION = '0.2.0-004'
    CONTTROL_IN_PORT = 'control-in-port'
    PORT_TABLE_NAME = 'table-port-sampling'
    FLOW_TABLE_NAME = 'table-flow-sampling'
    ACTION_NAME = 'DoMirror'
    TRAFFIC_INTERVAL = 0.2


class LoganalyzerConsts:
    LOG_FILE_NAME = "syslog"


class AppExtensionInstallationConstants:
    WJH_APP_NAME = 'what-just-happened'
    WJH_REPOSITORY = 'harbor.mellanox.com/sonic-wjh/docker-wjh'
    LC_MANAGER = 'line-card-manager'
    LC_MANAGER_REPOSITORY = 'harbor.mellanox.com/sonic-lc-manager/line-card-manager'
    CMD_GET_SDK_VERSION = "docker exec -i {} bash -c 'sx_sdk --version'"
    SYNCD_DOCKER = 'syncd'
    APPLICATION_LIST = [
        P4SamplingConsts.APP_NAME,
        WJH_APP_NAME,
        LC_MANAGER
    ]
