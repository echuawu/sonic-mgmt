import re
from ngts.constants.constants import ConfigDbJsonConst
from ngts.helpers.interface_helpers import get_alias_number, get_speed_in_G_format
import ngts.helpers.json_file_helper as json_file_helper
from ngts.cli_util.cli_constants import SonicConstant
from ngts.constants.constants import SonicConst


def get_breakout_mode_supported_speed_list(breakout_mode):
    """
    this function will return the speed that will be configured on the port be the breakout mode.
    :param breakout_mode: i,e. '4x25G[10G,1G]'
    :return: return 25G
    """
    support_speed_list = []
    support_speed_list.append(re.search(r"\dx(\d+G)", breakout_mode).group(1))
    support_speed_list.extend(re.search(r"\dx(\d+G)\[([\d+G,]+)\]", breakout_mode).group(2).split(','))
    return support_speed_list


def get_breakout_mode_by_speed_conf(breakout_modes_list, port_speed):
    """
    :param breakout_modes_list: i.e, ['4x25G[10G,1G]', '4x1G']
    :param port_speed: i.e, 25G
    :return: the breakout mode that configures the port_speed, in this case '4x25G[10G,1G]'
    """
    for breakout_mode in breakout_modes_list:
        brk_mode_configured_speed = get_breakout_mode_supported_speed_list(breakout_mode)
        if port_speed in brk_mode_configured_speed:
            return breakout_mode
    raise Exception("Didn't find breakout mode that configured speed: {} in breakout_modes_list: {}"
                    .format(port_speed, breakout_modes_list))


def get_all_split_ports_parents(config_db_json):
    """
    this function will return a list of the ports that have breakout
    configuration configured on them and the split number the port was split(breakout) to.
    for example, if port 'Ethernet196' is breakout to 2.
    now we have 2 ports 'Ethernet196' and 'Ethernet198', but 'Ethernet196' is the port the breakout was configured on.
    so it's the parent port of the split.
    :param config_db_json: a json object of the switch config_db.json file
    :return: a list of tuples of first split port and their split number
    for example, [('Ethernet196', 2), ('Ethernet200', 2), ('Ethernet204', 4), ('Ethernet208', 4)]
    """
    dut_first_split_port_info = []
    port_info_dict = config_db_json.get(ConfigDbJsonConst.PORT)
    if port_info_dict:
        for port, port_info in port_info_dict.items():
            port_alias = port_info[ConfigDbJsonConst.ALIAS]
            is_first_split_port = bool(re.match(r'etp\d+a', port_alias))
            if is_first_split_port:
                split_num = get_split_number(config_db_json, port_alias)
                dut_first_split_port_info.append((port, split_num))
    return dut_first_split_port_info


def get_split_number(config_db_json, port_alias):
    """
    return the port split number, as the port was split to 2/4/8.
    :param config_db_json: a json object of the switch config_db.json file
    :param port_alias: the sonic port alias, e.g. 'etp1'
    :return: the number the port was split to, 2/4/8.
    """
    all_aliases = [port_info['alias'] for port_info in config_db_json[ConfigDbJsonConst.PORT].values()]
    port_alias_number = get_alias_number(port_alias)
    all_aliases_of_split_port = list(filter(lambda alias: re.search("etp{}[a-z]$".format(port_alias_number), alias),
                                            all_aliases))
    split_number = len(all_aliases_of_split_port)
    return split_number


def get_port_current_breakout_mode(config_db_json, port, split_num, parsed_platform_json_by_breakout_modes):
    port_speed = get_speed_in_G_format(config_db_json['PORT'][port]['speed'])
    supported_brk_modes = parsed_platform_json_by_breakout_modes[port][split_num]
    return get_breakout_mode_by_speed_conf(supported_brk_modes, port_speed)


def get_split_mode_supported_speeds(breakout_modes):
    """
    :param breakout_modes: a list of breakout modes, i.e. ['1x100G[50G,40G,25G,10G]',
    '2x50G[40G,25G,10G]', '4x25G[10G]']
    :return: a dictionary of supported speed for every split number option, i.e,
    {1: {'100G', '50G', '40G', '10G', '25G'},
    2: {'40G', '10G', '25G', '50G'},
    4: {'10G', '25G'}}
    """
    split_mode_supported_speeds = {1: set(), 2: set(), 4: set(), 8: set()}
    breakout_port_by_modes = get_speed_option_by_breakout_modes(breakout_modes)
    for breakout_mode, supported_speeds_list in breakout_port_by_modes.items():
        breakout_num, _ = breakout_mode.split("x")
        split_mode_supported_speeds[int(breakout_num)].update(supported_speeds_list)
    return split_mode_supported_speeds


