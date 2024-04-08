import os


class ArPerfConsts:
    AR_PERF_CONFIG_FOLDER = 'config_files'
    CUSTOM_IBM_PROFILE_JSON = 'ibm_profile.json'
    IBM_CUSTOM_PROFILE_NAME = 'ibm_profile'
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    CONFIG_FILES_DIR = os.path.join(BASE_DIR, 'config_files')
    DISABLE_MAC_SCRIPT = "disable_mac_learn.py"
    LB_FILTER_SCRIPT = "api_for_filter.py"
    LB_SCRIPT_TG = "run_lb_script.sh"
    IP_NEIGH_SCRIPT = "config_ip_neigh.sh"
    TRAFFIC_SENDER_SCRIPT_TG = "traffic_generator.py"
    CONFIG_FILES_LIST_LEFT_TG = [DISABLE_MAC_SCRIPT, LB_FILTER_SCRIPT, LB_SCRIPT_TG]
    CONFIG_FILES_LIST_RIGHT_TG = [DISABLE_MAC_SCRIPT, LB_FILTER_SCRIPT, LB_SCRIPT_TG]
    CONFIG_FILES_DICT = {"left_tg": CONFIG_FILES_LIST_LEFT_TG, "right_tg": CONFIG_FILES_LIST_RIGHT_TG}
    DEFAULT_SAMPLE_TIME_IN_SEC = 20
    EXTENDED_SAMPLE_TIME_IN_SEC = 60
    PACKET_SIZE_LIST = [1500, 2000, 4000, 8000]
    PACKET_SIZE_TO_PACKET_NUM_DICT = {1500: 32, 2000: 16, 4000: 8, 8000: 8}
    TG_TX_UTIL_TH = 95
    DUT_TX_UTIL_TH_DICT = {1500: 64, 2000: 80, 4000: 92, 8000: 93}
    DUT_TX_UTIL_W_IBM_TH_DICT = {1500: 64, 2000: 80, 4000: 96, 8000: 95}
    EXPECTED_EGRESS_PORTS = 64
    EXPECTED_MLOOP_PORTS = 64
    EXPECTED_AR_PORTS = 128
    EXPECTED_PORTS_BY_TYPE = {"egress": EXPECTED_EGRESS_PORTS,
                              "mloop": EXPECTED_MLOOP_PORTS,
                              "ar": EXPECTED_AR_PORTS}
    VALUE_INDEX = 0
    TIMESTAMP_INDEX = 1
    LOG_PORT_LEFT_TG = 0x10001
    LOG_PORT_RIGHT_TG = 0x10081
    LOG_PORTS_DICT = {"left_tg": LOG_PORT_LEFT_TG, "right_tg": LOG_PORT_RIGHT_TG}
    L_IP_NEIGH = "10.10.10.10"
    R_IP_NEIGH = "20.20.20.20"
    PERF_SUPPORTED_REBOOT_TYPES = ['reboot', 'config reload -y']
    SLEEP_TIME_BEFORE_SAMPLE = 15
