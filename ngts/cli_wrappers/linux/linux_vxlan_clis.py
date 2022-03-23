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
