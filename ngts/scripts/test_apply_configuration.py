#!/usr/bin/env python
import allure
import logging
import pytest
from retry import retry
from ngts.constants.constants import SonicConst

logger = logging.getLogger()


@pytest.mark.reboot_reload
@pytest.mark.disable_loganalyzer
@allure.title('Apply Sonic Basic Configuration')
def test_apply_basic_conf(topology_obj, setup_name, platform_params, is_simx):
    """
    This script will apply basic configuration on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform_params: platform_params fixture
    :return: raise assertion error in case of script failure
    """
    try:
        cli_object = topology_obj.players['dut']['cli']
        dut_engine = topology_obj.players['dut']['engine']
        configure_machine_conf(dut_engine, is_simx, platform_params)
        timezone = "Israel"
        with allure.step("Set dut timezone to {}".format(timezone)):
            dut_engine.run_cmd('sudo timedatectl set-timezone {}'.format(timezone), validate=True)
        with allure.step("Apply port_config.ini and config_db.json"):
            require_to_reload_before_qos = require_to_configure_machine_conf(is_simx, platform_params.platform)
            cli_object.general.apply_basic_config(topology_obj, setup_name, platform_params,
                                                  reload_before_qos=require_to_reload_before_qos)

        with allure.step('Apply DNS servers configuration into /etc/resolv.conf'):
            cli_object.ip.apply_dns_servers_into_resolv_conf(is_air_setup=platform_params.setup_name.startswith('air'))

        with allure.step("Verify dockers are up after configuration is applied"):
            cli_object.general.verify_dockers_are_up(SonicConst.DOCKERS_LIST)
        with allure.step("Verify expected ports exist on DUT"):
            check_ports_exist(topology_obj, cli_object)
        with allure.step('Apply DNS servers configuration into /etc/resolv.conf'):
            cli_object.ip.apply_dns_servers_into_resolv_conf(is_air_setup=platform_params.setup_name.startswith('air'))
    except Exception as err:
        raise AssertionError(err)


def require_to_configure_machine_conf(is_simx, platform):
    """
    :param is_simx: True if setup is a simx setup, else False
    :param platform: i.e, x86_64-nvidia_sn5600_simx-r0
    :return: True if setup need to configure onie_platform/onie_machine on /host/machine.conf, else False
    """
    return is_simx and 'nvidia' in platform


def configure_machine_conf(dut_engine, is_simx, platform_params):
    """
    configure onie_platform/onie_machine on /host/machine.conf in cases where setup is
    of nvidia platform (spc4) and simx
    :param dut_engine: an ssh engine to dut
    :param is_simx: True if setup is a simx setup, else False
    :param platform_params: platform_params fixture
    :return: none
    """
    if require_to_configure_machine_conf(is_simx, platform_params.platform):
        with allure.step("Configure onie_platform/onie_machine on /host/machine.conf"):
            logger.info("Configure onie_platform/onie_machine on /host/machine.conf")
            dut_engine.run_cmd(f"sudo sed -i "
                               f"'s/.*onie_machine=.*/onie_machine="
                               f"nvidia_{platform_params.filtered_platform}_simx/' /host/machine.conf")
            dut_engine.run_cmd(f"sudo sed -i "
                               f"'s/.*onie_platform=.*/onie_platform="
                               f"x86_64-nvidia_{platform_params.filtered_platform}_simx-r0/' /host/machine.conf")


@retry(Exception, tries=6, delay=10)
def check_ports_exist(topology_obj, cli_object):
    expected_ports_list = topology_obj.players_all_ports['dut']
    ports_status = cli_object.interface.parse_interfaces_status()
    missing_ports = []
    for port in expected_ports_list:
        if not ports_status.get(port):
            missing_ports.append(port)
    if missing_ports:
        raise AssertionError(f"show interfaces status doesn't show status of ports: {missing_ports}")