import time
from ngts.cli_wrappers.common.vxlan_clis_common import VxlanCliCommon


class LinuxVxlanCli(VxlanCliCommon):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj

    def configure_vxlan(self, vxlan_info):
        """
        Method which adding VXLAN on Linux device
        - Add VXLAN device with specific VNI
        - Add bridge device with name br_VNI
        - Connect bridge device with VXLAN device
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vxlan76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        vni = vxlan_info['vni']
        self.add_vtep(vtep_name, vxlan_info['vtep_src_ip'], vni,
                      vxlan_info.get('vtep_dst_ip'))

        self.engine.run_cmd('brctl addbr br_{}'.format(vni))
        self.engine.run_cmd('brctl addif br_{} {}'.format(vni, vtep_name))
        self.engine.run_cmd('brctl stp br_{} off'.format(vni))

        self.cli_obj.interface.enable_interface(vtep_name)
        self.cli_obj.interface.enable_interface('br_{}'.format(vni))

        for ip_mask in vxlan_info.get('vtep_ips', []):
            ip = ip_mask[0]
            mask = ip_mask[1]
            self.cli_obj.ip.add_ip_to_interface('br_{}'.format(vni), ip, mask)

    def delete_vxlan(self, vxlan_info):
        """
        Method which remove VXLAN from Linux device
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vxlan76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}
        :return: command output
        """
        self.cli_obj.interface.del_interface('br_{}'.format(vxlan_info['vni']))
        self.cli_obj.interface.del_interface(vxlan_info['vtep_name'])

    def add_vtep(self, vtep_name, src_ip, vni, dst_ip=False):
        """
        Method which adding VTEP to Linux device
        :param vtep_name: VTEP name
        :param src_ip: src_ip which will be used by VTEP
        :param vni: vni id
        :param dst_ip: dst_ip which will be used by VTEP
        :return: command output
        """
        cmd = 'ip link add {} type vxlan id {} dstport 4789 local {} '.format(vtep_name, vni, src_ip)
        if dst_ip:
            cmd += 'remote {}'.format(dst_ip)
        else:
            cmd += 'nolearning'

        return self.engine.run_cmd(cmd)

    def add_vxlan_veth(self, name_space, bridge_name, veth_name, veth_peer_name):
        """
        This method is used to add veth pair to vxlan bridge, use it as vxlan customer
        :param name_space: name space name
        :param bridge_name: the bridge to bind veth pair
        :param veth_name: veth name
        :param veth_peer_name: veth peer name
        """
        add_name_space = f"ip netns add {name_space}"
        add_veth_peer = f"ip link add {veth_name} type veth peer name {veth_peer_name}"
        set_veth_peer_up = f"ip link set dev {veth_peer_name} up"
        link_veth_with_name_space = f"ip link set {veth_name} netns {name_space}"
        set_veth_in_name_space_up = f"ip netns exec {name_space} ip link set dev {veth_name} up"
        bind_veth_peer_with_bridge = f"brctl addif {bridge_name} {veth_peer_name}"
        self.engine.run_cmd(add_name_space)
        self.engine.run_cmd(add_veth_peer)
        self.engine.run_cmd(set_veth_peer_up)
        self.engine.run_cmd(link_veth_with_name_space)
        self.engine.run_cmd(set_veth_in_name_space_up)
        self.engine.run_cmd(bind_veth_peer_with_bridge)

    def del_vxlan_veth_ns(self, veth_name, name_space):
        """
        This method is used to delete veth pair and its related namespace
        :param veth_name: veth_name or veth peer name
        """
        self.engine.run_cmd(f"ip link del dev {veth_name}")
        self.engine.run_cmd(f"ip netns del {name_space}")

    def set_veth_ip_addr(self, name_space, veth_name, ip, mask=24):
        """
        This method is used to set ip address of veth in a specific namespace
        :param name_space: name space name
        :param veth_name: veth name
        :param ip: ip address
        """
        self.engine.run_cmd(f"ip netns exec {name_space} ip addr add {ip}/{mask} dev {veth_name}")

    def set_veth_mac_addr(self, name_space, veth_name, mac):
        """
        This method is used to set mac address of veth in a specific namespace
        :param name_space: name space name
        :param veth_name: veth name
        :param mac: mac address
        """
        self.engine.run_cmd(f"ip netns exec {name_space} ip link set {veth_name} address {mac}")

    def set_if_mac_addr(self, if_name, mac):
        """
        This method is used to set mac address of a linux interface
        :param if_name: linux interface name
        :param mac: mac address
        """
        self.engine.run_cmd(f"ip link set {if_name} address {mac}")

    def shutdown_interface(self, if_name):
        """
        This method is used to shutdown a linux interface
        It is a common way to stop send BGP route asap
        :param if_name: interface name
        """
        self.engine.run_cmd(f"ip link set dev {if_name} down")
        # Add 2 seconds for FRR BGP to detect the port flap and send evpn vxlan mac route
        time.sleep(2)

    def no_shutdown_interface(self, if_name):
        """
        This method is used to no shutdown a linux interface
        It is a common way to start send BGP route asap
        :param if_name: interface name
        """
        self.engine.run_cmd(f"ip link set dev {if_name} up")
        # Add 2 seconds for FRR BGP to detect the port flap and send evpn vxlan mac route
        time.sleep(2)
