import argparse
import json
import os
import pandas as pd
from collections import OrderedDict


SPC3_SI_PARAMS_EXCEL = 'spc3_si_params.xls'
SPC4_SI_PARAMS_EXCEL = 'spc4_si_params.xls'

GLOBAL_MEDIA_SETTINGS = 'GLOBAL_MEDIA_SETTINGS'
SPC3_PORT_RANGE = '1-32'
SPC4_PORT_RANGE = '1-64'
DEFAULT = 'Default'
GROUP_ID = 0

SPC3 = 'spc3'
SPC4 = 'spc4'

PORT = 'port'
MODULE = 'module'

NUM_OF_LANES = 8
LANE_PREFIX = 'lane'
SPEED_PREFIX = 'speed:'
MODULE_LANE_SPEED_SUFFIX = 'G_SPEED'

APPLICATION_ADVERTISEMENT = 'Application Advertisement'
IDENTIFIER = 'Identifier'
SPECIFICATION_COMPLIANCE = 'Specification compliance'
EEPROM_DATA_TO_EXTRACT = [APPLICATION_ADVERTISEMENT, IDENTIFIER, SPECIFICATION_COMPLIANCE]

FILTERS_BY_SPC = {
    SPC3: {'Tech': 'Active', 'device': 'Firebird'},
    SPC4: {'Tech': 'Active', 'device': 'Albatross'}
}

SPEED = 'SPEED'
LANES = 'LANES'

LANE_SPEED_TO_GENERATION = {
    100: 'NDR',
    50: 'HDR',
    25: 'EDR',
    10: 'FDR',
    2.5: 'SDR',
    1: 'SGMII'
}

SPC3_EXCEL_SPEED_COLUMN_TO_SPEED_ALIAS = {
    'SDR': '10GbE',
    'FDR': 'FDR/56GbE',
    'EDR': 'EDR/100GbE',
    'HDR': 'HDR/200GbE'
}

APPLICATIONS_DATA_BY_SFF_SPEC = {
    # Ethernet
    '1000BASE-CX':      {SPEED: 1, LANES: 1},
    'XAUI':             {SPEED: 12, LANES: 4},
    '25GAUI':           {SPEED: 25, LANES: 1},
    'XLAUI':            {SPEED: 40, LANES: 4},
    'XLPPI':            {SPEED: 40, LANES: 4},
    'LAUI-2':           {SPEED: 50, LANES: 2},
    '50GAUI-2':         {SPEED: 50, LANES: 2},
    '50GAUI-1':         {SPEED: 50, LANES: 1},
    'CAUI-4':           {SPEED: 100, LANES: 4},
    '100GAUI-4 C2M':    {SPEED: 100, LANES: 4},
    '100GAUI-2':        {SPEED: 100, LANES: 2},
    '100GAUI-1':        {SPEED: 100, LANES: 1},
    '200GAUI-8':        {SPEED: 200, LANES: 8},
    '200GAUI-4':        {SPEED: 200, LANES: 4},
    '200GAUI-2':        {SPEED: 200, LANES: 2},
    '400GAUI-16':       {SPEED: 400, LANES: 16},
    '400GAUI-8':        {SPEED: 400, LANES: 8},
    '400GAUI-4-S':      {SPEED: 400, LANES: 4},
    '400GAUI-4-L':      {SPEED: 400, LANES: 4},
    '800G':             {SPEED: 800, LANES: 8},
    # Reserved
    '10GBASE-CX4':      {SPEED: 12, LANES: 4},
    '25GBASE-CR':       {SPEED: 25, LANES: 1},
    '40GBASE-CR4':      {SPEED: 40, LANES: 4},
    '50GBASE-CR2':      {SPEED: 50, LANES: 5},
    '50GBASE-CR':       {SPEED: 50, LANES: 1},
    '100GBASE-CR10':    {SPEED: 100, LANES: 10},
    '100GBASE-CR4':     {SPEED: 100, LANES: 4},
    '100GBASE-CR2':     {SPEED: 100, LANES: 2},
    '100GBASE-CR1':     {SPEED: 100, LANES: 1},
    '200GBASE-CR4':     {SPEED: 200, LANES: 4},
    '200GBASE-CR2':     {SPEED: 200, LANES: 2},
    '400G':             {SPEED: 400, LANES: 8},
    '400GBASE-CR4':     {SPEED: 400, LANES: 4},
    '800G-ETC-CR8':     {SPEED: 800, LANES: 8},
}

