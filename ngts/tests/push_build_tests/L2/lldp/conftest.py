import pytest
import logging
import os
from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def lldp_configuration(topology_obj):
    """
    :param topology_obj: topology object fixture
    """
    logger.info('Enable LLDP on hosts')
    hosts_aliases = ['ha', 'hb']
    for host_alias in hosts_aliases:
        host_engine = topology_obj.players[host_alias]['engine']
        cli_object = topology_obj.players[host_alias]['cli']
        if not cli_object.lldp.is_lldp_enabled_on_host(host_engine):
            cli_object.lldp.enable_lldp_on_host(host_engine)
            # to prevent advertising the same mac on an interfaces,
            # need to restart ports status after lldp enbling
            for port in topology_obj.players_all_ports[host_alias]:
                LinuxInterfaceCli.disable_interface(host_engine, port)
                LinuxInterfaceCli.enable_interface(host_engine, port)
    yield


@pytest.fixture(autouse=False)
def ignore_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests
    because of some expected bugs which causes exceptions in log
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "temp_log_analyzer_ignores.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)
