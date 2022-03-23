from ngts.cli_wrappers.common.vlan_clis_common import VlanCliCommon


class LinuxVlanCli(VlanCliCommon):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj

    def configure_vlan_and_add_ports(self, vlan_info):
        """
        This method create a list a vlan interfaces, according to the dictionary provided by the user
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                self.add_vlan_interface(vlan_port, vlan_info['vlan_id'])
                vlan_iface = '{}.{}'.format(vlan_port, vlan_info['vlan_id'])
                self.cli_obj.interface.enable_interface(vlan_iface)

    def delete_vlan_and_remove_ports(self, vlan_info):
        """
        This method deletes a vlan interface
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                self.del_vlan_interface(vlan_port, vlan_info['vlan_id'])

    def add_vlan_interface(self, interface, vlan):
        """
        This method creates a VLAN interface on Linux host
        :param interface: linux interface name on top of it we will create vlan interface
        :param vlan: vlan ID
        :return: command output
        """
        vlan_interface = '{}.{}'.format(interface, vlan)
        return self.engine.run_cmd("sudo ip link add link {} name {} type vlan id {}".format(interface, vlan_interface,
                                                                                             vlan))

    def del_vlan_interface(self, interface, vlan):
        """
        This method deletes a VLAN interface on Linux host
        :param interface: linux interface name on top of it we will remove vlan interface
        :param vlan: vlan ID
        :return: command output
        """
        vlan_interface = '{}.{}'.format(interface, vlan)
        return self.engine.run_cmd("sudo ip link del {}".format(vlan_interface))