PORTS_SI_PARAM_NAMES_EXCEL_TO_JSON = {
    SPC3: {
        'ob_amp': 'idriver',
        'ob_pre': 'pre1',
        'ob_pre2': 'pre2',
        'ob_main': 'main',
        'ob_post': 'post1',
        'ob_alev': 'ob_alev_out',
        'ob_m2lp': 'ob_m2lp',
        'obplev': 'obplev',
        'obnlev': 'obnlev',
        'regn_bfm1p': 'regn_bfm1p',
        'regp_bfm1n': 'regn_bfm1n'
    },
    SPC4: {
        'fir_amp': 'fir_amp',
        'fir_pre1': 'fir_pre1',
        'fir_pre2': 'fir_pre2',
        'fir_pre3': 'fir_pre3',
        'fir_main': 'fir_main',
        'fir_post1': 'fir_post1'
    }
}

MODULE_SI_PARAM_NAMES_EXCEL_TO_JSON = {
    SPC3: {
        'cmis_amp': 'OutputAmplitudeTargetRx',
        'cmis_pre': 'OutputEqPreCursorTargetRx',
        'cmis_post': 'OutputEqPostCursorTargetRx'
    },
    SPC4: {
        'rx_out_amp': 'OutputAmplitudeTargetRx',
        'rx_out_emp_pre': 'OutputEqPreCursorTargetRx',
        'rx_out_emp_post': 'OutputEqPostCursorTargetRx'
    }
}

# This dictionary maps between EEPROM entries for the identifier field and their corresponding representation in JSON.
# The JSON identifier representation can be usually derived from the EEPROM, but that is not always the case.
EEPROM_IDENTIFIER_TO_JSON_IDENTIFIER = {'OSFP 8X Pluggable Transceiver': 'OSFP-8X'}


def parse_args():
    """
    @summary: generate the ArgumentParser, parse arguments and return them
    """
    parser = argparse.ArgumentParser(description='Create Independent Module jsons')
    parser.add_argument('-s', '--spc', type=str, choices=['spc3', 'spc4'], help="spectrum3 or spectrum4 indication", required=True)
    parser.add_argument('-e', '--eeprom_input', type=str, help="Path to modules EEPROM input data")
    parser.add_argument('-m', '--mode', type=str, choices=['port', 'module'], help="The required IM json - 'port' or 'module' SI data", required=True)
    return parser.parse_args()


def get_groups():
    lanes_range = SPC3_PORT_RANGE if args.spc == SPC3 else SPC4_PORT_RANGE
    return lanes_range


def get_excel_row_id(speed):
    row_id = None
    if args.spc == SPC4:
        if speed in LANE_SPEED_TO_GENERATION:
            row_id = LANE_SPEED_TO_GENERATION[speed]
    elif args.spc == SPC3:
        if speed in LANE_SPEED_TO_GENERATION and LANE_SPEED_TO_GENERATION[speed] in SPC3_EXCEL_SPEED_COLUMN_TO_SPEED_ALIAS:
            row_id = SPC3_EXCEL_SPEED_COLUMN_TO_SPEED_ALIAS[LANE_SPEED_TO_GENERATION[speed]]
    return row_id


def build_si_param_section(df):
    if args.mode == PORT:
        media_key_to_lane_speed_keys = get_media_key_to_lane_peed_keys_mapping()
        return get_port_si_params(df, media_key_to_lane_speed_keys)
    elif args.mode == MODULE:
        return get_module_si_params(df)


def build_json_dict(si_params):
    ports_range = get_groups()
    json_dict = {
        GLOBAL_MEDIA_SETTINGS: {
            ports_range: si_params
        }
    }
    return json_dict


def export_to_json(json_dict):
    file_name = 'media_settings.json' if args.mode == 'port' else 'optics_si_settings.json'
    with open(file_name, "w") as json_file:
        json.dump(json_dict, json_file, indent=4)
        print("The {} file has been successfully generated".format(file_name))


