import allure
import re

from retry import retry
from ngts.cli_wrappers.common.vxlan_clis_common import VxlanCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicVxlanCli(VxlanCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def configure_vxlan(self, vxlan_info):
        """
        Method which adding VXLAN on SONiC device
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        if vxlan_info.get('evpn_nvo'):
            self.add_vtep(vtep_name, vxlan_info['vtep_src_ip'])
            self.add_evpn_nvo_vxlan_mapping(vtep_name, vxlan_info['evpn_nvo'])
        for tunnel in vxlan_info['tunnels']:
            vlan = tunnel['vlan']
            vni = tunnel['vni']
            self.add_vtep_mapping_to_vlan_vni(vtep_name, vlan, vni)

    def delete_vxlan(self, vxlan_info):
        """
        Method which remove VXLAN on SONiC device
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vtep_76543', 'vtep_src_ip': '10.1.0.32', 'vni': 76543, 'vlan': 2345}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        for tunnel in vxlan_info['tunnels']:
            vlan = tunnel['vlan']
            vni = tunnel['vni']
            self.del_vtep_mapping_to_vlan_vni(vtep_name, vlan, vni)
        if vxlan_info.get('evpn_nvo'):
            self.del_evpn_nvo_vxlan_mapping(vxlan_info['evpn_nvo'])
            self.del_vtep(vtep_name)

    def add_vtep(self, vtep_name, src_ip):
        """
        Method which adding VTEP to SONiC dut
        :param vtep_name: VTEP name
        :param src_ip: src_ip which will be used by VTEP
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan add {} {}'.format(vtep_name, src_ip))

    def del_vtep(self, vtep_name):
        """
        Method which removing VTEP from SONiC dut
        :param vtep_name: VTEP name
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan del {}'.format(vtep_name))

    def add_evpn_nvo_vxlan_mapping(self, vtep_name, evpn_nvo):
        """
        Method which adding mapping for EVPN_NVO to VXLAN tunnel on SONiC dut
        :param vtep_name: VTEP name
        :param evpn_nvo: evpn nvo name
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan evpn_nvo add {} {}'.format(evpn_nvo, vtep_name))

    def del_evpn_nvo_vxlan_mapping(self, evpn_nvo):
        """
        Method which removing mapping for EVPN_NVO to VXLAN tunnel from SONiC dut
        :param evpn_nvo: evpn nvo name
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan evpn_nvo del {}'.format(evpn_nvo))

    def add_vtep_mapping_to_vlan_vni(self, vtep_name, vlan, vni):
        """
        Method which adding mapping for VTEP to VLAN/VNI on SONiC dut
        :param vtep_name: VTEP name
        :param vlan: vlan id
        :param vni: vni id
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan map add {} {} {}'.format(vtep_name, vlan, vni))

    def add_vtep_mapping_range_to_vlan_vni(self, vtep_name, vlan_start, vlan_end, vni_start):
        """
        Method which adding mapping range for VTEP to VLAN/VNI on SONIC dut
        :param vtep_name: VTEP name
        :param vlan_start: vlan range start vlan
        :param vlan_end: vlan range stop vlan
        :param vni_start: vni range start vni
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan map_range add {} {} {} {}'.format(vtep_name, vlan_start, vlan_end, vni_start))

    def del_vtep_mapping_to_vlan_vni(self, vtep_name, vlan, vni):
        """
        Method which removing VTEP mapping to VLAN/VNI from SONiC dut
        :param vtep_name: VTEP name
        :param vlan: vlan id
        :param vni: vni id
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan map del {} {} {}'.format(vtep_name, vlan, vni))

    def del_vtep_mapping_range_to_vlan_vni(self, vtep_name, vlan_start, vlan_end, vni_start):
        """
        Method which removing mapping range for VTEP to VLAN/VNI on SONIC dut
        :param vtep_name: VTEP name
        :param vlan_start: vlan range start vlan
        :param vlan_end: vlan range stop vlan
        :param vni_start: vni range start vni
        :return: command output
        """
        return self.engine.run_cmd('sudo config vxlan map_range del {} {} {} {}'.format(vtep_name, vlan_start, vlan_end, vni_start))

    def get_vxlan_tunnels_info(self):
        """
        Method which gets VXLAN tunnel info from command "show vxlan tunnel"
        :return: dictionary with parsed output from command
        """
        vxlan_tunnel_output = self.show_vxlan_tunnel()
        vxlan_tunnel_dict = generic_sonic_output_parser(vxlan_tunnel_output,
                                                        headers_ofset=0,
                                                        len_ofset=1,
                                                        data_ofset_from_start=2,
                                                        data_ofset_from_end=None,
                                                        column_ofset=2,
                                                        output_key='vxlan tunnel name')
        return vxlan_tunnel_dict

    def show_vxlan_tunnel(self):
        """
        Method which gets VXLAN tunnel info from command "show vxlan tunnel"
        :return: command output
        """
        return self.engine.run_cmd('sudo show vxlan tunnel')

    @retry(Exception, tries=5, delay=2)
    def check_vxlan_tunnels(self, expected_tunnels_info_list):
        """
        Method which checks VXLAN tunnel info from command "show vxlan tunnel"
        :param expected_tunnels_info_list: list with expected VXLAN tunnel info.
        Example: [{'vxlan tunnel name': 'vtep_76543', 'source ip': '10.1.0.32', 'destination ip': '',
        'tunnel map name': 'map_76543_Vlan2345', 'tunnel map mapping(vni -> vlan)': '76543 -> Vlan2345'}]
        :return: assertion error in case when expected VXLAN tunnel info does not exist
        """
        vxlan_tunnnels_dict = self.get_vxlan_tunnels_info()

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

    def show_vxlan_vlanvnimap(self):
        """
        Method which gets VXLAN VLAN to VNI map info from command "show vxlan vlanvnimap"
        :return: command output
        """
        return self.engine.run_cmd('sudo show vxlan vlanvnimap')

    def check_vxlan_vlanvnimap(self, vlan_vni_map_list):
        """
        Method which checks VXLAN VLAN to VNI map info from command "show vxlan vlanvnimap"
        :param vlan_vni_map_list: list with VLAN VNI maps. Example: [("2345", "76543"), ("1234", "43210")]
        :return: assertion error in case when expected VLAN not mapped to expected VNI
        """
        vxlan_vlanvnimap_output = self.show_vxlan_vlanvnimap()
        for vlan_vni in vlan_vni_map_list:
            vlan = vlan_vni[0]
            vni = vlan_vni[1]
            with allure.step('Checking VLAN {} mapping to VNI {}'.format(vlan, vni)):
                assert re.search(r'Vlan{}\s|\s{}\s'.format(vlan, vni), vxlan_vlanvnimap_output)

    def show_vxlan_remotemac(self, vtep_ip='all'):
        """
        This method is used to get VXLAN remote MAC addresses from command "show vxlan remotemac"
        :param vtep_ip: the vtep ip address, default value is all, means list all the entries
        :return: command output
        """
        return self.engine.run_cmd(f"sudo show vxlan remotemac {vtep_ip}")

    @retry(Exception, tries=5, delay=2)
    def check_vxlan_remotemac(self, vlan_mac_vtep_vni_check_list, type='dynamic', learned=True):
        """
        This method is used to check VXLAN remote mac learning status from command "show vxlan remotemac"
        The typical output of command "show vxlan remotemac" is listed
        +---------+-------------------+--------------+--------+---------+
        | VLAN    | MAC               | RemoteVTEP   |    VNI | Type    |
        +=========+===================+==============+========+=========+
        | Vlan100 | 2e:9e:14:94:98:77 | 40.0.0.3     | 500100 | dynamic |
        +---------+-------------------+--------------+--------+---------+
        | Vlan100 | 86:3c:7a:78:8a:a7 | 30.0.0.2     | 500100 | dynamic |
        +---------+-------------------+--------------+--------+---------+
        | Vlan101 | 0a:bf:1f:21:cf:91 | 30.0.0.2     | 500101 | dynamic |
        +---------+-------------------+--------------+--------+---------+
        Total count : 3

        :param vlan_mac_vtep_vni_check_list: list with VLAN, MAC, VTEP IP, VNI maps. Example: [("100", "2e:9e:14:94:98:77", "40.0.0.3", "500100")]
        :param type: mac type, now there is only one value "dynamic"
        :param learned: a flag to determine wether or not the mac entry is supposed to be learned
        :return: assertion error in case of mac does not exist with specific parameters
        """
        remotemac_output = self.show_vxlan_remotemac()
        for vlan_mac_vtep_vni in vlan_mac_vtep_vni_check_list:
            vlan = vlan_mac_vtep_vni[0]
            mac = vlan_mac_vtep_vni[1]
            vtep_ip = vlan_mac_vtep_vni[2]
            vni = vlan_mac_vtep_vni[3]
            if learned:
                with allure.step(f"Checking MAC {mac} learned from VTEP {vtep_ip} with VLAN {vlan} and VNI {vni}"):
                    assert re.search(fr"Vlan{vlan}\s+\|\s+{mac}\s+\|\s+{vtep_ip}\s+\|\s+{vni}\s+\|\s+{type}\s+\|", remotemac_output)
            else:
                with allure.step(f"Checking MAC {mac} not learned from VTEP {vtep_ip} with VLAN {vlan} and VNI {vni}"):
                    assert not re.search(fr"Vlan{vlan}\s+\|\s+{mac}\s+\|\s+{vtep_ip}\s+\|\s+{vni}\s+\|\s+{type}\s+\|", remotemac_output)

    def show_vxlan_remotevni(self, vtep_ip='all'):
        """
        This method is used to get VXLAN remote vni list from command 'show vxlan remotevni'
        :param vtep_ip: vtep ip address
        :return: command output
        """
        return self.engine.run_cmd(f"sudo show vxlan remotevni {vtep_ip}")

    def check_vxlan_remotevni(self, vlan_vtep_vni_check_list, all=False, learned=True):
        """
        This method is used to check VXLAN remote vni status from command 'show vxlan remotevni'
        The typical output of the command is listed
        +---------+--------------+--------+
        | VLAN    | RemoteVTEP   |    VNI |
        +=========+==============+========+
        | Vlan100 | 30.0.0.2     | 500100 |
        +---------+--------------+--------+
        | Vlan100 | 40.0.0.3     | 500100 |
        +---------+--------------+--------+
        | Vlan101 | 30.0.0.2     | 500101 |
        +---------+--------------+--------+
        Total count : 3

        :param vlan_vtep_vni_check_list: list with vlan, remote vtep ip and vni. Example: [("100", "40.0.0.3", "500100")]
        :param all: flag to determine whether to use option 'all' or 'vtep_ip' in the command 'show vxlan remotevni all|vtep_ip'
        :param learned: flag to determine whether or not the vni entry is supposed to be learned
        :return: assertion error in case of no match
        """
        if all:
            remotevni_output = self.show_vxlan_remotevni()
        for vlan_vtep_vni in vlan_vtep_vni_check_list:
            vlan = vlan_vtep_vni[0]
            vtep_ip = vlan_vtep_vni[1]
            vni = vlan_vtep_vni[2]
            if not all:
                remotevni_output = self.show_vxlan_remotevni(vtep_ip)
            if learned:
                with allure.step(f"Checking VNI {vni} learned from VTEP {vtep_ip} with VLAN {vlan}"):
                    assert re.search(fr"Vlan{vlan}\s+\|\s+{vtep_ip}\s+\|\s+{vni}\s+\|", remotevni_output)
            else:
                with allure.step(f"Checking VNI {vni} not learned from VTEP {vtep_ip} with VLAN {vlan}"):
                    assert not re.search(fr"Vlan{vlan}\s+\|\s+{vtep_ip}\s+\|\s+{vni}\s+\|", remotevni_output)

    def enable_vxlan_counter(self):
        """
        This method is used to enable vxlan counter
        """
        return self.engine.run_cmd("sudo counterpoll tunnel enable")

    def disable_vxlan_counter(self):
        """
        This method is used to disable vxlan counter
        """
        return self.engine.run_cmd("sudo counterpoll tunnel disable")

    def clear_vxlan_counter(self):
        """
        This method is used to clear vxlan counter
        """
        return self.engine.run_cmd("sudo sonic-clear tunnelcounters")

    def show_vxlan_counter(self, vtep_name=None):
        """
        This method is used to get VXLAN Counter info from command "show vxlan counters"
        There are two format outputs
        Default format is:

        'show vxlan counters'
             IFACE    RX_PKTS    RX_BYTES    RX_PPS    TX_PKTS    TX_BYTES    TX_PPS
        ----------  ---------  ----------  --------  ---------  ----------  --------
        vtep101032          0         N/A    0.00/s          0         N/A    0.00/s

        Vtep based format is

        'show vxlan counters vtep101032'
        vtep101032
        ----------

                RX:
                         0 packets
                       N/A bytes
                TX:
                         0 packets
                       N/A bytes

        :return: command output
        """
        if vtep_name:
            vxlan_counters = self.engine.run_cmd('sudo show vxlan counters {}'.format(vtep_name))
            return vxlan_counters
        else:
            vxlan_counters = self.engine.run_cmd('sudo show vxlan counters')
            vxlan_counters_dict = generic_sonic_output_parser(vxlan_counters,
                                                              headers_ofset=1,
                                                              len_ofset=2,
                                                              data_ofset_from_start=3,
                                                              column_ofset=2,
                                                              output_key='IFACE')
            return vxlan_counters_dict

    def show_interface_counter(self):
        """
        This method is used to get interface counter info from command "show interface counters"
        :return: command output
        """
        interface_counters = self.engine.run_cmd('show interface counters')
        interface_counters_dict = generic_sonic_output_parser(interface_counters,
                                                              headers_ofset=1,
                                                              len_ofset=2,
                                                              data_ofset_from_start=2,
                                                              column_ofset=2,
                                                              output_key='IFACE')
        return interface_counters_dict

    def show_vxlan_interface(self):
        """
        This method is used to get vxlan interface infos from "show vxlan interface"

        VTEP Information:

        VTEP Name : vtep101032, SIP  : 10.1.0.32
        NVO Name  : my-nvo,  VTEP : vtep101032
        Source interface  : Loopback0

        :return: command output
        """
        return self.engine.run_cmd('show vxlan interface')

    def check_vxlan_interface_info(self, nvo_name, vtep_name, vtep_ip, vtep_interface):
        """
        This method is used to check the vxlan interface infos from "show vxlan interface"
        :param nvo_name: nvo name
        :param vtep_name:  vtep name
        :param vtep_ip: vtep ip address
        :param vtep_interface: vtep interface
        :return:
        """
        vxlan_interface_info = self.show_vxlan_interface()
        assert re.search(fr"NVO\sName\s+\:\s+{nvo_name},", vxlan_interface_info)
        assert re.search(fr"VTEP\sName\s\:\s{vtep_name},", vxlan_interface_info)
        assert re.search(fr"SIP\s+\:\s{vtep_ip}", vxlan_interface_info)
        assert re.search(fr"Source\sinterface\s+\:\s{vtep_interface}", vxlan_interface_info)
