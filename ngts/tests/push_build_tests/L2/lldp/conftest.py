import pytest
import logging

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def lldp_configuration(topology_obj, cli_objects):
    """
    :param topology_obj: topology object fixture
    :param cli_objects: cli_objects fixture
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
                cli_object.interface.disable_interface(host_engine, port)
                cli_object.interface.enable_interface(host_engine, port)
    yield
