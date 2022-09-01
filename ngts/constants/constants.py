import copy


class PytestConst:
    run_config_only_arg = '--run_config_only'
    run_test_only_arg = '--run_test_only'
    run_cleanup_only_arg = '--run_cleanup_only'
    alluredir_arg = '--alluredir'
    disable_loganalyzer = '--disable_loganalyzer'
    disable_export_mars_cases_result = '--disable_exporting_results_to_mars_db'
    CUSTOM_SKIP_IF_DICT = 'custom_skip_if_dict'
    CUSTOM_TEST_SKIP_PLATFORM_TYPE = 'dynamic_tests_skip_platform_type'
    CUSTOM_TEST_SKIP_BRANCH_NAME = 'dynamic_tests_skip_branch_name'
    LA_DYNAMIC_IGNORES_LIST = 'LA_DYNAMIC_IGNORES_LIST'
    GET_DUMP_AT_TEST_FALIURE = "GET_DUMP"


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
    DOCKERS_LIST_BF = ['swss', 'syncd', 'bgp', 'pmon', 'lldp']
    DOCKERS_LIST_TOR = DOCKERS_LIST
    DOCKERS_LIST_LEAF = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp']
    DAEMONS_DICT = {'swss': [], 'syncd': [], 'bgp': [],
                    'teamd': [], 'pmon': [], 'lldp': [], 'dhcp_relay': []}
    DAEMONS_DICT_BF = {'swss': [],
                       'syncd': [],
                       'bgp': [],
                       'pmon': ['pcied', 'rsyslogd', 'supervisor-proc-exit-listener', 'syseepromd', 'thermalctld', 'xcvrd'],
                       'lldp': []}

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

    BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"(\dx\d+G\[[\d+G,]+\]|\dx\d+\[[\d,]+\])"  # 1x100G[50G,25G,1G]
    BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G"  # 2x50G

    BREAKOUT_MODES_REGEX = "{}|{}|{}".format(BREAKOUT_MODE_WITH_DIFF_LANE_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX)

    MINIGRAPH_XML = 'minigraph.xml'
    MINIGRAPH_XML_PATH = SONIC_CONFIG_FOLDER + MINIGRAPH_XML
    SANITIZER_FOLDER_PATH = "/var/log/asan"


class CliType:
    NVUE = 'NVUE'
    SONIC = 'Sonic'
    SHELL = 'SHELL'
    MLNX_OS = 'MLNX_OS'


class DbConstants:
    METADATA_PATH = "/.autodirect/sw_regression/system/SONIC/MARS/metadata/"
    METADATA_PATH_NVOS = "/auto/sw_system_project/MLNX_OS_INFRA/NVOS-SONIC/MARS/metadata/"

    CLI_TYPE_PATH_MAPPING = {CliType.SONIC: METADATA_PATH,
                             CliType.NVUE: METADATA_PATH_NVOS,
                             CliType.SHELL: METADATA_PATH,
                             CliType.MLNX_OS: METADATA_PATH_NVOS}
    CREDENTIALS = {CliType.SONIC: {'server': 'mtlsqlprd', 'database': 'sonic_mars',
                                   'username': 'sonic_db_user', 'password': 'Pa$$word01'},
                   CliType.NVUE: {'server': "mtlsqlprd", 'database': "NVOS", 'username': 'NVOS_ADMIN',
                                  'password': "Nvos1234$$"}}


class InfraConst:
    HTTP_SERVER = 'http://fit69'
    HTTTP_SERVER_FIT16 = 'http://r-fit16-clone.mtr.labs.mlnx'
    MARS_TOPO_FOLDER_PATH = '/auto/sw_regression/system/SONIC/MARS/conf/topo/'
    NVOS_REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/NVOS/MARS/results'
    REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'
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
    STATE = 'state'
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
    DOCKER_ROUTING_CONFIG_MODE = "docker_routing_config_mode"
    SPLIT = "split"