def get_filtered_df():
    si_params_excel = SPC3_SI_PARAMS_EXCEL if args.spc == SPC3 else SPC4_SI_PARAMS_EXCEL
    si_params_sheet_name = 'TX_DB_HDR' if args.spc == 'spc3' else 'TX_DB'
    df = pd.read_excel(si_params_excel, sheet_name=si_params_sheet_name)
    filtered_df = df
    for k, v in FILTERS_BY_SPC[args.spc].items():
        filtered_df = filtered_df.loc[df[k] == v]
    return filtered_df


# ----------------------------------------------------- Port SI -----------------------------------------------------
def read_eeprom_data_from_file(eeprom_text_file=''):
    eeprom_text_data = []
    if eeprom_text_file:
        if os.path.isfile(eeprom_text_file):
            with open(eeprom_text_file, "r") as eeprom_text_file_fd:
                for line in eeprom_text_file_fd:
                    eeprom_text_data.append(line.strip())
    return eeprom_text_data


def extract_data_from_eeprom(eeprom_data_list, delimiter=':'):
    extracted_data_list = []
    extracted_data = {}
    i = 0

    for line in eeprom_data_list:
        if "SFP EEPROM detected" in line:
            i += 1
            if i > 1:
                extracted_data_list.append(extracted_data)
                extracted_data = {}
            continue
        if delimiter in line:
            line_splitted = line.split(delimiter)
            spec_comp_processing = False
            for key in EEPROM_DATA_TO_EXTRACT:
                if key in line_splitted[0]:
                    # only Specification compliance needs special treatment over several lines
                    if key in APPLICATION_ADVERTISEMENT:
                        extracted_data[key] = [line_splitted[1].split()[0].strip()]
                        spec_comp_processing = True
                    elif key in IDENTIFIER:
                        id_from_eeprom = line_splitted[1].strip()
                        extracted_data[key] = EEPROM_IDENTIFIER_TO_JSON_IDENTIFIER[id_from_eeprom] if id_from_eeprom in EEPROM_IDENTIFIER_TO_JSON_IDENTIFIER else line_splitted[1].split()[0].strip()
                        pass
                    else:
                        extracted_data[key] = line_splitted[1].strip()
        elif spec_comp_processing:
            extracted_data[APPLICATION_ADVERTISEMENT].append(line.split()[0].strip())
    extracted_data_list.append(extracted_data)
    return extracted_data_list


def generate_media_keys_dict(extracted_data_dict_list=None):
    media_keys_dict = {}
    for extracted_data_dict in extracted_data_dict_list:
        media_key_spec_identifier = '-'.join([extracted_data_dict[EEPROM_DATA_TO_EXTRACT[1]]
                                                 , extracted_data_dict[EEPROM_DATA_TO_EXTRACT[2]]])
        if media_key_spec_identifier not in media_keys_dict:
            media_keys_dict[media_key_spec_identifier] = set()
        speeds = extracted_data_dict[EEPROM_DATA_TO_EXTRACT[0]]
        for speed in speeds:
            media_keys_dict[media_key_spec_identifier].add(speed)
    return media_keys_dict


def get_media_key_to_lane_peed_keys_mapping():

    if args.eeprom_input:
        eeprom_data = read_eeprom_data_from_file(args.eeprom_input)
        extracted_data_dict_list = extract_data_from_eeprom(eeprom_data)
        media_key_spec_identifiers = generate_media_keys_dict(extracted_data_dict_list)
        return media_key_spec_identifiers
    else:
        raise FileNotFoundError("The eeprom data file is missing.")


def get_application_lane_speed(application):
    lane_speed = None
    if application in APPLICATIONS_DATA_BY_SFF_SPEC:
        application_data = APPLICATIONS_DATA_BY_SFF_SPEC[application]
        lane_speed = application_data[SPEED] // application_data[LANES]
    return lane_speed


def decimal_to_hexadecimal(decimal_value):
    width = 8
    if decimal_value >= 0:
        return format(decimal_value, '#0{}x'.format(width + 2))
    else:   # Negative numbers are converted to two's complement representation
        positive_value = abs(decimal_value)
        complement_value = (1 << (width * 4)) - positive_value
        return format(complement_value, '#0{}x'.format(width))


def get_port_single_param_values(param_value):
    param_dict = OrderedDict()
    for lane in range(NUM_OF_LANES):
        lane_str = '{}{}'.format(LANE_PREFIX, lane)
        param_dict[lane_str] = param_value
    return param_dict


def positive_to_negative(value):
    return -abs(value)


