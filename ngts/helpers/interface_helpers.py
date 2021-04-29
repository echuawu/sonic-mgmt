import re


def get_speed_in_G_format(speed_in_kb):
    """
    :param speed_in_kb: i.e, 25000
    :return: speed in G format, i.e, 25G
    """
    return "{}G".format(int(int(speed_in_kb)/1000))


def get_alias_number(port_alias):
    """
    :param port_alias:  the sonic port alias, e.g. 'etp1'
    :return: the number in the alias, e.g. 1
    """
    return re.search('etp(\d+)', port_alias).group(1)
