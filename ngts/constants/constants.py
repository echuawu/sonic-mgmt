import copy


class PytestConst:
    run_config_only_arg = '--run_config_only'
    run_test_only_arg = '--run_test_only'
    run_cleanup_only_arg = '--run_cleanup_only'
    alluredir_arg = '--alluredir'
    disable_loganalyzer = '--disable_loganalyzer'


class SonicConst:
    PORT_SPLIT_NUM_1 = 1
    PORT_SPLIT_NUM_2 = 2
    PORT_SPLIT_NUM_4 = 4
    PORT_LANE_NUM_1 = 1
    PORT_LANE_NUM_2 = 2
    PORT_LANE_NUM_4 = 4
    FEC_RS_MODE = 'rs'
    FEC_FC_MODE = 'fc'
    FEC_NONE_MODE = 'none'
    DOCKERS_LIST = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']
    DOCKERS_LIST_TOR = DOCKERS_LIST
    DOCKERS_LIST_LEAF = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp']

    CPU_RAM_CHECK_PROCESS_LIST = ['sx_sdk', 'syncd', 'redis-server', 'snmpd', 'zebra', 'bgpd', 'bgpcfgd', 'bgpmon',
                                  'fpmsyncd', 'orchagent', 'ntpd', 'neighsyncd', 'vlanmgrd', 'intfmgrd', 'portmgrd',
                                  'buffermgrd', 'vrfmgrd', 'nbrmgrd', 'vxlanmgrd', 'sensord']

    SONIC_CONFIG_FOLDER = '/etc/sonic/'
    PORT_CONFIG_INI = 'port_config.ini'
    CONFIG_DB_JSON = 'config_db.json'
    EXTENDED_CONFIG_DB_PATH = "extended_config_db.json"
    CONFIG_DB_JSON_PATH = SONIC_CONFIG_FOLDER + CONFIG_DB_JSON
    PLATFORM_JSON_PATH = "/usr/share/sonic/device/{PLATFORM}/platform.json"
    COPP_CONFIG = 'copp_cfg.json'

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
    HTTTP_SERVER_FIT16 = 'http://r-fit16-clone.mtr.labs.mlnx'
    MARS_TOPO_FOLDER_PATH = '/auto/sw_regression/system/SONIC/MARS/conf/topo/'
    REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'
    METADATA_PATH = "/.autodirect/sw_regression/system/SONIC/MARS/metadata/"
    HTTP_SERVER_MARS_TOPO_FOLDER_PATH = '{}{}'.format(HTTP_SERVER, MARS_TOPO_FOLDER_PATH)

    MYSQL_SERVER = '10.208.1.11'
    MYSQL_USER = 'sonic'
    MYSQL_PASSWORD = 'sonic11'
    MYSQL_DB = 'sonic'
    RC_SUCCESS = 0
    NGTS_PATH_PYTEST = '/ngts_venv/bin/pytest'
    SLEEP_BEFORE_RRBOOT = 5
    SLEEP_AFTER_RRBOOT = 35
    SLEEP_AFTER_WJH_INSTALLATION = 100
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
    MGMT_PORT = "MGMT_PORT"
    MGMT_PORT_VALUE = '''{"eth0":{"admin_status": "up", "alias": "eth0"}}'''
    LOCALHOST = "localhost"
    TYPE = 'type'
    TOR_ROUTER = 'ToRRouter'
    HOSTNAME = "hostname"
    MAC = "mac"
    HWSKU = "hwsku"
    ADMIN_STATUS = "admin_status"


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
        ADMIN: (r"State\s*:\s*(\w*)", "Active", "up", "down"),
        OPER: (r"Physical state\s*:\s*(.*)", "LinkUp|ENABLE", "up", "down"),
        SPEED: (r"Speed\s*:\s*(?:BaseT)?(\d*M|\d*G)", None, None, None),
        WIDTH: (r"Width\s*:\s*(\d+)x", None, None, None),
        FEC: (r"FEC\s*:\s*(.*)", "No FEC", "none", None),
        AUTONEG_MODE: (r"Auto Negotiation\s*:\s*(\w*)", "ON", "enabled", "disabled")
    }


class DefaultCredentialConstants:
    OTHER_SONIC_USER = "admin"
    OTHER_SONIC_PASSWORD_LIST = ["password"]


