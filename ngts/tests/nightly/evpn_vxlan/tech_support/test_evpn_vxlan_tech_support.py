import logging
import pytest
import os

from retry import retry
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vxlan_config_template import VxlanConfigTemplate
from ngts.config_templates.frr_config_template import FrrConfigTemplate
from ngts.helpers.vxlan_helper import send_and_validate_traffic, verify_counter_entry, validate_basic_evpn_type_2_3_route, get_tech_support_tar_file, validate_vxlan_table_in_dest_json, \
    validate_dest_files_exist_in_tarball
from ngts.constants.constants import VxlanConstants
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure

"""

 EVPN VXLAN Test Cases

 Documentation: https://confluence.nvidia.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+EVPN+VXLAN+Documentation

"""

logger = logging.getLogger()
allure.logger = logger

VNI_TO_HEX_VNI_MAP = {VxlanConstants.VNI_12345: '0x303900'}
CONFIG_DB_JSON_NAME = 'CONFIG_DB.json'
APPL_DB_JSON_NAME = 'APPL_DB.json'
CONFIG_DB_VXLAN_TABLES = ['VXLAN_EVPN_NVO', 'VXLAN_TUNNEL_MAP', 'VXLAN_TUNNEL']
APPL_DB_VXLAN_TABLES = ['VXLAN_EVPN_NVO_TABLE', 'VXLAN_FDB_TABLE', 'VXLAN_REMOTE_VNI_TABLE', 'VXLAN_TUNNEL_MAP_TABLE', 'VXLAN_TUNNEL_TABLE']


@pytest.fixture(scope='module', autouse=True)
def basic_configuration(topology_obj, interfaces, cli_objects):
    """
    Pytest fixture used to configure basic vlan and ip configuration
    And config vlan and vni map related configurations
    :param topology_obj: topology object fixture
    :param interfaces:  interfaces fixture
    """
    ip_config_dict = {
        'dut': [{'iface': 'Loopback0', 'ips': [('10.1.0.32', '32')]},
                {'iface': interfaces.dut_ha_1, 'ips': [('1.1.1.2', '24')]}
                ],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('1.1.1.1', '24')]}
               ]
    }

    frr_config_folder = os.path.dirname(os.path.abspath(__file__))
    frr_config_dict = {
        'dut': {'configuration': {'config_name': 'dut_frr_config.conf', 'path_to_config_file': frr_config_folder},
                'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']},
        'ha': {'configuration': {'config_name': 'ha_frr_config.conf', 'path_to_config_file': frr_config_folder},
               'cleanup': ['configure terminal', 'no router bgp', 'exit', 'exit']}
    }

    vlan_config_dict = {
        'dut': [{'vlan_id': '{}'.format(VxlanConstants.VLAN_100), 'vlan_members': [{interfaces.dut_hb_1: 'trunk'}]}
                ],
        'hb': [{'vlan_id': '{}'.format(VxlanConstants.VLAN_100), 'vlan_members': [{interfaces.hb_dut_1: None}]}
               ]
    }

    vxlan_ip_config_dict = {
        'dut': [{'iface': 'Vlan{}'.format(VxlanConstants.VLAN_100), 'ips': [('100.0.0.1', '24')]}
                ],
        'hb': [{'iface': '{}.{}'.format(interfaces.hb_dut_1, VxlanConstants.VLAN_100), 'ips': [('100.0.0.3', '24')]}
               ]
    }

    vxlan_config_dict = {
        'dut': [{'evpn_nvo': '{}'.format(VxlanConstants.EVPN_NVO), 'vtep_name': 'vtep101032', 'vtep_src_ip': '10.1.0.32',
                 'tunnels': [{'vni': '{}'.format(VxlanConstants.VNI_12345), 'vlan': '{}'.format(VxlanConstants.VLAN_100)}]}
                ],
        'ha': [{'vtep_name': 'vtep_{}'.format(VxlanConstants.VNI_12345), 'vtep_src_ip': '1.1.1.1', 'vni': '{}'.format(VxlanConstants.VNI_12345),
                'vtep_ips': [('100.0.0.2', '24')]}],
    }

    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('Evpn vxlan configuration completed')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, vxlan_ip_config_dict)
    VxlanConfigTemplate.configuration(topology_obj, vxlan_config_dict)
    # in case there is useless bgp configuration exist
    FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
    FrrConfigTemplate.configuration(topology_obj, frr_config_dict)
    logger.info("Enable vxlan counter")
    cli_objects.dut.vxlan.enable_vxlan_counter()

    yield

    logger.info("Disable vxlan counter")
    cli_objects.dut.vxlan.disable_vxlan_counter()
    logger.info('Cleanup evpn vxlan configuration')
    FrrConfigTemplate.cleanup(topology_obj, frr_config_dict)
    VxlanConfigTemplate.cleanup(topology_obj, vxlan_config_dict)
    IpConfigTemplate.cleanup(topology_obj, vxlan_ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)


