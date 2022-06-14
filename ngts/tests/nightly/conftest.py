import random
import re
import allure
import pytest
import logging

from retry.api import retry_call
from ngts.constants.constants import InterfacesTypeConstants

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


@pytest.fixture()
def cleanup_list():
    """
    Fixture to execute cleanup after a test has run
    :return: None
    """
    cleanup_list = []

    yield cleanup_list

    logger.info("------------------test teardown------------------")
    cleanup(cleanup_list)


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


def save_configuration_and_reboot(topology_obj, dut_engine, cli_object, ports, cleanup_list, reboot_type):
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
        cli_object.general.reboot_reload_flow(r_type=reboot_type, topology_obj=topology_obj, ports_list=ports)


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
    cli_object.general.save_configuration()


def compare_actual_and_expected(key, expected_val, actual_val):
    """
    :param key: a string describing what is being compared, "speed"/"status", etc...
    :param expected_val: the expected value
    :param actual_val: the actual value
    :return: raise assertion error in case values does not match
    """
    assert str(expected_val) == str(actual_val), \
        "Compared {} result failed: actual - {}, expected - {}".format(key, actual_val, expected_val)


def convert_speed_format_to_m_speed(split_mode_supported_speeds):
    """
    Convert speed value from platform.json to {speed_value}M - which is used by the test
    :param split_mode_supported_speeds: dictionary, result of parsing platform.json file
    :return: split_mode_supported_speeds with updated speeds in M format, i.e,
    {'Ethernet0': {1: ('100M', '1000M', '10M'),2: (), 4: ()},...}
    """
    split_mode = 1
    for iface, split_speeds_info in split_mode_supported_speeds.items():
        for speed in split_speeds_info[split_mode]:
            if re.match(r"\d+$", speed):
                split_mode_supported_speeds[iface][split_mode].remove(speed)
                split_mode_supported_speeds[iface][split_mode].add(f"{speed}M")


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
            cli_object.general.reload_flow(ports_list=ports)
        else:
            save_configuration_and_reboot(topology_obj, dut_engine, cli_object, ports, cleanup_list, reboot_type=mode)


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
    return cli_objects.dut.interface.get_interfaces_speed(interfaces_list=ports)


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


@pytest.fixture(scope='session')
def interfaces_status_dict(engines, cli_objects):
    """
    Get and parse show interfaces status output
    :param engines: engines fixture
    :param cli_objects:  cli objects fixture
    :return: dictionary with parsed output
    """
    interfaces_status_dict = cli_objects.dut.interface.parse_interfaces_status()
    return interfaces_status_dict


@pytest.fixture(scope='session')
def physical_interfaces_types_dict(interfaces_status_dict):
    """
    Get physical interfaces type dictionary
    :param interfaces_status_dict: dictionary with parsed output of "show interfaces status"
    :return: dictionary, example: {"Ethernet0": "RJ45", "Ethernet1": "RJ45", ...}
    """
    interfaces_types_dict = {}
    for port, port_status in interfaces_status_dict.items():
        interfaces_types_dict[port] = port_status['Type']
    return interfaces_types_dict


@pytest.fixture(scope='session')
def rj45_ports_list(physical_interfaces_types_dict):
    """
    Get rj45 ports list
    :param physical_interfaces_types_dict: dictionary, example: {"Ethernet0": "RJ45", "Ethernet1": "RJ45", ...}
    :return: list with rj45 ports, example: ['Ethernet0', 'Ethernet1', 'Ethernet2'...]
    """
    rj_45_ports_list = []
    for port in physical_interfaces_types_dict:
        if physical_interfaces_types_dict[port] == InterfacesTypeConstants.RJ45:
            rj_45_ports_list.append(port)

    return rj_45_ports_list


@pytest.fixture(scope='session')
def sfp_ports_list(physical_interfaces_types_dict):
    """
    Get SFP ports list
    :param physical_interfaces_types_dict: dictionary, example: {"Ethernet0": "RJ45", "Ethernet1": "QSFP", ...}
    :return: list with SFP ports, example: ['Ethernet1', 'Ethernet2'...]
    """
    spf_ifaces_list = []
    for port in physical_interfaces_types_dict:
        if 'SFP' in physical_interfaces_types_dict[port]:
            spf_ifaces_list.append(port)

    return spf_ifaces_list