def get_port_json_data(excel_row_dict):
    json_data = {}
    si_param_names = PORTS_SI_PARAM_NAMES_EXCEL_TO_JSON[args.spc]
    for col in excel_row_dict:
        if col in si_param_names:
            param_name_excel = col
            param_name_json = PORTS_SI_PARAM_NAMES_EXCEL_TO_JSON[args.spc][param_name_excel]

            param_val_excel = int(excel_row_dict[col])
            json_value = param_val_excel

            # SPC3 conversions
            if param_name_excel == 'ob_pre':
                json_value = positive_to_negative(param_val_excel)
            elif param_name_excel == 'ob_m2lp':
                json_value = param_val_excel - 10
            elif param_name_excel == 'ob_post':
                if excel_row_dict['tx_mode'] == 0 or excel_row_dict['tx_mode'] == 2:
                    json_value = positive_to_negative(param_val_excel)
                elif excel_row_dict['tx_mode'] == 5:
                    json_value = param_val_excel
            # SPC4 conversions
            elif param_name_excel == 'fir_pre3':
                json_value = positive_to_negative(param_val_excel)
            elif param_name_excel == 'fir_pre1':
                json_value = positive_to_negative(param_val_excel)
            elif param_name_excel == 'fir_post1':
                json_value = positive_to_negative(param_val_excel)

            hex_json_value = decimal_to_hexadecimal(json_value)
            json_data[param_name_json] = get_port_single_param_values(hex_json_value)

    return json_data


def get_port_si_params(df, media_key_to_lane_speed_keys):
    si_params = {}
    for media_key, applications in media_key_to_lane_speed_keys.items():
        media_key_si_params = {}
        for application in applications:
            lane_speed = get_application_lane_speed(application)
            if lane_speed is None:
                continue
            row_id = get_excel_row_id(lane_speed)
            application_si_excel_data = df.loc[(df['speed / protocol'] == row_id) & (df['group'] == GROUP_ID)]
            application_si_excel_data_dict = application_si_excel_data.to_dict(orient='records')[0]
            application_si_json_data = get_port_json_data(application_si_excel_data_dict)

            application_json_str = SPEED_PREFIX + application
            media_key_si_params[application_json_str] = application_si_json_data
        si_params[media_key] = media_key_si_params
    return si_params
# ----------------------------------------------------- Port SI -----------------------------------------------------


# ---------------------------------------------------- Module SI ----------------------------------------------------
def get_module_single_param_values(attribute, param_value):
    param_dict = OrderedDict()
    for lane in range(1, NUM_OF_LANES + 1):
        lane_str = '{}{}'.format(attribute, lane)
        param_dict[lane_str] = param_value
    return param_dict


def get_module_json_data(excel_row_dict):
    json_data = {}
    si_param_names = MODULE_SI_PARAM_NAMES_EXCEL_TO_JSON[args.spc]
    for col in excel_row_dict:
        if col in si_param_names:
            param_name_excel = col
            param_name_json = MODULE_SI_PARAM_NAMES_EXCEL_TO_JSON[args.spc][param_name_excel]
            param_val_excel = int(excel_row_dict[col])
            json_value = param_val_excel
            json_data[param_name_json] = get_module_single_param_values(param_name_json, json_value)

    return json_data


def get_module_si_params(df):
    si_params = {}
    for supported_speed, _ in LANE_SPEED_TO_GENERATION.items():
        lane_speed_si_params = {}
        row_id = get_excel_row_id(supported_speed)
        if not row_id:
            continue
        generation_si_excel_data = df.loc[(df['speed / protocol'] == row_id) & (df['group'] == GROUP_ID)]
        if generation_si_excel_data.empty:
            continue
        generation_si_excel_data_dict = generation_si_excel_data.to_dict(orient='records')[0]
        application_si_json_data = get_module_json_data(generation_si_excel_data_dict)

        lane_speed_str = str(supported_speed) + MODULE_LANE_SPEED_SUFFIX
        lane_speed_si_params[DEFAULT] = application_si_json_data
        si_params[lane_speed_str] = lane_speed_si_params
    return si_params
# ---------------------------------------------------- Module SI ----------------------------------------------------


if __name__ == '__main__':
    args = parse_args()
    df = get_filtered_df()
    si_params_section = build_si_param_section(df)
    json_dict = build_json_dict(si_params_section)
    export_to_json(json_dict)