class PlatformTypesConstants:
    FILTERED_PLATFORM_ALLIGATOR = 'SN2201'
    FILTERED_PLATFORM_ANACONDA = "MSN3700"
    FILTERED_PLATFORM_ANACONDA_C = "MSN3700C"
    FILTERED_PLATFORM_LIONFISH = "MSN3420"
    FILTERED_PLATFORM_TIGRIS = "MSN3800"
    FILTERED_PLATFORM_LIGER = "MSN4600"
    FILTERED_PLATFORM_LEOPARD = "MSN4700"
    FILTERED_PLATFORM_TIGON = "MSN4600C"
    FILTERED_PLATFORM_OCELOT = "MSN4410"

    PLATFORM_ALLIGATOR = 'x86_64-nvidia_sn2201-r0'
    PLATFORM_ANACONDA = 'x86_64-mlnx_msn3700-r0'
    PLATFORM_ANACONDA_C = 'x86_64-mlnx_msn3700c-r0'
    PLATFORM_BOXER = 'x86_64-mlnx_msn2010-r0'
    PLATFORM_LEOPARD = 'x86_64-mlnx_msn4700-r0'
    PLATFORM_LIGER = 'x86_64-mlnx_msn4600-r0'
    PLATFORM_LIONFISH = 'x86_64-mlnx_msn3420-r0'
    PLATFORM_OCELOT = 'x86_64-mlnx_msn4410-r0'
    PLATFORM_PANTHER = 'x86_64-mlnx_msn2700-r0'
    PLATFORM_SPIDER = 'x86_64-mlnx_msn2410-r0'
    PLATFORM_TIGON = 'x86_64-mlnx_msn4600c-r0'
    PLATFORM_TIGRIS = 'x86_64-mlnx_msn3800-r0'


class InterfacesTypeConstants:
    INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC = {
        PlatformTypesConstants.FILTERED_PLATFORM_ALLIGATOR: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['100M', '1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']}
        },
        'default': {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']},
        }
    }
    INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC2 = {
        PlatformTypesConstants.FILTERED_PLATFORM_LIONFISH: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA_C: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_TIGRIS: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G', '50G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G', '100G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G', '200G']}
        }
    }
    INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC3 = {
        PlatformTypesConstants.FILTERED_PLATFORM_OCELOT: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G', '50G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G', '100G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G', '200G', '400G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_LEOPARD: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G', '50G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G', '100G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G', '200G', '400G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_LIGER: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G', '50G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G', '100G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G', '200G']}
        },
        PlatformTypesConstants.FILTERED_PLATFORM_TIGON: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['1G', '10G', '25G']},
            SonicConst.PORT_LANE_NUM_2: {'CR2': ['50G']},
            SonicConst.PORT_LANE_NUM_4: {'CR4': ['40G', '100G']}
        }

    }


class FecConstants:
    FEC_MODES_SPC_SPEED_SUPPORT = {
        SonicConst.FEC_FC_MODE: {
            SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '40G': ['CR4'],
                                          '50G': ['CR2']
                                          },
            SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '50G': ['CR2']
                                          },
            SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '50G': ['CR2']
                                          }
        },
        SonicConst.FEC_RS_MODE: {
            SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          },
            SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          },
            SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          },
        },
        SonicConst.FEC_NONE_MODE: {
            SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '40G': ['CR4'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          },
            SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          },
            SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                          '25G': ['CR'],
                                          '50G': ['CR2'],
                                          '100G': ['CR4']
                                          }
        }
    }
    FEC_MODES_SPC2_SPEED_SUPPORT = {
        PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA_C: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                              '25G': ['CR']
                                              }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4'],
                                              '200G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR'],
                                              },
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                              '25G': ['CR']
                                              }
            }
        },
        PlatformTypesConstants.FILTERED_PLATFORM_TIGRIS: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {
                    '25G': ['CR'],
                    '50G': ['CR2']
                }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR'],
                                              },
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'1G': ['CR'],
                                              '10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR']
                                              }
            }
        }
    }

    FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA] = \
        copy.deepcopy(FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA_C])
    FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA][SonicConst.FEC_RS_MODE][SonicConst.PORT_SPLIT_NUM_1]['100G'] = ['CR2']
    FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA][SonicConst.FEC_RS_MODE][SonicConst.PORT_SPLIT_NUM_2]['50G'] = ['CR']

    FEC_MODES_SPC3_SPEED_SUPPORT = {
        PlatformTypesConstants.FILTERED_PLATFORM_LIGER: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4'],
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              },
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'1G': ['CR'],
                                              '10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR']
                                              }
            }
        },
        PlatformTypesConstants.FILTERED_PLATFORM_LEOPARD: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '50G': ['CR2']
                                              }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4'],
                                              '200G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR2'],
                                              '200G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR'],
                                              '100G': ['CR2']
                                              },
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'10G': ['CR'],
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
    VERSION = '0.2.0-012'
    UPGRADE_TARGET_VERSION = '0.2.0-19'
    CONTTROL_IN_PORT = 'control_in_port'
    PORT_TABLE_NAME = 'table_port_sampling'
    FLOW_TABLE_NAME = 'table_flow_sampling'
    ACTION_NAME = 'DoMirror'
    TRAFFIC_INTERVAL = 0.2
    COUNTER_REFRESH_INTERVAL = 10


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
    APP_EXTENSION_PROJECT_MAPPING = {'sonic-wjh': WJH_APP_NAME,
                                     'p4-sampling': P4SamplingConsts.APP_NAME,
                                     'sonic-lc-manager': LC_MANAGER}
    APPS_WHERE_SX_SDK_NOT_PRESENT = [P4SamplingConsts.APP_NAME]
