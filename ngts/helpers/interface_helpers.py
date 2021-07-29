import re


def get_speed_in_G_format(speed_in_kb):
    """
    :param speed_in_kb: i.e, 25000
    :return: speed in G format, i.e, 25G
    """
    return "{}G".format(int(int(speed_in_kb) / 1000))


def get_alias_number(port_alias):
    """
    :param port_alias:  the sonic port alias, e.g. 'etp1'
    :return: the number in the alias, e.g. 1
    """
    return re.search(r'etp(\d+)', port_alias).group(1)


def get_dut_default_ports_list(topology_obj):
    base_ports_list = []
    dut_ports = topology_obj.players_all_ports['dut']
    for port_alias, port_name in topology_obj.ports.items():
        if port_name in dut_ports and not re.search(r"dut-lb-splt\d-p\d-[^1]", port_alias):
            base_ports_list.append(port_name)
    return base_ports_list


def get_lb_mutual_speed(lb, split_mode, split_mode_supported_speeds):
    """
    :param lb: a tuple of ports connected as loopback ('Ethernet52', 'Ethernet56')
    :param split_mode: the port split mode i.e, 1/2/4
    :param split_mode_supported_speeds: a dictionary with available breakout options on all setup ports
    (including host ports)
    :return: a list of mutual speeds supported by the loopback ports, i.e. ['50G', '10G', '40G', '25G', '100G']
    """
    speeds_sets = []
    for port in lb:
        speeds_sets.append(set(split_mode_supported_speeds[port][split_mode]))
    return list(set.intersection(*speeds_sets))