class TestEvpnVxlanTechSupport:

    @pytest.fixture(autouse=True)
    def prepare_param(self, topology_obj, engines, players, interfaces):
        self.topology_obj = topology_obj
        self.engines = engines
        self.players = players
        self.interfaces = interfaces

        self.dut_loopback_ip = '10.1.0.32'
        self.dut_vlan_ip = '100.0.0.1'
        self.dut_ha_1_ip = '1.1.1.2'

        self.ha_dut_1_ip = '1.1.1.1'
        self.ha_br_ip = '100.0.0.2'

        self.hb_vlan_ip = '100.0.0.3'

        self.hb_vlan_100_iface = f"{interfaces.hb_dut_1}.100"

        self.dut_bgp_neighbor_1_ip_1_1_1_1 = self.ha_dut_1_ip

        self.dut_vtep_ip = self.dut_loopback_ip
        self.ha_vtep_ip = self.ha_dut_1_ip

    def get_ha_br_mac(self, cli_objects, vni):
        """
        This method is used to get the mac address of bridge interface at HA
        :param cli_objects: cli_objects fixture
        :return: mac address of bridge interface at HA
        """
        ha_vni_iface = f"br_{vni}"
        ha_br_mac = cli_objects.ha.mac.get_mac_address_for_interface(ha_vni_iface)
        return ha_br_mac

    def validate_basic_traffic_and_counters(self, cli_objects, interfaces, vlan_id, vni):
        with allure.step(f"Send traffic from HB to HA via VLAN {vlan_id} to VNI {vni}"):
            hb_vlan_iface = f"{interfaces.hb_dut_1}.{vlan_id}"
            hb_vlan_mac = cli_objects.hb.mac.get_mac_address_for_interface(hb_vlan_iface)
            ha_vni_iface = f"br_{vni}"
            ha_br_mac = cli_objects.ha.mac.get_mac_address_for_interface(ha_vni_iface)

            logger.info("Clear vxlan counter")
            cli_objects.dut.vxlan.clear_vxlan_counter()
            pkt_hb_ha_vlan_vni_r = VxlanConstants.SIMPLE_PACKET.format(hb_vlan_mac, ha_br_mac,
                                                                       self.hb_vlan_ip,
                                                                       self.ha_br_ip)
            logger.info("Validate traffic from HB to HA")
            send_and_validate_traffic(player=self.players, sender=VxlanConstants.HOST_HB,
                                      sender_intf=hb_vlan_iface, sender_pkt_format=pkt_hb_ha_vlan_vni_r,
                                      sender_count=VxlanConstants.PACKET_NUM_100, receiver=VxlanConstants.HOST_HA, receiver_intf=interfaces.ha_dut_1,
                                      receiver_filter_format=VxlanConstants.TCPDUMP_VXLAN_SRC_IP_FILTER.format(
                                          VNI_TO_HEX_VNI_MAP[vni],
                                          VxlanConstants.HEX_100_0_0_3))

        with allure.step('Validate vxlan tx counters'):
            verify_counter_entry(cli_objects, VxlanConstants.VTEP_NAME_DUT, 'tx', 100)

    def validate_basic_vxlan_function(self, cli_objects, interfaces, vlan_id, vni):
        """
        This method is used to verify a full set of test
        1. Validate BGP neighbor establishment
        2. Validate type 2 and type 3 routes
        3. Validate VXLAN remote mac learning
        4. Validate basic side traffic
        5. Validate VXLAN counters
        :param topology_obj: topology_obj fixture
        :param cli_objects: cli_objects fixture
        :param interfaces:  interface fixture
        :param vlan_id: vlan id
        :param vni: vni value
        """
        with allure.step(f"Validate BGP neighbor {self.ha_dut_1_ip} established"):
            cli_objects.dut.frr.validate_bgp_neighbor_established(self.ha_dut_1_ip)
        with allure.step(f"Validate evpn type 2 and type 3 routes for vni {vni}"):
            ha_br_mac = self.get_ha_br_mac(cli_objects, vni)
            validate_basic_evpn_type_2_3_route(self.players, cli_objects, interfaces, vlan_id, self.dut_vlan_ip, self.dut_loopback_ip, self.ha_vtep_ip, self.hb_vlan_ip, VxlanConstants.RD_100)
        with allure.step(f"Validate MAC {ha_br_mac} is learned from EVPN VXLAN - vlan {vlan_id} - vtep {self.ha_vtep_ip} - vni {vni}"):
            cli_objects.dut.vxlan.check_vxlan_remotemac(vlan_mac_vtep_vni_check_list=[
                (vlan_id, ha_br_mac, self.ha_vtep_ip, vni)
            ])
        with allure.step('Validate vxlan traffic and counters'):
            self.validate_basic_traffic_and_counters(cli_objects, interfaces, VxlanConstants.VLAN_100, VxlanConstants.VNI_12345)

    def validate_vxlan_tables_in_tech_support(self, engines):
        """
        This method is used to very all needed VXLAN infos exist in tech support dump files
        Typical VXLAN tables in CONFIG_DB.json:
            "VXLAN_EVPN_NVO"
            "VXLAN_TUNNEL_MAP"
            "VXLAN_TUNNEL"
        Typical VXLAN tables in APPL_DB.json:
            "VXLAN_EVPN_NVO_TABLE"
            "VXLAN_FDB_TABLE"
            "VXLAN_REMOTE_VNI_TABLE"
            "VXLAN_TUNNEL_MAP_TABLE"
            "VXLAN_TUNNEL_TABLE"
        :param engines: engines fixture
        """
        with allure.step("Execute 'show techsupport' command and copy the tarball from DUT to NGTS docker"):
            tarball_file_name = get_tech_support_tar_file(engines)

        with allure.step(f"Get file path of {CONFIG_DB_JSON_NAME}"):
            config_db_json_path = validate_dest_files_exist_in_tarball(tarball_file_name, CONFIG_DB_JSON_NAME)
        with allure.step(f"Validate VXLAN tables existence in {tarball_file_name}"):
            validate_vxlan_table_in_dest_json(engines, tarball_file_name, config_db_json_path, CONFIG_DB_VXLAN_TABLES)

        with allure.step(f"Get file path of {APPL_DB_JSON_NAME}"):
            appl_db_json_path = validate_dest_files_exist_in_tarball(tarball_file_name, APPL_DB_JSON_NAME)
        with allure.step(f"Validate VXLAN tables existence in {tarball_file_name}"):
            validate_vxlan_table_in_dest_json(engines, tarball_file_name, appl_db_json_path, APPL_DB_VXLAN_TABLES, remove_tarball=True)

    def test_tech_support(self, cli_objects, topology_obj, interfaces, engines):
        """
        This test will check EVPN VXLAN config change functionality

        Test has next steps:
        1. Configure BGP/EVPN VXLAN on DUT and HA, VNI 12345
        2. Add VLAN 100 on DUT and map with with tunnel 12345, make VLAN 100 accessible on HB
        3. Validate traffic and VXLAN counters work fine
        4. Do "show techsupport"
        5. Check that in techsupport dump available info about EVPN VXLAN tunnels
          1) Table 'VXLAN_EVPN_NVO', 'VXLAN_TUNNEL_MAP', 'VXLAN_TUNNEL' exist in CONFIG_DB.json file
          2) Table 'VXLAN_EVPN_NVO_TABLE', 'VXLAN_FDB_TABLE', 'VXLAN_REMOTE_VNI_TABLE', 'VXLAN_TUNNEL_MAP_TABLE', 'VXLAN_TUNNEL_TABLE'
             exist in APPL_DB.json
        """
        with allure.step(f"Test VXLAN functionality at VLAN {VxlanConstants.VLAN_100} map with VNI {VxlanConstants.VNI_12345}"):
            self.validate_basic_vxlan_function(cli_objects, interfaces, VxlanConstants.VLAN_100, VxlanConstants.VNI_12345)
        with allure.step(f"Execute 'show techsupport' command"):
            self.validate_vxlan_tables_in_tech_support(engines)
