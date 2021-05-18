import re
import allure
import pytest
import logging

logger = logging.getLogger()


@pytest.fixture(scope='session')
def disable_ssh_client_alive_interval(topology_obj):
    """
    Pytest fixture which are disabling ClientAliveInterval(set it to 0), for prevent SSH session disconnection
    after 15 min without activity. After chagned sshd config, we do service ssh restart and reconnect ssh engine
    :param topology_obj: topology object fixture
    """
    engine = topology_obj.players['dut']['engine']
    engine.run_cmd('sudo sed -i "s/ClientAliveInterval 900/ClientAliveInterval 0/g" /etc/ssh/sshd_config')
    engine.run_cmd('sudo service ssh restart')
    engine.disconnect()
    engine.get_engine()

    yield

    engine.run_cmd('sudo sed -i "s/ClientAliveInterval 0/ClientAliveInterval 900/g" /etc/ssh/sshd_config')
    engine.run_cmd('sudo service ssh restart')


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


def get_dut_loopbacks(topology_obj):
    """
    :return: a list of ports tuple which are connected as loopbacks on dut
    i.e,
    [('Ethernet4', 'Ethernet8'), ('Ethernet40', 'Ethernet36'), ...]
    """
    dut_loopbacks = {}
    pattern = r"dut-lb\d+-\d"
    for alias, connected_alias in topology_obj.ports_interconnects.items():
        if dut_loopbacks.get(connected_alias):
            continue
        if re.search(pattern, alias):
            dut_loopbacks[alias] = connected_alias
    dut_loopback_aliases_list = dut_loopbacks.items()
    return list(map(lambda lb_tuple: (topology_obj.ports[lb_tuple[0]], topology_obj.ports[lb_tuple[1]]),
                    dut_loopback_aliases_list))


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


def cleanup(cleanup_list):
    """
    execute all the functions in the cleanup list
    :return: None
    """
    for func, args in cleanup_list:
        func(*args)


def save_configuration_and_reboot(dut_engine, cli_object, ports, cleanup_list, reboot_type):
    """
    save configuration and reboot
    :param dut_engine: ssh connection to dut
    :param cli_object: cli object of dut
    :param ports: list of interfaces to validate after reboot
    :param cleanup_list: a list of functions to be cleaned after the test
    :param reboot_type: i.e reboot/warm-reboot/fast-reboot
    :return: none
    """
    with allure.step('Save configuration and reboot with type: {}'.format(reboot_type)):
        save_configuration(dut_engine, cli_object, cleanup_list)
        logger.info("Reload switch with reboot type: {}".format(reboot_type))
        cli_object.general.reboot_flow(dut_engine, reboot_type=reboot_type, ports_list=ports)


def save_configuration(dut_engine, cli_object, cleanup_list):
    """
    save configuration
    :param dut_engine: ssh connection to dut
    :param cli_object: cli object of dut
    :param cleanup_list: a list of functions to be cleaned after the test
    :return: none
    """
    logger.info("saving configuration")
    cleanup_list.append((dut_engine.run_cmd, ('sudo config save -y',)))
    cli_object.general.save_configuration(dut_engine)


def compare_actual_and_expected(key, expected_val, actual_val):
    """
    :param key: a string describing what is being compared, "speed"/"status", etc...
    :param expected_val: the expected value
    :param actual_val: the actual value
    :return: raise assertion error in case values does not match
    """
    assert str(expected_val) == str(actual_val), \
        "Compared {} result failed: actual - {}, expected - {}".format(key, actual_val, expected_val)
