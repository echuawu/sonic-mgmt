import pytest
import logging
import allure
import os
from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.cli_wrappers.sonic.sonic_counterpoll_clis import SonicCounterpollCli


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
def copp_configuration(topology_obj, engines, interfaces, cli_objects):
    """
    Pytest fixture which are doing configuration for test case based on copp config
    :param topology_obj: topology object fixture
    """
    logger.info('Starting CoPP Common configuration')

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
    cli_objects.ha.general.stop_service(engines.ha, 'lldpad')
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)

    logger.info('CoPP Common configuration completed')

    yield

    logger.info('Starting CoPP Common configuration cleanup')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    cli_objects.ha.general.start_service(engines.ha, 'lldpad')

    cli_objects.dut.general.load_configuration(engines.dut, CONFIG_DB_COPP_CONFIG)
    cli_objects.dut.general.save_configuration(engines.dut)

    logger.info('CoPP Common cleanup completed')


@pytest.fixture(scope='module', autouse=True)
def flowcnt_trap_configuration(engines, sonic_version):
    """
    Pytest fixture which are doing configuration for test case based on flow counters config
    :param engines: engines fixture
    """
    if is_trap_counters_supported(sonic_version):
        SonicCounterpollCli.enable_flowcnt_trap(engines.dut)

    yield

    if is_trap_counters_supported(sonic_version):
        SonicCounterpollCli.disable_flowcnt_trap(engines.dut)


def is_trap_counters_supported(sonic_version):
    return 'master' in sonic_version
