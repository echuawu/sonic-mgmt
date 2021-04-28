import pytest
import logging
import allure
import os
from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.cli_wrappers.linux.linux_route_clis import LinuxRouteCli


logger = logging.getLogger()
CONFIG_DB_COPP_CONFIG = '/etc/sonic/copp_cfg.json'


@pytest.fixture(autouse=True)
def ignore_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "..", "..", "..",
                                                               "tools", "loganalyzer", "reboot_loganalyzer_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


@pytest.fixture(scope='module', autouse=True)
def copp_configuration(topology_obj, engines, interfaces):
    """
    Pytest fixture which are doing configuration for test case based on copp config
    :param topology_obj: topology object fixture
    """
    logger.info('Starting CoPP Common configuration')

    host_cli_object = topology_obj.players['ha']['cli']

    dut_cli_object = topology_obj.players['dut']['cli']

    with allure.step('Check that link in UP state'):
        retry_call(SonicInterfaceCli.check_ports_status,
                   fargs=[engines.dut, [interfaces.dut_ha_1]],
                   tries=10,
                   delay=10,
                   logger=logger)

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'ips': [('192.168.1.1', '24'), ('2001:db8:5::1', '60')]}],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('192.168.1.2', '24'), ('2001:db8:5::2', '60')]}]
    }

    logger.info('Disable periodic lldp traffic')
    host_cli_object.general.stop_service(engines.ha, 'lldpad')
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    LinuxRouteCli.add_route(engines.ha, '255.255.255.255', interfaces.ha_dut_1, '32')

    logger.info('CoPP Common configuration completed')

    yield

    logger.info('Starting CoPP Common configuration cleanup')
    LinuxRouteCli.del_route(engines.ha, '255.255.255.255', interfaces.ha_dut_1, '32')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    host_cli_object.general.start_service(engines.ha, 'lldpad')

    dut_cli_object.general.load_configuration(engines.dut, CONFIG_DB_COPP_CONFIG)
    dut_cli_object.general.save_configuration(engines.dut)

    logger.info('CoPP Common cleanup completed')
