class ArConsts:
    DOAI_CONTAINER_NAME = "doai"
    PORT_UTIL_PERCENT = 1
    PORT_UTIL_DEFAULT_PERCENT = 70
    FRR_CONFIG_FOLDER = 'frr_config'
    AR_CONFIG_FOLDER = 'ar_profile_config'
    AR_CUSTOM_PROFILE_FILE_NAME = 'custom_profile.json'
    PACKET_SPEED_5M = 5
    PACKET_SPEED_15M = 15
    PACKET_NUM_20 = 20
    PACKET_NUM_1000 = 1000
    RECEIVE_NUM_500 = 500
    PACKET_NUM_10000000 = 10000000
    LO_THRESHOLD_PROFILE0 = 200
    HOST_A = 'ha'
    HOST_B = 'hb'
    NON_EXIST_PROFILE = 'non_exist_profile'
    NON_EXIST_PORT = 'Ethernet1000'
    DUMMY_VLAN = '2'
    DUMMY_VLAN_INTF = 'Vlan2'
    DUMMY_VLAN_IP = '123.1.2.3'
    DUMMY_LAG_INTF = 'PortChannel0'
    MGMT_PORT = 'eth0'
    INVALID_LINK_UTIL_PERCENT_VALUE = '101'
    AR_DUMP_FILE_NAME = "dump/doai.gz"

    WARNING_MESSAGE = 'doAI is not enabled. Enable the feature before configuring Adaptive Routing'
    NON_EXIST_PROFILE_ERROR_MESSAGE = f'Profile {NON_EXIST_PROFILE} does not exist'
    NON_EXIST_PORT_ERROR_MESSAGE = f'Invalid port {NON_EXIST_PORT}'
    AR_ON_VLAN_INTF_ERROR_MESSAGE = f'Invalid port {DUMMY_VLAN_INTF}'
    AR_ON_LAG_INTF_ERROR_MESSAGE = f'Invalid port {DUMMY_LAG_INTF}'
    AR_ON_LAG_MEMBER_ERROR_MESSAGE = 'Adaptive Routing can be enabled only on L3 port'
    AR_ON_MGMT_PORT_ERROR_MESSAGE = f'Invalid port {MGMT_PORT}'
    INVALID_LINK_UTIL_PERCENT_MESSAGE = f'{INVALID_LINK_UTIL_PERCENT_VALUE} is not in the valid range of 1 to 100'

    DIR_DELIMITER = '/'
    PACKET_AGING_SCRIPT_PATH = 'sonic-mgmt/tests/qos/files/mellanox/packets_aging.py'
    CONFIG_DB_FILE_PATH = "/etc/sonic/"
    CONFIG_DB_FILE_NAME = "config_db.json"
    DUT_HOME_DIR = "/home/admin/"

    TC3_ROCEV2_AR_FLAG_PACKET = "Ether(src='{}',dst='{}')/IP(src='{}',dst='{}')" \
                                "/UDP(sport=56238, dport=4791)/b'\\x00\\x00\\xff\\xff\\x00\\" \
                                "x00\\x00\\x00@\\x00\\x00\\x00\\xcd\\x8bw\\x1b'"
    TC3_ROCEV2_AR_FLAG_FILTER = 'port 4791 and src={} and dst={}'
    ROCEV2_PACKET = 'Ether(src="{}",dst="{}")/IP(src="{}",dst="{}")/UDP(sport=56238, dport=4791)'
    ROCEV2_FILTER = 'port 4791 and src={} and dst={}'
    IP_PACKET = 'Ether(src="{}",dst="{}")/IP(src="{}",dst="{}")'
    IP_FILTER = 'port 4791 and ether[46:4]={} and ether[76:4]={}'

    # Global AR feature keys
    AR_GLOBAL = "Global"
    AR_PROFILE_GLOBAL = "Profiles"
    AR_PORTS_GLOBAL = "Ports"
    DOAI_STATE = 'DoAI state'
    AR_STATE = 'AR state'
    AR_ACTIVE_PROFILE = 'AR active profile'
    # AR profile keys
    PROF_KEY_NAME = 'name'
    PROF_KEY_MODE = 'mode'
    PROF_KEY_BUSY_THRES = 'busy_threshold'
    PROF_KEY_FREE_THRES = 'free_threshold'
    PROF_KEY_CONG_THRES_LO = 'congestion_th_low \\(Cells\\)'
    PROF_KEY_CONG_THRES_ME = 'congestion_th_medium \\(Cells\\)'
    PROF_KEY_CONG_THRES_HI = 'congestion_th_high \\(Cells\\)'
    PROF_KEY_SHAPER_FR_EN = 'from_shaper_enable'
    PROF_KEY_SHAPER_FR = "from_shaper \\(\\* 100 ns\\)"
    PROF_KEY_SHAPER_TO_EN = 'to_shaper_enable'
    PROF_KEY_SHAPER_TO = 'to_shaper \\(\\* 100 ns\\)'
    PROF_KEY_ECMP_SIZE = 'ecmp_size'
    PROF_KEY_ELEPH_FLOW = 'elephant_enable'

    AR_PROFILE_KEYS_LIST = [
        PROF_KEY_MODE,
        PROF_KEY_BUSY_THRES,
        PROF_KEY_FREE_THRES,
        PROF_KEY_CONG_THRES_LO,
        PROF_KEY_CONG_THRES_ME,
        PROF_KEY_CONG_THRES_HI,
        PROF_KEY_SHAPER_FR_EN,
        PROF_KEY_SHAPER_FR,
        PROF_KEY_SHAPER_TO_EN,
        PROF_KEY_SHAPER_TO,
        PROF_KEY_ECMP_SIZE,
        PROF_KEY_ELEPH_FLOW
    ]

    MODE_DICT = {
        '0': 'free',
        '1': 'time_bound',
        '2': 'random'
    }
    # Golden Profile values
    GOLDEN_PROFILE0 = 'profile0'
    GOLDEN_PROFILE0_PARAMETERS = {
        PROF_KEY_NAME: GOLDEN_PROFILE0,
        PROF_KEY_MODE: MODE_DICT['0'],
        PROF_KEY_CONG_THRES_LO.replace("\\", ""): str(LO_THRESHOLD_PROFILE0),
        PROF_KEY_CONG_THRES_ME.replace("\\", ""): '1000',
        PROF_KEY_CONG_THRES_HI.replace("\\", ""): '10000',
        PROF_KEY_BUSY_THRES: '0',
        PROF_KEY_FREE_THRES: '4',
        PROF_KEY_SHAPER_FR_EN: 'true',
        PROF_KEY_SHAPER_FR.replace("\\", ""): '10',
        PROF_KEY_SHAPER_TO_EN: 'N/A',
        PROF_KEY_SHAPER_TO.replace("\\", ""): 'N/A',
        PROF_KEY_ECMP_SIZE: '64',
        PROF_KEY_ELEPH_FLOW: 'false'
    }

    CUSTOM_PROFILE_NAME = 'custom_profile0'
    CUSTOM_PROFILE0_PARAMETERS = {
        PROF_KEY_NAME: CUSTOM_PROFILE_NAME,
        PROF_KEY_MODE: MODE_DICT['1'],
        PROF_KEY_CONG_THRES_LO.replace("\\", ""): '200',
        PROF_KEY_CONG_THRES_ME.replace("\\", ""): '1000',
        PROF_KEY_CONG_THRES_HI.replace("\\", ""): '10000',
        PROF_KEY_BUSY_THRES: '0',
        PROF_KEY_FREE_THRES: '4',
        PROF_KEY_SHAPER_FR_EN: 'true',
        PROF_KEY_SHAPER_FR.replace("\\", ""): '100',
        PROF_KEY_SHAPER_TO_EN: 'false',
        PROF_KEY_SHAPER_TO.replace("\\", ""): '10',
        PROF_KEY_ECMP_SIZE: '64',
        PROF_KEY_ELEPH_FLOW: 'false'
    }

    SIMX_REBOOT_TYPES = ['fast-reboot', 'reboot']

    DUMMY_INTF = {
        'name': 'dummy_1',
        'ipv4_addr': '10.0.0.1', 'ipv4_mask': '24', 'ipv4_network': '10.0.0.0/24',
        'ipv6_addr': '5000::1', 'ipv6_mask': '64', 'ipv6_network': '5000::/64',
    }

    V4_CONFIG = {
        'dut_ha_1': '1.1.1.1', 'ha_dut_1': '1.1.1.2',
        'dut_hb_1': '2.2.2.1', 'hb_dut_1': '2.2.2.3',
        'dut_hb_2': '3.3.3.1', 'hb_dut_2': '3.3.3.3',
        'ipv4_network': '10.0.0.0/24'
    }

    V6_CONFIG = {
        'dut_ha_1': '1000::1', 'ha_dut_1': '1000::2',
        'dut_hb_1': '2000::1', 'hb_dut_1': '2000::3',
        'dut_hb_2': '3000::1', 'hb_dut_2': '3000::3',
        'ipv6_network': '5000::/64'
    }
