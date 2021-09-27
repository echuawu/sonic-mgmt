from ngts.cli_wrappers.common.vxlan_clis_common import VxlanCliCommon
from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.linux.linux_ip_clis import LinuxIpCli


class LinuxVxlanCli(VxlanCliCommon):

    @staticmethod
    def configure_vxlan(engine, vxlan_info):
        """
        Method which adding VXLAN on Linux device
        - Add VXLAN device with specific VNI
        - Add bridge device with name br_VNI
        - Connect bridge device with VXLAN device
        :param engine: ssh engine object
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vxlan76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}
        :return: command output
        """
        vtep_name = vxlan_info['vtep_name']
        vni = vxlan_info['vni']
        LinuxVxlanCli.add_vtep(engine, vtep_name, vxlan_info['vtep_src_ip'], vni,
                               vxlan_info.get('vtep_dst_ip'))

        engine.run_cmd('brctl addbr br_{}'.format(vni))
        engine.run_cmd('brctl addif br_{} {}'.format(vni, vtep_name))
        engine.run_cmd('brctl stp br_{} off'.format(vni))

        LinuxInterfaceCli.enable_interface(engine, vtep_name)
        LinuxInterfaceCli.enable_interface(engine, 'br_{}'.format(vni))

        for ip_mask in vxlan_info.get('vtep_ips', []):
            ip = ip_mask[0]
            mask = ip_mask[1]
            LinuxIpCli.add_ip_to_interface(engine, 'br_{}'.format(vni), ip, mask)

    @staticmethod
    def delete_vxlan(engine, vxlan_info):
        """
        Method which remove VXLAN from Linux device
        :param engine: ssh engine object
        :param vxlan_info: vxlan info dictionary
        Example: {'vtep_name': 'vxlan76543', 'vtep_src_ip': '10.1.1.32', 'vtep_dst_ip': '10.1.0.32', 'vni': 76543,
                'vtep_ips': [('23.45.0.1', '24')]}
        :return: command output
        """
        LinuxInterfaceCli.del_interface(engine, 'br_{}'.format(vxlan_info['vni']))
        LinuxInterfaceCli.del_interface(engine, vxlan_info['vtep_name'])

    @staticmethod
    def add_vtep(engine, vtep_name, src_ip, vni, dst_ip=False):
        """
        Method which adding VTEP to Linux device
        :param engine: ssh engine object
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

        return engine.run_cmd(cmd)
