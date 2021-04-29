import re

from ngts.constants.constants import ConfigDbJsonConst
from ngts.helpers.interface_helpers import get_alias_number, get_speed_in_G_format
from ngts.tests.nightly.conftest import get_speed_option_by_breakout_modes


def get_breakout_mode_configured_speed(breakout_mode):
    """
    this function will return the speed that will be configured on the port be the breakout mode.
    :param breakout_mode: i,e. '4x25G[10G,1G]'
    :return: return 25G
    """
    return re.search(r"\dx(\d+G)\[[\d+G,]+\]|\dx(\d+G)", breakout_mode).group(1)


def get_breakout_mode_by_speed_conf(breakout_modes_list, port_speed):
    """
    :param breakout_modes_list: i.e, ['4x25G[10G,1G]', '4x1G']
    :param port_speed: i.e, 25G
    :return: the breakout mode that configures the port_speed, in this case '4x25G[10G,1G]'
    """
    for breakout_mode in breakout_modes_list:
        brk_mode_configured_speed = get_breakout_mode_configured_speed(breakout_mode)
        if brk_mode_configured_speed == port_speed:
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
            is_first_split_port = bool(re.match('etp\d+a', port_alias))
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
    split_mode_supported_speeds = {1: set(), 2: set(), 4: set()}
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
    split_mode_supported_breakout_modes = {1: set(), 2: set(), 4: set()}
    for breakout_mode in breakout_modes:
        breakout_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        if re.search(breakout_pattern, breakout_mode):
            breakout_num, _ = breakout_mode.split("x")
            split_mode_supported_breakout_modes[int(breakout_num)].add(breakout_mode)
    return split_mode_supported_breakout_modes