class IpIfaceAddrConst:
    IPV4_ADDR_MASK_KEY = 'IPv4 address/mask'
    IPV6_ADDR_MASK_KEY = 'IPv6 address/mask'
    IPV4_MASK_24 = '24'


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
        SPEED: (r"Speed\s*:\s*(?:BaseT|BaseTx)?(\d*M|\d*G)", None, None, None),
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
    FILTERED_PLATFORM_MOOSE = "SN5600"

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
    PLATFORM_MOOSE = 'x86_64-nvidia_sn5600_simx-r0'


class InterfacesTypeConstants:
    RJ45 = 'RJ45'

    INTERFACE_TYPE_SUPPORTED_SPEEDS_SPC = {
        PlatformTypesConstants.FILTERED_PLATFORM_ALLIGATOR: {
            SonicConst.PORT_LANE_NUM_1: {'CR': ['10M', '100M', '1000M', '1G', '10G', '25G']},
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
        PlatformTypesConstants.FILTERED_PLATFORM_LIONFISH: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR']
                                              }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR']
                                              }
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'1G': ['CR'],
                                              '10G': ['CR'],
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
        PlatformTypesConstants.FILTERED_PLATFORM_ANACONDA_C: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              },
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

    FEC_MODES_SPC3_SPEED_SUPPORT = {
        PlatformTypesConstants.FILTERED_PLATFORM_LEOPARD: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              }
            },
            SonicConst.FEC_RS_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR'],
                                              '100G': ['CR2'],
                                              '200G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR'],
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
        },
        PlatformTypesConstants.FILTERED_PLATFORM_OCELOT: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR']
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
                                              '50G': ['CR2']
                                              }
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'1G': ['CR'],
                                              '10G': ['CR'],
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


        PlatformTypesConstants.FILTERED_PLATFORM_LIGER:
            FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_LIONFISH],
        PlatformTypesConstants.FILTERED_PLATFORM_TIGON:
            FEC_MODES_SPC2_SPEED_SUPPORT[PlatformTypesConstants.FILTERED_PLATFORM_LIONFISH]
    }

    FEC_MODES_SPC4_SPEED_SUPPORT = {
        PlatformTypesConstants.FILTERED_PLATFORM_MOOSE: {
            SonicConst.FEC_FC_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {
                    '25G': ['CR'],
                    '50G': ['CR2']
                },
                SonicConst.PORT_SPLIT_NUM_2: {
                    '25G': ['CR'],
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
                                              '100G': ['CR'],
                                              '200G': ['CR4'],
                                              '400G': ['CR4'],
                                              '800G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR'],
                                              '200G': ['CR4'],
                                              '400G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'25G': ['CR'],
                                              '50G': ['CR2'],
                                              '100G': ['CR'],
                                              '200G': ['CR2'],
                                              },
            },
            SonicConst.FEC_NONE_MODE: {
                SonicConst.PORT_SPLIT_NUM_1: {'1G': ['CR'],
                                              '10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_2: {'1G': ['CR'],
                                              '10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
                                              '50G': ['CR2'],
                                              '100G': ['CR4']
                                              },
                SonicConst.PORT_SPLIT_NUM_4: {'1G': ['CR'],
                                              '10G': ['CR'],
                                              '25G': ['CR'],
                                              '40G': ['CR4'],
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


class P4ExamplesConsts:
    REPO_NAME = "urm.nvidia.com/sw-nbu-sws-sonic-docker/p4-examples"
    APP_NAME = 'p4-examples'
    APP_VERSION = '0.5.0'
    NO_EXAMPLE = "NO_EXAMPLE"
    VXLAN_BM_FEATURE_NAME = "VXLAN_BM"
    VXLAN_BM_ENCAP_TABLE = "p4-vxlan-bm-overlay-router"
    VXLAN_BM_DECAP_TABLE = "p4-vxlan-bm-tenant-forward"
    GTP_PARSER_TABLE = "p4-gtp"
    GTP_PARSER_P4NSPECT_TABLE = "match_gtpv1"
    GTP_PARSER_FEATURE_NAME = "GTP"


class SflowConsts:
    SFLOW_FEATURE_NAME = "sflow"
    DEFAULT_UDP = 6343
    UDP_1 = 6555
    COLLECTOR_0 = "collector0"
    COLLECTOR_1 = "collector1"
    COLLECTOR_F = "collector2"
    COLLECTOR = {
        COLLECTOR_0: {
            'name': COLLECTOR_0,
            'ip': '50.0.0.2',
            'ipv6': '5000::2',
            'port': DEFAULT_UDP,
            'sample_file': "/tmp/collector_0.json"
        },
        COLLECTOR_1: {
            'name': COLLECTOR_1,
            'ip': '60.0.0.2',
            'ipv6': '6000::2',
            'port': UDP_1,
            'sample_file': "/tmp/collector_1.json"
        },
        COLLECTOR_F: {
            'name': COLLECTOR_F,
            'ip': '70.1.1.2'
        }
    }

    LOOPBACK_0 = "Loopback0"
    LOOPBACK_0_IP = "1000:aaaa:bbbb:cccc:dddd:eeee:2000:3000"
    VRF_DEFAULT = "default"
    AGENT_ID_DEFAULT = "default"
    SFLOW_UP = "up"
    SFLOW_DOWN = "down"
    SFLOW_TOOL_PRETTY = "/usr/local/bin/sflowtool -J -p "
    POLLING_INTERVAL_DEVIATION_TOLERANCE = 2
    SAMPLE_RATE_1 = 500
    SAMPLE_RATE_2 = 300
    SAMPLE_RATE_3 = 1000
    SEND_PACKET_NUM = 1024

    DUT_HA_1_IP = "30.0.0.1"
    DUT_HA_2_IP = "40.0.0.1"
    HA_DUT_1_IP = "30.0.0.2"
    HA_DUT_2_IP = "40.0.0.2"

    DUT_HB_1_IP = "50.0.0.1"
    DUT_HB_2_IP = "60.0.0.1"
    DUT_HB_1_IP_V6 = "5000::1"
    DUT_HB_2_IP_V6 = "6000::1"
    HB_DUT_1_IP = "50.0.0.2"
    HB_DUT_2_IP = "60.0.0.2"
    HB_DUT_1_IP_V6 = "5000::2"
    HB_DUT_2_IP_V6 = "6000::2"
    COLLECTOR_0_IP = HB_DUT_1_IP
    COLLECTOR_1_IP = HB_DUT_2_IP
    COLLECTOR_0_IP_V6 = HB_DUT_1_IP_V6
    COLLECTOR_1_IP_V6 = HB_DUT_2_IP_V6
    COLLECTOR_LIST = [COLLECTOR_0, COLLECTOR_1]
    MGMT_INTF = 'eth0'
    POLLING_INTERVAL_0 = 0
    POLLING_INTERVAL_1 = 5
    POLLING_INTERVAL_2 = 10
    POLLING_INTF_0_WAIT_TIME = 10


class CounterpollConstants:
    COUNTERPOLL_SHOW = 'sudo counterpoll show'
    COUNTERPOLL_DISABLE = 'sudo counterpoll {} disable'
    COUNTERPOLL_ENABLE = 'sudo counterpoll {} enable'
    COUNTERPOLL_RESTORE = 'sudo counterpoll {} {}'
    COUNTERPOLL_INTERVAL_STR = 'sudo counterpoll {} interval {}'
    COUNTERPOLL_QUEST = 'sudo counterpoll --help'
    EXCLUDE_COUNTER_SUB_COMMAND = ['show', 'config-db', "flowcnt-trap", "flowcnt-route", "tunnel"]
    INTERVAL = 'Interval (in ms)'
    TYPE = 'Type'
    STATUS = 'Status'
    STDOUT = 'stdout'
    PG_DROP = 'pg-drop'
    PG_DROP_STAT_TYPE = 'PG_DROP_STAT'
    QUEUE_STAT_TYPE = 'QUEUE_STAT'
    QUEUE = 'queue'
    PORT_STAT_TYPE = 'PORT_STAT'
    PORT = 'port'
    PORT_BUFFER_DROP_TYPE = 'PORT_BUFFER_DROP'
    PORT_BUFFER_DROP = 'port-buffer-drop'
    RIF_STAT_TYPE = 'RIF_STAT'
    RIF = 'rif'
    WATERMARK = 'watermark'
    QUEUE_WATERMARK_STAT_TYPE = 'QUEUE_WATERMARK_STAT'
    PG_WATERMARK_STAT_TYPE = 'PG_WATERMARK_STAT'
    BUFFER_POOL_WATERMARK_STAT_TYPE = 'BUFFER_POOL_WATERMARK_STAT'
    ACL = 'acl'
    ACL_TYPE = 'ACL'
    TUNNEL_STAT = 'tunnel'
    TUNNEL_STAT_TYPE = 'TUNNEL_STAT'
    FLOW_CNT_TRAP_STAT = 'flowcnt-trap'
    FLOW_CNT_TRAP_STAT_TYPE = 'FLOW_CNT_TRAP_STAT'
    FLOW_CNT_ROUTE_STAT = 'flowcnt-route'
    FLOW_CNT_ROUTE_STAT_TYPE = 'FLOW_CNT_ROUTE_STAT'

    COUNTERPOLL_MAPPING = {PG_DROP_STAT_TYPE: PG_DROP,
                           QUEUE_STAT_TYPE: QUEUE,
                           PORT_STAT_TYPE: PORT,
                           PORT_BUFFER_DROP_TYPE: PORT_BUFFER_DROP,
                           RIF_STAT_TYPE: RIF,
                           BUFFER_POOL_WATERMARK_STAT_TYPE: WATERMARK,
                           QUEUE_WATERMARK_STAT_TYPE: WATERMARK,
                           PG_WATERMARK_STAT_TYPE: WATERMARK,
                           ACL_TYPE: ACL,
                           TUNNEL_STAT_TYPE: TUNNEL_STAT,
                           FLOW_CNT_TRAP_STAT_TYPE: FLOW_CNT_TRAP_STAT,
                           FLOW_CNT_ROUTE_STAT_TYPE: FLOW_CNT_ROUTE_STAT}
    COUNTERPOLL_INTERVAL = {WATERMARK: 10000,
                            PORT: 10000,
                            RIF: 10000,
                            PG_DROP: 10000,
                            QUEUE: 10000,
                            PORT_BUFFER_DROP: 10000,
                            ACL: 10000,
                            TUNNEL_STAT: 10000}
    SX_SDK = 'sx_sdk'
    COUNTERPOLL_CPU_USAGE_THRESHOLD = 10
    WATERMARK_INTERVAL_1 = 10000
    WATERMARK_INTERVAL_DEFAULT = 60000

    CPU_THRESHOLD_FOR_ORDINARY_PROCESS = 50
    CPU_THRESHOLD_FOR_HIGH_CONSUME_PROCESS = 90
    MEMORY_THRESHOLD = 50
    MEMORY_THRESHOLD_ASAN = 90
    CPU_HIGH_CONSUME_PERSIST_TIME_THRESHOLD = 8

    CPU_MEMORY_SAMPLE_INTERVAL_1 = 5
    CPU_MEMORY_SAMPLE_ITERATION_1 = 24
    CPU_MEMORY_SAMPLE_INTERVAL_2 = 1
    CPU_MEMORY_SAMPLE_ITERATION_2 = 60


class AppExtensionInstallationConstants:
    WJH_APP_NAME = 'what-just-happened'
    WJH_REPOSITORY = 'harbor.mellanox.com/sonic-wjh/docker-wjh'
    LC_MANAGER = 'line-card-manager'
    DOROCE = 'doroce'
    LC_MANAGER_REPOSITORY = 'harbor.mellanox.com/sonic-lc-manager/line-card-manager'
    CMD_GET_SDK_VERSION = "docker exec -i {} bash -c 'sx_sdk --version'"
    SYNCD_DOCKER = 'syncd'
    APPLICATION_LIST = [
        P4SamplingConsts.APP_NAME,
        WJH_APP_NAME,
        LC_MANAGER,
        P4ExamplesConsts.APP_NAME,
        DOROCE
    ]
    APP_EXTENSION_PROJECT_MAPPING = {'sonic-wjh': WJH_APP_NAME,
                                     'p4-sampling': P4SamplingConsts.APP_NAME,
                                     'sonic-lc-manager': LC_MANAGER,
                                     'p4-examples': P4ExamplesConsts.APP_NAME,
                                     'doroce': DOROCE}
    APPS_WHERE_SX_SDK_NOT_PRESENT = [P4SamplingConsts.APP_NAME, P4ExamplesConsts.APP_NAME, DOROCE]


class MarsConstants:
    SONIC_MARS_BASE_PATH = "/.autodirect/sw_regression/system/SONIC/MARS"

    SONIC_MGMT_DEVICE_ID = "SONIC_MGMT"
    NGTS_PATH_PYTEST = "/ngts_venv/bin/pytest"
    NGTS_PATH_PYTHON = "/ngts_venv/bin/python"
    TEST_SERVER_DEVICE_ID = "TEST_SERVER"
    NGTS_DEVICE_ID = "NGTS"
    DUT_DEVICE_ID = "DUT"
    FANOUT_DEVICE_ID = "FANOUT"
    SONIC_MGMT_DIR = '/root/mars/workspace/sonic-mgmt/'
    UPDATED_FW_TAR_PATH = 'tests/platform_tests/fwutil/updated-fw.tar.gz'
    HTTP_SERVER_NBU_NFS = 'http://nbu-nfs.mellanox.com'

    DOCKER_SONIC_MGMT_IMAGE_NAME = "docker-sonic-mgmt"
    DOCKER_NGTS_IMAGE_NAME = "docker-ngts"

    SONIC_MGMT_REPO_URL = "http://10.7.77.140:8080/switchx/sonic/sonic-mgmt"
    SONIC_MGMT_MOUNTPOINTS = {
        '/.autodirect/mswg/projects': '/.autodirect/mswg/projects',
        '/auto/sw_system_project': '/auto/sw_system_project',
        '/auto/sw_system_release': '/auto/sw_system_release',
        '/.autodirect/sw_system_release/': '/.autodirect/sw_system_release/',
        '/auto/sw_regression/system/SONIC/MARS': '/auto/sw_regression/system/SONIC/MARS',
        '/.autodirect/sw_regression/system/SONIC/MARS': '/.autodirect/sw_regression/system/SONIC/MARS',
        '/workspace': '/workspace',
        '/.autodirect/LIT/SCRIPTS': '/.autodirect/LIT/SCRIPTS'
    }

    VER_SDK_PATH = "/opt/ver_sdk"
    EXTRA_PACKAGE_PATH_LIST = ["/usr/lib64/python2.7/site-packages"]

    TOPO_ARRAY = ("t0-56-po2vlan", "t0", "t1-lag", "ptf32", "t0-64", "t1-64-lag", "t0-56")
    REBOOT_TYPES = {
        "reboot": "reboot",
        "fast-reboot": "fast-reboot",
        "warm-reboot": "warm-reboot"
    }

    DOCKER_REGISTRY = "harbor.mellanox.com/sonic"

    DUT_LOG_BACKUP_PATH = "/.autodirect/sw_system_project/sonic/dut_logs"

    BRANCH_PTF_MAPPING = {'master': 'latest',
                          '202012': '42007',
                          '202106': '42007'
                          }


class PlayeresAliases:
    Aliases_list = ['sl']
    SL = 'sl'
    duts_list = ['dut', 'dut-b']


class NvosCliTypes:
    NvueCliTypes = ["NVUE", "MLNX_OS"]


class BluefieldConstants:
    BASE_SLINK_BF_IMAGE = '/auto/sw_system_release/sonic/sonic_dpu_config/images/{}/Image'
    BASE_SLINK_BF_INITRAMFS = '/auto/sw_system_release/sonic/sonic_dpu_config/initramfs/{}/initramfs'
    BMC_USER = 'root'
    BMC_PASS = '3tango11'
