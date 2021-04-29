class PytestConst:
    run_config_only_arg = '--run_config_only'
    run_test_only_arg = '--run_test_only'
    run_cleanup_only_arg = '--run_cleanup_only'
    alluredir_arg = '--alluredir'
    disable_loganalyzer = '--disable_loganalyzer'


class SonicConst:
    DOCKERS_LIST = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']

    CPU_RAM_CHECK_PROCESS_LIST = ['sx_sdk', 'syncd', 'redis-server', 'snmpd', 'zebra', 'bgpd', 'bgpcfgd', 'bgpmon',
                                  'fpmsyncd', 'orchagent', 'ntpd', 'neighsyncd', 'vlanmgrd', 'intfmgrd', 'portmgrd',
                                  'buffermgrd', 'vrfmgrd', 'nbrmgrd', 'vxlanmgrd', 'sensord']

    SONIC_CONFIG_FOLDER = '/etc/sonic/'
    PORT_CONFIG_INI = 'port_config.ini'
    CONFIG_DB_JSON = 'config_db.json'
    CONFIG_DB_JSON_PATH = SONIC_CONFIG_FOLDER + CONFIG_DB_JSON
    PLATFORM_JSON_PATH = "/usr/share/sonic/device/{PLATFORM}/platform.json"

    BREAKOUT_MODE_WITH_DIFF_LANE_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G\(\d\)\+\dx\d+G\(\d\)"  # i.e, 2x25G(2)+1x50G(2)

    BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G\[[\d+G,]+\]"  # 1x100G[50G,25G,1G]
    BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX = r"\dx\d+G"  # 2x50G

    BREAKOUT_MODES_REGEX = "{}|{}|{}".format(BREAKOUT_MODE_WITH_DIFF_LANE_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITH_ADDITIONAL_SUPPORTED_SPEEDS_REGEX,
                                             BREAKOUT_MODE_WITHOUT_ADDITIONAL_SUPPORTED_SPEEDS_REGEX)


class InfraConst:
    HTTP_SERVER = 'http://fit69'
    MARS_TOPO_FOLDER_PATH = '/auto/sw_regression/system/SONIC/MARS/conf/topo/'
    REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'

    MYSQL_SERVER = '10.208.1.11'
    MYSQL_USER = 'sonic'
    MYSQL_PASSWORD = 'sonic11'
    MYSQL_DB = 'sonic'
    RC_SUCCESS = 0
    NGTS_PATH_PYTEST = '/ngts_venv/bin/pytest'
    SLEEP_BEFORE_RRBOOT = 5
    SLEEP_AFTER_RRBOOT = 35


class LinuxConsts:
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

SPC = {
 '25GBASE-CR': ['10G', '25G'],
 '50GBASE-CR2': ['50G'],
 '40GBASE-CR4': ['40G', '50G'],
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
 '25GBASE-CR': ['10G', '25G'],
 '50GBASE-CR2': ['50G'],
 '40GBASE-CR4': ['40G', '50G'],
 '100GBASE-CR4': ['100G'],
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


class P4SamplingEntryConsts:
    ENTRY_PRIORITY_HEADERS = ['PRIO']
    COUNTER_PACKETS_HEADERS = ['Packets']
    COUNTER_BYTES_HEADERS = ['Bytes']
    FLOW_ENTRY_KEY_HEADERS = ['Key SIP', 'Key DIP', 'Key PROTO', 'Key L4 SPORT', 'Key L4 SPORT',
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
