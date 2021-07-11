import random
import re
import allure
import pytest
import logging

from ngts.constants.constants import SonicConst
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.helpers import json_file_helper as json_file_helper

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


@pytest.fixture(scope='session')
def hosts_ports(engines, cli_objects, interfaces):
    hosts_ports = {engines.ha: (cli_objects.ha, [interfaces.ha_dut_1, interfaces.ha_dut_2]),
                   engines.hb: (cli_objects.hb, [interfaces.hb_dut_1, interfaces.hb_dut_2])}
    return hosts_ports


@pytest.fixture(scope='session')
@pytest.mark.usefixtures("hosts_ports")
def split_mode_supported_speeds(topology_obj, engines, cli_objects, interfaces, hosts_ports):
    """
    :param topology_obj: topology object fixture
    :param engines: setup engines fixture
    :param cli_objects: cli objects fixture
    :param interfaces: host <-> dut interfaces fixture
    :param hosts_ports: a dictionary with hosts engine, cli_object and ports
    :return: a dictionary with available breakout options on all setup ports (included host ports)
    format : {<port_name> : {<split type>: {[<supported speeds]}

    i.e,  {'Ethernet0': {1: {'100G', '50G', '40G', '10G', '25G'},
                        2: {'40G', '10G', '25G', '50G'},
                        4: {'10G', '25G'}},
          ...
          'enp131s0f1': {1: {'100G', '40G', '50G', '10G', '1G', '25G'}}}
    """
    platform_json_info = json_file_helper.get_platform_json(engines.dut, cli_objects.dut, fail_if_doesnt_exist=False)
    split_mode_supported_speeds = SonicGeneralCli.parse_platform_json(topology_obj, platform_json_info)
    for host_engine, host_info in hosts_ports.items():
        host_cli, host_ports = host_info
        for port in host_ports:
            split_mode_supported_speeds[port] = \
                {1: host_cli.interface.parse_show_interface_ethtool_status(host_engine, port)["supported speeds"]}
    return split_mode_supported_speeds


def reboot_reload_random(topology_obj, dut_engine, cli_object, ports, cleanup_list):
    """
    Do reload/or reboot by any given way (reboot, fast-reboot, warm-reboot) on dut
    :param topology_obj: topology_obj fixture
    :param dut_engine: a ssh connection to dut
    :param cli_object: a cli object of dut
    :param ports: a ports list on dut to validate after reboot
    :param cleanup_list: a list of cleanup functions that should be called in the end of the test
    :return: raise assertion error in case reload/reboot failed
    """
    supported_reboot_modes = ['reload', 'warm-reboot', 'fast-reboot', 'reboot']
    chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']
    if chip_type == "SPC2":
        supported_reboot_modes.remove('fast-reboot')
    mode = random.choice(supported_reboot_modes)
    with allure.step('Preforming {} on dut:'.format(mode)):
        logger.info('Saving Configuration and preforming {} on dut:'.format(mode))
        if mode == 'reload':
            save_configuration(dut_engine, cli_object, cleanup_list)
            cli_object.general.reload_flow(dut_engine, ports_list=ports)
        else:
            save_configuration_and_reboot(dut_engine, cli_object, ports, cleanup_list, reboot_type=mode)
