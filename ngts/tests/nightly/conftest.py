import random
import re
import allure
import pytest
import logging

from retry.api import retry_call
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
    for cleanup_item in cleanup_list:
        if len(cleanup_item) == 3:  # if **kwargs available
            func, args, kwargs = cleanup_item
            func(*args, **kwargs)
        else:
            func, args = cleanup_item
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
        cli_object.general.reboot_reload_flow(dut_engine, r_type=reboot_type, ports_list=ports)


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
    split_mode_supported_speeds = SonicGeneralCli().parse_platform_json(topology_obj, platform_json_info)

    # TODO: code below to convert 100(which we get from platform.json on DUT) to 100M, which is used by the test
    convert_100_to_100m_speed(split_mode_supported_speeds)

    for host_engine, host_info in hosts_ports.items():
        host_cli, host_ports = host_info
        for port in host_ports:
            port_ethtool_status = host_cli.interface.parse_show_interface_ethtool_status(host_engine, port)
            port_supported_speeds = port_ethtool_status["supported speeds"]
            if '1G' in port_supported_speeds:
                port_supported_speeds.remove('1G')
                # TODO: bug 2966698 fix only on latest kernel - kernel update is unplanned for now
                # TODO: please remove this if statement once issue is resolved
            split_mode_supported_speeds[port] = \
                {1: port_supported_speeds}
    return split_mode_supported_speeds


def convert_100_to_100m_speed(split_mode_supported_speeds):
    """
    Convert value 100 which we get from platform.json on DUT to 100M - which is used by the test
    :param split_mode_supported_speeds: dictionary, result of parsing platform.json file
    :return:
    """
    original_value = '100'
    new_value = '100M'
    split_mode = 1
    for iface, split_info in split_mode_supported_speeds.items():
        if original_value in split_info[split_mode]:
            split_mode_supported_speeds[iface][split_mode].remove(original_value)
            split_mode_supported_speeds[iface][split_mode].add(new_value)


def reboot_reload_random(topology_obj, dut_engine, cli_object, ports, cleanup_list, simx=False):
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
    if simx:
        supported_reboot_modes = ['reload', 'reboot']
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


@pytest.fixture()
def skip_if_active_optical_cable(cable_compliance_info):
    """
    Fixture that skips test execution in case setup has Active Optical Cable
    """
    if re.search(r"Active\s+Optical\s+Cable", cable_compliance_info, re.IGNORECASE):
        pytest.skip("This test is not supported because setup has Active Optical Cable")


@pytest.fixture(scope='session')
def cable_compliance_info(topology_obj, platform_params, engines):
    if "simx" not in platform_params.setup_name:
        cables_output = retry_call(check_cable_compliance_info_updated_for_all_port,
                                   fargs=[topology_obj, engines], tries=12, delay=10, logger=logger)
    else:
        cables_output = "No cables info on simx setups"
    return cables_output


def check_cable_compliance_info_updated_for_all_port(topology_obj, engines):
    ports = topology_obj.players_all_ports['dut']
    logger.info("Verify cable compliance info is updated for all ports")
    compliance_info = engines.dut.run_cmd("show interfaces transceiver eeprom")
    for port in ports:
        if re.search("{}: SFP EEPROM is not applicable for RJ45 port".format(port), compliance_info):
            continue
        if not re.search("{}: SFP EEPROM detected".format(port), compliance_info):
            raise AssertionError("Cable Information for port {} is not Loaded by"
                                 " \"show interfaces transceiver eeprom\" cmd".format(port))
    return compliance_info


@pytest.fixture(scope='session')
def dut_ports_default_speeds_configuration(topology_obj, engines, cli_objects):
    ports = topology_obj.players_all_ports['dut']
    return cli_objects.dut.interface.get_interfaces_speed(engines.dut, interfaces_list=ports)


@pytest.fixture(scope='session')
def dut_ports_interconnects(topology_obj):
    """
    :return: a dictionary with all the Noga connectivity for dut ports, i.e.
    {
    'Ethernet4': 'Ethernet8'
    }
    """
    dut_ports_interconnects_dict = {}
    for port_noga_alias, neighbor_port_noga_alias in topology_obj.ports_interconnects.items():
        alias_prefix = port_noga_alias.split('-')[0]
        if alias_prefix == 'dut':
            port = topology_obj.ports[port_noga_alias]
            neighbor_port = topology_obj.ports[neighbor_port_noga_alias]
            dut_ports_interconnects_dict.update({port: neighbor_port})
    return dut_ports_interconnects_dict
