import pytest
import logging

from ngts.config_templates.vlan_config_template import VlanConfigTemplate

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def vlan_configuration(topology_obj, cli_objects):
    """
    :param topology_obj: topology object fixture
    :param cli_objects: cli_objects fixture
    """
    # Ports which will be used in test
    duthb1 = topology_obj.ports['dut-hb-1']
    dutha2 = topology_obj.ports['dut-ha-2']

    # VLAN config which will be used in test
    vlan_config_dict = {'dut': [{'vlan_id': 30, 'vlan_members': [{'PortChannel0001': 'access'},
                                                                 {duthb1: 'trunk'},
                                                                 {dutha2: 'trunk'}
                                                                 ]},
                                {'vlan_id': 800, 'vlan_members': [{duthb1: 'trunk'}]}
                                ]
                        }

    cli_objects.dut.ip.del_ip_from_interface('PortChannel0001', '30.0.0.1')
    cli_objects.dut.ip.del_ip_from_interface('PortChannel0001', '3000::1', '64')

    logger.info('Starting vlan configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    logger.info('vlan test cases configuration completed')

    yield

    logger.info('Starting vlan test cases configuration cleanup')
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    cli_objects.dut.ip.add_ip_to_interface('PortChannel0001', '30.0.0.1')
    cli_objects.dut.ip.add_ip_to_interface('PortChannel0001', '3000::1', '64')

    logger.info('vlan cleanup completed')
