"""

conftest.py

Defines the methods and fixtures which will be used by pytest for only canonical setups.

"""

import pytest
import logging
from dotted_dict import DottedDict

from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.tests.push_build_tests.system.test_cpu_ram_hdd_usage import get_cpu_usage_and_processes

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def show_version(engines):
    """
    Print show version output to logs
    :param engines: engines fixture
    """
    SonicGeneralCli.show_version(engines.dut)


@pytest.fixture(scope='session')
def engines(topology_obj):
    engines_data = DottedDict()
    engines_data.dut = topology_obj.players['dut']['engine']
    engines_data.ha = topology_obj.players['ha']['engine']
    engines_data.hb = topology_obj.players['hb']['engine']
    return engines_data


@pytest.fixture(scope='session')
def cli_objects(topology_obj):
    cli_obj_data = DottedDict()
    cli_obj_data.dut = topology_obj.players['dut']['cli']
    cli_obj_data.ha = topology_obj.players['ha']['cli']
    cli_obj_data.hb = topology_obj.players['hb']['cli']
    return cli_obj_data


@pytest.fixture(scope='session')
def interfaces(topology_obj):
    interfaces_data = DottedDict()
    interfaces_data.ha_dut_1 = topology_obj.ports['ha-dut-1']
    interfaces_data.ha_dut_2 = topology_obj.ports['ha-dut-2']
    interfaces_data.hb_dut_1 = topology_obj.ports['hb-dut-1']
    interfaces_data.hb_dut_2 = topology_obj.ports['hb-dut-2']
    interfaces_data.dut_ha_1 = topology_obj.ports['dut-ha-1']
    interfaces_data.dut_ha_2 = topology_obj.ports['dut-ha-2']
    interfaces_data.dut_hb_1 = topology_obj.ports['dut-hb-1']
    interfaces_data.dut_hb_2 = topology_obj.ports['dut-hb-2']
    return interfaces_data


@pytest.fixture(scope='session')
def ha_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-1
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.ha, interfaces.ha_dut_1)


@pytest.fixture(scope='session')
def ha_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: ha-dut-2
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.ha, interfaces.ha_dut_2)


@pytest.fixture(scope='session')
def hb_dut_1_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-1
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.hb, interfaces.hb_dut_1)


@pytest.fixture(scope='session')
def hb_dut_2_mac(engines, interfaces):
    """
    Pytest fixture which are returning mac address for link: hb-dut-2
    """
    return LinuxMacCli.get_mac_address_for_interface(engines.hb, interfaces.hb_dut_2)


@pytest.fixture(scope='session')
def dut_ha_1_mac(engines, cli_objects, topology_obj):
    """
    Pytest fixture which are returning mac address for link: dut-ha-1
    """
    return cli_objects.dut.mac.get_mac_address_for_interface(engines.dut, topology_obj.ports['dut-ha-1'])


@pytest.fixture(scope='session')
def dut_hb_2_mac(engines, cli_objects, topology_obj):
    """
    Pytest fixture which are returning mac address for link: dut-hb-2
    """
    return cli_objects.dut.mac.get_mac_address_for_interface(engines.dut, topology_obj.ports['dut-hb-2'])


@pytest.fixture(autouse=True)
def get_ram_usage_for_syncd_process(engines):
    """
    Pytest fixture which prints RAM usage for syncd process
    """
    yield

    process = 'syncd'
    total_cpu_usage, cpu_usage_per_process_dict = get_cpu_usage_and_processes(engines.dut)

    try:
        process_pid = cpu_usage_per_process_dict[process]['pid']
        cat_smaps_cmd = "sudo cat /proc/{}/smaps".format(process_pid)
        get_ram_usage_cmd = cat_smaps_cmd + "| grep Pss | awk '{Total+=$2} END {print Total/1024}'"
        used_ram_mb = float(engines.dut.run_cmd(get_ram_usage_cmd))
        logger.info('Process: {} used {} Mb of RAM'.format(process, used_ram_mb))

    except KeyError:
        logger.error('Can not find RAM usage for process: {} - process is not running'.format(process))
