import pytest
import logging
import allure
import os
import json

from retry.api import retry_call
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.constants.constants import InfraConst


logger = logging.getLogger()
CONFIGS_FOLDER = os.path.dirname(os.path.abspath(__file__))


def prepare_dut_bgp_config():
    """
    Prepare config for BGP which will be loaded on DUT and save locally
    :return: path to BGP config file
    """

    bgp_conf = {"BGP_NEIGHBOR": {"20.0.0.2": {"admin_status": "up", "asn": "501", "holdtime": "10", "keepalive": "3",
                                              "local_addr": "20.0.0.1", "name": "HA", "nhopself": "0", "rrclient": "0"},
                                 "30.0.0.2": {"admin_status": "up", "asn": "501", "holdtime": "10", "keepalive": "3",
                                              "local_addr": "30.0.0.1", "name": "HB", "nhopself": "0", "rrclient": "0"}
                                 },
                "DEVICE_METADATA": {"localhost": {"bgp_asn": "500"}}
                }

    bgp_conf_file_path = os.path.join(CONFIGS_FOLDER, 'dut_bgp_conf.json')

    with open(bgp_conf_file_path, 'w') as bgp_conf_file:
        json.dump(bgp_conf, bgp_conf_file, indent=4)

    return bgp_conf_file_path


@pytest.fixture(scope='class', autouse=True)
def configuration(topology_obj, cli_objects, engines, interfaces, platform_params, setup_name):
    """
    Pytest fixture which are doing configuration for routing tests
    Configuration schema:
     ----------------           ---------------             ---------------
    |AS 501         |      -----|20.0.0.1/24   |           |AS 501         |
    |               |    BGP    |    AS 500    |    BGP    |               |
    |    20.0.0.2/24|-----      |10.10.10.10/32|      -----|30.0.0.2/24    |
    |               |           |              |     |     |               |
    |               |           |   30.0.0.1/24|-----      |               |
     ---------------            ---------------             ---------------
    DUT has static routes:
    50.0.0.0/24 via 20.0.0.2
    50.0.0.1/32 via 30.0.0.2
    :param topology_obj: topology object fixture
    :param cli_objects: cli_objects fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :param platform_params: platform_params fixture
    :param setup_name: setup_name fixture
    """
    # Clear FRR BGP config (could exist default BGP configuration)
    engines.dut.run_cmd('sudo sed -e "s/split/separated/g" -i /etc/sonic/config_db.json')
    cli_objects.dut.frr.remove_frr_config_files()
    cli_objects.dut.general.reload_flow(topology_obj=topology_obj, reload_force=True)

    # IP config which will be used in test
    dut_ip_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'ips': [('20.0.0.1', '24')]},
                {'iface': interfaces.dut_hb_1, 'ips': [('30.0.0.1', '24')]},
                {'iface': 'Loopback0', 'ips': [('10.10.10.10', '32')]}
                ]
    }

    hosts_ip_config_dict = {
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('20.0.0.2', '24')]}
               ],
        'hb': [{'iface': interfaces.hb_dut_1, 'ips': [('30.0.0.2', '24')]}
               ]
    }

    static_route_config_dict = {
        'dut': [{'dst': '50.0.0.0', 'dst_mask': 24, 'via': ['20.0.0.2']},
                {'dst': '50.0.0.1', 'dst_mask': 32, 'via': ['30.0.0.2']}]
    }

    frr_config_dict = {
        'ha': {'configuration': {'config_name': 'ha_frr.conf', 'path_to_config_file': CONFIGS_FOLDER},
               'cleanup': ['configure terminal', 'no router bgp 501', 'exit', 'exit']},
        'hb': {'configuration': {'config_name': 'hb_frr.conf', 'path_to_config_file': CONFIGS_FOLDER},
               'cleanup': ['configure terminal', 'no router bgp 501', 'exit', 'exit']}
    }

    IpConfigTemplate.configuration(topology_obj, dut_ip_config_dict)
    IpConfigTemplate.configuration(topology_obj, hosts_ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    FrrConfigTemplate.configuration(topology_obj, frr_config_dict)

    dut_bgp_conf_file_path = prepare_dut_bgp_config()
    engines.dut.copy_file(source_file=dut_bgp_conf_file_path, file_system='/tmp', dest_file='dut_bgp_conf.json')
    engines.dut.run_cmd('sudo config load -y /tmp/dut_bgp_conf.json')
    cli_objects.dut.general.save_configuration()

    cli_objects.dut.general.reload_flow(ports_list=[interfaces.dut_ha_1, interfaces.dut_hb_1], reload_force=True)

    yield

    FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
    IpConfigTemplate.cleanup(topology_obj, hosts_ip_config_dict)

    hwsku = platform_params['hwsku']
    shared_path = '{}{}'.format(InfraConst.MARS_TOPO_FOLDER_PATH, setup_name)
    cli_objects.dut.general.upload_config_db_file(topology_obj, setup_name, hwsku, shared_path)
    cli_objects.dut.general.reload_flow(topology_obj=topology_obj, reload_force=True)