def get_split_mode_supported_breakout_modes(breakout_modes):
    """
    :param breakout_modes: a list of breakout modes, i.e. ['1x100G[50G,40G,25G,10G]',
    '2x50G[40G,25G,10G]', '4x25G[10G]']
    :return: a dictionary of supported breakout mode for every split number option, i.e,
    {1:{'1x100G[50G,40G,25G,10G]'},
    2: {'2x50G[40G,25G,10G]'},
    4: {'4x25G[10G]'}
    """
    split_mode_supported_breakout_modes = {1: set(), 2: set(), 4: set(), 8: set()}
    for breakout_mode in breakout_modes:
        breakout_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        if re.search(breakout_pattern, breakout_mode):
            breakout_num, _ = breakout_mode.split("x")
            split_mode_supported_breakout_modes[int(breakout_num)].add(breakout_mode)
    return split_mode_supported_breakout_modes


def get_dut_breakout_modes(dut_engine, cli_object):
    """
    parsing platform breakout options and config_db.json breakout configuration.
    :return: a dictionary with available breakout options on all dut ports
    i.e,
       { 'Ethernet0' :{'index': ['1', '1', '1', '1'],
                       'lanes': ['0', '1', '2', '3'],
                       'alias_at_lanes': ['etp1a', ' etp1b', ' etp1c', ' etp1d'],
                       'breakout_modes': ['1x200G[100G,50G,40G,25G,10G,1G]',
                                          '2x100G[50G,40G,25G,10G,1G]',
                                          '4x50G[40G,25G,10G,1G]'],
                       'breakout_port_by_modes': {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
                                                  '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G[',
                                                                                 'Ethernet2': '100G'},
                                                  '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G',
                                                                            'Ethernet1': '50G',
                                                                            'Ethernet2': '50G',
                                                                            'Ethernet3': '50G'}},
                       'default_breakout_mode': '1x200G[100G,50G,40G,25G,10G,1G]'}, .....}

    """
    platform_json = json_file_helper.get_platform_json(dut_engine, cli_object)
    config_db_json = json_file_helper.get_config_db(dut_engine)
    return parse_platform_json(platform_json, config_db_json)


def parse_platform_json(platform_json_obj, config_db_json):
    """
    parsing platform breakout options and config_db.json breakout configuration.
    :param platform_json_obj: a json object of platform.json file
    :param config_db_json: a json object of config_db.json file
    :return: a dictionary with available breakout options on all dut ports
    i.e,
       { 'Ethernet0' :{'index': ['1', '1', '1', '1'],
                       'lanes': ['0', '1', '2', '3'],
                       'alias_at_lanes': ['etp1a', ' etp1b', ' etp1c', ' etp1d'],
                       'breakout_modes': ['1x200G[100G,50G,40G,25G,10G,1G]',
                                          '2x100G[50G,40G,25G,10G,1G]',
                                          '4x50G[40G,25G,10G,1G]'],
                       'breakout_port_by_modes': {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
                                                  '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G',
                                                                                 'Ethernet2': '100G'},
                                                  '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G',
                                                                            'Ethernet1': '50G',
                                                                            'Ethernet2': '50G',
                                                                            'Ethernet3': '50G'}},
                       'default_breakout_mode': '1x200G[100G,50G,40G,25G,10G,1G]'}, .....}
    """
    ports_breakout_info = {}
    breakout_options = SonicConst.BREAKOUT_MODES_REGEX
    for port_name, port_dict in platform_json_obj["interfaces"].items():
        parsed_port_dict = dict()
        parsed_port_dict[SonicConstant.INDEX] = port_dict[SonicConstant.INDEX].split(",")
        parsed_port_dict[SonicConstant.LANES] = port_dict[SonicConstant.LANES].split(",")
        breakout_modes = re.findall(breakout_options, ",".join(port_dict[SonicConstant.BREAKOUT_MODES].keys()))
        parsed_port_dict[SonicConstant.BREAKOUT_MODES] = breakout_modes
        parsed_port_dict['breakout_port_by_modes'] = get_breakout_port_by_modes(breakout_modes,
                                                                                parsed_port_dict
                                                                                [SonicConstant.LANES])
        parsed_port_dict['speeds_by_modes'] = get_speed_option_by_breakout_modes(breakout_modes)
        port_breakout_cfg = config_db_json[SonicConstant.BREAKOUT_CFG].get(port_name)
        if port_breakout_cfg:
            parsed_port_dict['default_breakout_mode'] = port_breakout_cfg[SonicConstant.BRKOUT_MODE]
        ports_breakout_info[port_name] = parsed_port_dict
    return ports_breakout_info


