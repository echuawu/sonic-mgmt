import re
import logging

pattern_top_layer_key_value = "^(?P<key>Ethernet\d+):(?P<value>.*)"
pattern_second_layer_key_value = r"(^\s{8}|\t{1})(?P<key>[a-zA-Z0-9][a-zA-Z0-9\s\/\(\)-]+):(?P<value>.*)"
pattern_third_layer_key_value = r"(^\s{16}|\t{2})(?P<key>[a-zA-Z0-9][a-zA-Z0-9\s\/]+):(?P<value>.*)"

pattern_digit_unit = "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>dBm|mA|C|c|Volts)"


def parse_one_sfp_eeprom_info(sfp_eeprom_info):
    """
    Parse the one sfp eeprom info, return top_key, sfp_eeprom_info_dict
    e.g
    sfp_info:
    Ethernet0: SFP EEPROM detected
        Application Advertisement: N/A
        Connector: No separable connector
        Encoding: 64B/66B
        Extended Identifier: Power Class 3 Module (2.5W max.), No CLEI code present in Page 02h, CDR present in TX, CDR present in RX
        Extended RateSelect Compliance: Unknown
        Identifier: QSFP28 or later
        Length Cable Assembly(m): 3.0
        Nominal Bit Rate(100Mbs): 255
        Specification compliance:
                10/40G Ethernet Compliance Code: Extended
                Extended Specification Compliance: 100G AOC (Active Optical Cable) or 25GAUI C2M AOC
                Fibre Channel Link Length: Unknown
                Fibre Channel Speed: Unknown
                Fibre Channel Transmission Media: Unknown
                Fibre Channel Transmitter Technology: Unknown
                Gigabit Ethernet Compliant Codes: Unknown
                SAS/SATA Compliance Codes: Unknown
                SONET Compliance Codes: Unknown
        Vendor Date Code(YYYY-MM-DD Lot): 2019-01-17
        Vendor Name: Mellanox
        Vendor OUI: 00-02-c9
        Vendor PN: MFA1A00-C003
        Vendor Rev: B2
        Vendor SN: MT1903FT05965
        ChannelMonitorValues:
                RX1Power: 0.927dBm
                RX2Power: 0.938dBm
                RX3Power: 0.912dBm
                RX4Power: 0.95dBm
                TX1Bias: 6.75mA
                TX1Power: 1.071dBm
                TX2Bias: 6.75mA
                TX2Power: 1.04dBm
                TX3Bias: 6.75mA
                TX3Power: 1.039dBm
                TX4Bias: 6.75mA
                TX4Power: 1.031dBm
        ChannelThresholdValues:
                RxPowerHighAlarm  : 5.4dBm
                RxPowerHighWarning: 2.4dBm
                RxPowerLowAlarm   : -13.307dBm
                RxPowerLowWarning : -10.301dBm
                TxBiasHighAlarm   : 8.5mA
                TxBiasHighWarning : 8.0mA
                TxBiasLowAlarm    : 5.492mA
                TxBiasLowWarning  : 6.0mA
        ModuleMonitorValues:
                Temperature: 43.105C
                Vcc: 3.235Volts
        ModuleThresholdValues:
                TempHighAlarm  : 80.0C
                TempHighWarning: 70.0C
                TempLowAlarm   : -10.0C
                TempLowWarning : 0.0C
                VccHighAlarm   : 3.5Volts
                VccHighWarning : 3.465Volts
                VccLowAlarm    : 3.1Volts
                VccLowWarning  : 3.135Volts
    top_key, sfp_eeprom_info_dict:
    Ethernet0,
    {
        'Ethernet0': 'SFP EEPROM detected',
        'Application Advertisement': 'N/A',
        'Connector': 'No separable connector',
        'Encoding': '64B/66B',
        'Extended Identifier': 'Power Class 3 Module (2.5W max.), No CLEI code present in Page 02h, CDR present in TX, CDR present in RX',
        'Extended RateSelect Compliance': 'Unknown',
        'Identifier': 'QSFP28 or later',
        'Length Cable Assembly(m)': '3.0',
        'Nominal Bit Rate(100Mbs)': '255',
        'Specification compliance': {
            '10/40G Ethernet Compliance Code': 'Extended',
            'Extended Specification Compliance': '100G AOC (Active Optical Cable) or 25GAUI C2M AOC',
            'Fibre Channel Link Length': 'Unknown',
            'Fibre Channel Speed': 'Unknown',
            'Fibre Channel Transmission Media': 'Unknown',
            'Fibre Channel Transmitter Technology': 'Unknown',
            'Gigabit Ethernet Compliant Codes': 'Unknown',
            'SAS/SATA Compliance Codes': 'Unknown',
            'SONET Compliance Codes': 'Unknown'
        },
        'Vendor Date Code(YYYY-MM-DD Lot)': '2019-01-17',
        'Vendor Name': 'Mellanox',
        'Vendor OUI': '00-02-c9',
        'Vendor PN': 'MFA1A00-C003',
        'Vendor Rev': 'B2',
        'Vendor SN': 'MT1903FT05965',
        'ChannelMonitorValues': {
            'RX1Power': '0.927dBm',
            'RX2Power': '0.938dBm',
            'RX3Power': '0.912dBm',
            'RX4Power': '0.95dBm',
            'TX1Bias': '6.75mA',
            'TX1Power': '1.071dBm',
            'TX2Bias': '6.75mA',
            'TX2Power': '1.04dBm',
            'TX3Bias': '6.75mA',
            'TX3Power': '1.039dBm',
            'TX4Bias': '6.75mA',
            'TX4Power': '1.031dBm'
        },
        'ChannelThresholdValues': {
            'RxPowerHighAlarm': '5.4dBm',
            'RxPowerHighWarning': '2.4dBm',
            'RxPowerLowAlarm': '-13.307dBm',
            'RxPowerLowWarning': '-10.301dBm',
            'TxBiasHighAlarm': '8.5mA',
            'TxBiasHighWarning': '8.0mA',
            'TxBiasLowAlarm': '5.492mA',
            'TxBiasLowWarning': '6.0mA'
        },
        'ModuleMonitorValues': {
            'Temperature': '43.105C',
            'Vcc': '3.235Volts'
        },
        'ModuleThresholdValues': {
            'TempHighAlarm': '80.0C',
            'TempHighWarning': '70.0C',
            'TempLowAlarm': '-10.0C',
            'TempLowWarning': '0.0C',
            'VccHighAlarm': '3.5Volts',
            'VccHighWarning': '3.465Volts',
            'VccLowAlarm': '3.1Volts',
            'VccLowWarning': '3.135Volts'
        }
    }
    """
    one_sfp_eeprom_info_dict = {}
    second_layer_dict = {}
    previous_key = ""
    top_key = ""
    for line in sfp_eeprom_info.split("\n"):
        res1 = re.match(pattern_top_layer_key_value, line)
        if res1:
            top_key = res1.groupdict()["key"].strip()
            one_sfp_eeprom_info_dict[top_key] = res1.groupdict()["value"].strip()
            continue
        res2 = re.match(pattern_second_layer_key_value, line)
        if res2:
            if second_layer_dict and previous_key:
                one_sfp_eeprom_info_dict[previous_key] = second_layer_dict
                second_layer_dict = {}
            one_sfp_eeprom_info_dict[res2.groupdict()["key"].strip()] = res2.groupdict()["value"].strip()
            previous_key = res2.groupdict()["key"].strip()
        else:
            res3 = re.match(pattern_third_layer_key_value, line)
            if res3:
                second_layer_dict[res3.groupdict()["key"].strip()] = res3.groupdict()["value"].strip()
    if second_layer_dict and previous_key:
        one_sfp_eeprom_info_dict[previous_key] = second_layer_dict

    return top_key, one_sfp_eeprom_info_dict


