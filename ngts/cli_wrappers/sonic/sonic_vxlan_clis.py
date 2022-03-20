import allure
import re

from ngts.cli_wrappers.common.vxlan_clis_common import VxlanCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicVxlanCli(VxlanCliCommon):

    @staticmethod
    def configure_vxlan(engine, vxlan_info):
        """
        Method which adding VXLAN on SONiC device
        :param engine: ssh engine object
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        SonicVxlanCli.add_vtep(engine, vtep_name, vxlan_info['vtep_src_ip'])
        if vxlan_info.get('evpn_nvo'):
            SonicVxlanCli.add_evpn_nvo_vxlan_mapping(engine, vtep_name, vxlan_info['evpn_nvo'])
        for tunnel in vxlan_info['tunnels']:
            vlan = tunnel['vlan']
            vni = tunnel['vni']
            SonicVxlanCli.add_vtep_mapping_to_vlan_vni(engine, vtep_name, vlan, vni)

    @staticmethod
    def delete_vxlan(engine, vxlan_info):
        """
        Method which remove VXLAN on SONiC device
        :param engine: ssh engine object
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        for tunnel in vxlan_info['tunnels']:
            vlan = tunnel['vlan']
            vni = tunnel['vni']
            SonicVxlanCli.del_vtep_mapping_to_vlan_vni(engine, vtep_name, vlan, vni)
        if vxlan_info.get('evpn_nvo'):
            SonicVxlanCli.del_evpn_nvo_vxlan_mapping(engine, vxlan_info['evpn_nvo'])
        SonicVxlanCli.del_vtep(engine, vtep_name)

    @staticmethod
    def add_vtep(engine, vtep_name, src_ip):
        """
        Method which adding VTEP to SONiC dut
        :param engine: ssh engine object
        :param vtep_name: VTEP name
        :param src_ip: src_ip which will be used by VTEP
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan add {} {}'.format(vtep_name, src_ip))

    @staticmethod
    def del_vtep(engine, vtep_name):
        """
        Method which removing VTEP from SONiC dut
        :param engine: ssh engine object
        :param vtep_name: VTEP name
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan del {}'.format(vtep_name))

    @staticmethod
    def add_evpn_nvo_vxlan_mapping(engine, vtep_name, evpn_nvo):
        """
        Method which adding mapping for EVPN_NVO to VXLAN tunnel on SONiC dut
        :param engine: ssh engine object
        :param vtep_name: VTEP name
        :param evpn_nvo: evpn nvo name
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan evpn_nvo add {} {}'.format(evpn_nvo, vtep_name))

    @staticmethod
    def del_evpn_nvo_vxlan_mapping(engine, evpn_nvo):
        """
        Method which removing mapping for EVPN_NVO to VXLAN tunnel from SONiC dut
        :param engine: ssh engine object
        :param evpn_nvo: evpn nvo name
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan evpn_nvo del {}'.format(evpn_nvo))

    @staticmethod
    def add_vtep_mapping_to_vlan_vni(engine, vtep_name, vlan, vni):
        """
        Method which adding mapping for VTEP to VLAN/VNI on SONiC dut
        :param engine: ssh engine object
        :param vtep_name: VTEP name
        :param vlan: vlan id
        :param vni: vni id
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan map add {} {} {}'.format(vtep_name, vlan, vni))

    @staticmethod
    def del_vtep_mapping_to_vlan_vni(engine, vtep_name, vlan, vni):
        """
        Method which removing VTEP mapping to VLAN/VNI from SONiC dut
        :param engine: ssh engine object
        :param vtep_name: VTEP name
        :param vlan: vlan id
        :param vni: vni id
        :return: command output
        """
        return engine.run_cmd('sudo config vxlan map del {} {} {}'.format(vtep_name, vlan, vni))

    @staticmethod
    def get_vxlan_tunnels_info(engine):
        """
        Method which gets VXLAN tunnel info from command "show vxlan tunnel"
        :param engine: ssh engine object
        :return: dictionary with parsed output from command
        """
        vxlan_tunnel_output = SonicVxlanCli.show_vxlan_tunnel(engine)
        vxlan_tunnel_dict = generic_sonic_output_parser(vxlan_tunnel_output,
                                                        headers_ofset=0,
                                                        len_ofset=1,
                                                        data_ofset_from_start=2,
                                                        data_ofset_from_end=None,
                                                        column_ofset=2,
                                                        output_key='vxlan tunnel name')
        return vxlan_tunnel_dict

    @staticmethod
    def show_vxlan_tunnel(engine):
        """
        Method which gets VXLAN tunnel info from command "show vxlan tunnel"
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo show vxlan tunnel')

    @staticmethod
    def check_vxlan_tunnels(engine, expected_tunnels_info_list):
        """
        Method which checks VXLAN tunnel info from command "show vxlan tunnel"
        :param engine: ssh engine object
        :param expected_tunnels_info_list: list with expected VXLAN tunnel info.
        Example: [{'vxlan tunnel name': 'vtep_76543', 'source ip': '10.1.0.32', 'destination ip': '',
        'tunnel map name': 'map_76543_Vlan2345', 'tunnel map mapping(vni -> vlan)': '76543 -> Vlan2345'}]
        :return: assertion error in case when expected VXLAN tunnel info does not exist
        """
        vxlan_tunnnels_dict = SonicVxlanCli.get_vxlan_tunnels_info(engine)

        for expected_tunnel_info in expected_tunnels_info_list:
            vxlan_tunnel_name = expected_tunnel_info['vxlan tunnel name']
            with allure.step('Checking VXLAN tunnel {} configuration'.format(vxlan_tunnel_name)):
                source_ip = expected_tunnel_info.get('source ip')
                destination_ip = expected_tunnel_info.get('destination ip')
                tun_map_name = expected_tunnel_info.get('tunnel map name')
                tun_map_mapping = expected_tunnel_info.get('tunnel map mapping(vni -> vlan)')

                assert vxlan_tunnel_name in vxlan_tunnnels_dict
                if source_ip:
                    assert source_ip in vxlan_tunnnels_dict[vxlan_tunnel_name]['source ip']
                if destination_ip:
                    assert destination_ip in vxlan_tunnnels_dict[vxlan_tunnel_name]['destination ip']
                if tun_map_name:
                    assert tun_map_name in vxlan_tunnnels_dict[vxlan_tunnel_name]['tunnel map name']
                if tun_map_mapping:
                    assert tun_map_mapping in vxlan_tunnnels_dict[vxlan_tunnel_name]['tunnel map mapping(vni -> vlan)']

    @staticmethod
    def show_vxlan_vlanvnimap(engine):
        """
        Method which gets VXLAN VLAN to VNI map info from command "show vxlan vlanvnimap"
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo show vxlan vlanvnimap')

    @staticmethod
    def check_vxlan_vlanvnimap(engine, vlan_vni_map_list):
        """
        Method which checks VXLAN VLAN to VNI map info from command "show vxlan vlanvnimap"
        :param engine: ssh engine object
        :param vlan_vni_map_list: list with VLAN VNI maps. Example: [("2345", "76543"), ("1234", "43210")]
        :return: assertion error in case when expected VLAN not mapped to expected VNI
        """
        vxlan_vlanvnimap_output = SonicVxlanCli.show_vxlan_vlanvnimap(engine)
        for vlan_vni in vlan_vni_map_list:
            vlan = vlan_vni[0]
            vni = vlan_vni[1]
            with allure.step('Checking VLAN {} mapping to VNI {}'.format(vlan, vni)):
                assert re.search(r'Vlan{}\s|\s{}\s'.format(vlan, vni), vxlan_vlanvnimap_output)