@staticmethod
def get_default_breakout_mode(engine_dut, cli_object, port_list):
    """
    get the default port breakout mode for port list
    :param engine_dut: ssh engine object
    :param cli_object: dut cli object
    :param port_list:port list
    :return: dictionary of the breakout mode
    """
    ports_breakout_modes = get_dut_breakout_modes(engine_dut, cli_object)
    default_ports_breakout_conf = {}
    for port in port_list:
        default_breakout_mode = ports_breakout_modes[port]['default_breakout_mode']
        if default_breakout_mode in default_ports_breakout_conf.keys():
            default_ports_breakout_conf[default_breakout_mode].append(port)
        else:
            default_ports_breakout_conf[default_breakout_mode] = [port]
    return default_ports_breakout_conf


@staticmethod
def get_breakout_mode(engine_dut, cli_object, port_list):
    """
    get the breakout mode for port list
    :param engine_dut: ssh engine object
    :param cli_object: dut cli object
    :param port_list:port list
    :return: dictionary of the breakout mode
    """
    breakout_mode = {}
    port_breakout_modes = get_dut_breakout_modes(engine_dut, cli_object)
    for port in port_list:
        supported_breakout_modes = port_breakout_modes[port]['breakout_modes']
        breakout_mode[port] = supported_breakout_modes[-1]
    return breakout_mode


def get_speed_option_by_breakout_modes(breakout_modes):
    """
    :param breakout_modes: a list of breakout modes supported by a port, i.e,
    ['1x200G[100G,50G,40G,25G,10G,1G]', '2x100G[50G,40G,25G,10G,1G]', '4x50G[40G,25G,10G,1G]']
    :return: a dictionary with speed configuration available for each breakout modes,
    i.e,
    {'1x200G[100G,50G,40G,25G,10G,1G]': [100G,50G,40G,25G,10G,1G],
    '2x100G[50G,40G,25G,10G,1G]': [50G,40G,25G,10G,1G],
    '4x50G[40G,25G,10G,1G]': [40G,25G,10G,1G]}
    """
    breakout_port_by_modes = {}
    for breakout_mode in breakout_modes:
        breakout_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        if re.search(breakout_pattern, breakout_mode):
            breakout_num, speed_conf = breakout_mode.split("x")
            speed_value = r"(\d+G)\[[\d*G,]*\]|(\d+G)"
            speed = re.match(speed_value, speed_conf).group(1)
            speeds_list_pattern = r"\d+G\[([\d*G,]*)\]|(\d+G)"
            speeds_list_str = re.match(speeds_list_pattern, speed_conf).group(1)
            speeds_list = speeds_list_str.split(sep=',')
            speeds_list.append(speed)
            breakout_port_by_modes[breakout_mode] = speeds_list
    return breakout_port_by_modes


def get_breakout_port_by_modes(breakout_modes, lanes):
    """
    :param breakout_modes: a list of breakout modes supported by a port, i.e,
    ['1x200G[100G,50G,40G,25G,10G,1G]', '2x100G[50G,40G,25G,10G,1G]', '4x50G[40G,25G,10G,1G]']
    :param lanes: a list with port lanes, i.e, for port Ethernet0 the list will be [0, 1, 2, 3]
    :return: a dictionary with ports and speed configuration result for each breakout modes,
    i.e,
    {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
    '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G',
                                   'Ethernet2': '100G'},
    '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G', 'Ethernet1': '50G',
                              'Ethernet2': '50G', 'Ethernet3': '50G'}}
    """
    breakout_port_by_modes = {}
    for breakout_mode in breakout_modes:
        breakout_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        if re.search(breakout_pattern, breakout_mode):
            breakout_num, speed_conf = breakout_mode.split("x")
            speed_value = r"(\d+G)\[[\d*G,]*\]|(\d+G)"
            speed = re.match(speed_value, speed_conf).group(1)
            num_lanes_after_breakout = len(lanes) // int(breakout_num)
            lanes_after_breakout = [lanes[idx:idx + num_lanes_after_breakout]
                                    for idx in range(0, len(lanes), num_lanes_after_breakout)]
            breakout_port = {'Ethernet{}'.format(lanes[0]): speed for lanes in lanes_after_breakout}
            breakout_port_by_modes[breakout_mode] = breakout_port
    return breakout_port_by_modes