def parse_sfp_eeprom_infos(eeprom_infos):
    """
    This method is to pares sfp eeprom infos, and return sfp_eeprom_info_dict
    """
    sfp_eeprom_info_dict = {}
    for sfp_info in eeprom_infos.split("\n\n"):
        intf, eeprom_info = parse_one_sfp_eeprom_info(sfp_info)
        sfp_eeprom_info_dict[intf] = eeprom_info
    return sfp_eeprom_info_dict


def check_sfp_eeprom_info(duthost, sfp_eeprom_info, is_support_dom, show_eeprom_cmd):
    """
    This method is check sfp info is correct or not.
    1. Check if all expected keys exist in the sfp_eeprom_info
    2. Check if Check Vendor name is Mellnaox and Vendor OUI is 00-02-c9
    3. When cable support dom, check the corresponding keys related to monitor exist, and the the corresponding value has correct format
    """
    logging.info("Check all expected keys exist in sfp info")
    expected_keys = set(["Application Advertisement", "Connector", "Encoding", "Extended Identifier",
                         "Extended RateSelect Compliance", "Identifier", "Length Cable Assembly(m)",
                         "Nominal Bit Rate(100Mbs)", "Specification compliance", "Vendor Date Code(YYYY-MM-DD Lot)",
                         "Vendor Name", "Vendor OUI", "Vendor PN", "Vendor Rev", "Vendor SN", "ChannelMonitorValues",
                         "ChannelThresholdValues", "ModuleMonitorValues", "ModuleThresholdValues"])
    excluded_keys = set()
    if "202012" in duthost.os_version and show_eeprom_cmd == "sudo sfputil show eeprom -d":
        excluded_keys = set(["Application Advertisement", "ChannelThresholdValues", "ModuleThresholdValues"])
        expected_keys = expected_keys - excluded_keys

    for key in expected_keys:
        assert key in sfp_eeprom_info, "key {} doesn't exist in {}".format(key, sfp_eeprom_info)

    if is_support_dom:

        if "ChannelThresholdValues" not in excluded_keys:
            logging.info("Check if ChannelThresholdValues' keys exist and the corresponding value format is correct")
            expected_channel_threshold_values_keys = ["RxPowerHighAlarm", "RxPowerHighWarning", "RxPowerLowAlarm",
                                                      "RxPowerLowWarning", "TxBiasHighAlarm", "TxBiasHighWarning",
                                                      "TxBiasLowAlarm", "TxBiasLowWarning"]
            for i, key in enumerate(expected_channel_threshold_values_keys):
                assert key in sfp_eeprom_info["ChannelThresholdValues"], \
                    "key {} doesn't exist in {}".format(key, sfp_eeprom_info["ChannelThresholdValues"])
                pattern_digit_unit = "^(?P<digit>-[0-9\.]+|[0-9.]+|-inf)(?P<unit>dBm$)" if i < 4 else "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>mA$)"
                assert re.match(pattern_digit_unit, sfp_eeprom_info["ChannelThresholdValues"][key]), \
                    "Value of {}:{} format is not correct. pattern is {}".format(key,
                                                                                 sfp_eeprom_info["ChannelThresholdValues"][key],
                                                                                 pattern_digit_unit)
        if "ModuleThresholdValues" not in excluded_keys:
            logging.info("Check if ModuleThresholdValues' keys exist and the corresponding format is correct")
            expected_module_threshold_values_keys = ["TempHighAlarm", "TempHighWarning", "TempLowAlarm", "TempLowWarning",
                                                     "VccHighAlarm", "VccHighWarning", "VccLowAlarm", "VccLowWarning"]
            for i, key in enumerate(expected_module_threshold_values_keys):
                assert key in sfp_eeprom_info["ModuleThresholdValues"], "key {} doesn't exist in {}".format(key,
                                                                                                            sfp_eeprom_info["ModuleThresholdValues"])
                pattern_digit_unit = "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>[Cc]$)" if i < 4 else "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>Volts$)"
                assert re.match(pattern_digit_unit, sfp_eeprom_info["ModuleThresholdValues"][key]), \
                    "Value of {}:{} format is not correct. pattern is {}".format(key,
                                                                                 sfp_eeprom_info["ModuleThresholdValues"][key],
                                                                                 pattern_digit_unit)

        logging.info("Check if ChannelMonitorValues's value format is correct")
        for k, v in sfp_eeprom_info["ChannelMonitorValues"].items():
            pattern_digit_unit = "^(?P<digit>-[0-9\.]+|[0-9.]+|-inf)(?P<unit>dBm$)" if "Power" in k else "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>mA$)"
            assert re.match(pattern_digit_unit, v), \
                "Value of {}:{} format is not correct. pattern is {}".format(k, v, pattern_digit_unit)

        logging.info("Check ModuleMonitorValues keys exist and the corresponding value format is correct")
        expected_module_monitor_values_keys = ["Temperature", "Vcc"]
        for i, key in enumerate(expected_module_monitor_values_keys):
            assert key in sfp_eeprom_info["ModuleMonitorValues"], "key {} doesn't exist in {}".format(key,
                                                                                                      sfp_eeprom_info["ModuleThresholdValues"])
            pattern_digit_unit = "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>[Cc]$)" if i < 1 else "^(?P<digit>-[0-9\.]+|[0-9.]+)(?P<unit>Volts$)"
            assert re.match(pattern_digit_unit, sfp_eeprom_info["ModuleMonitorValues"][key]), \
                "Value of {}:{} format is not correct. pattern is {}".format(key,
                                                                             sfp_eeprom_info["ModuleMonitorValues"][key],
                                                                             pattern_digit_unit)


def is_support_dom(duthost, port_index):
    """
    This method is to check if cable support dom
    """
    bulk_status_str = get_transceiver_bulk_status(duthost, port_index)
    bulk_status_dict = eval(bulk_status_str)
    for k, v in bulk_status_dict.items():
        if "power" in k or "bias" in k or "temperature" in k or "voltage" in k:
            if v not in ['N/A', '0.0', 0.0, '0.0000mA']:
                return True
    return False


def get_transceiver_bulk_status(duthost, port_index):
    """
    This method is to get transceiver bulk status
    """
    cmd = """
cat << EOF > get_transceiver_bulk_status.py
import sonic_platform.platform as P
info = P.Platform().get_chassis().get_sfp({}).get_transceiver_bulk_status()
print(info)
EOF
""".format(port_index)
    duthost.shell(cmd)
    return duthost.command("python3 get_transceiver_bulk_status.py")["stdout"]
