from ngts.cli_wrappers.common.vlan_clis_common import VlanCliCommon


class SonicVlanCli(VlanCliCommon):

    @staticmethod
    def configure_vlan_and_add_ports(engine, vlan_info):
        """
        Method which adding VLAN and ports to VLAN on SONiC device
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        SonicVlanCli.add_vlan(engine, vlan_info['vlan_id'])
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                SonicVlanCli.add_port_to_vlan(engine, vlan_port, vlan_info['vlan_id'], mode)

    @staticmethod
    def delete_vlan_and_remove_ports(engine, vlan_info):
        """
        Method which remove ports from VLANs and VLANs on SONiC device
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                SonicVlanCli.del_port_from_vlan(engine, vlan_port, vlan_info['vlan_id'])
        SonicVlanCli.del_vlan(engine, vlan_info['vlan_id'])

    @staticmethod
    def add_vlan(engine, vlan):
        """
        Method which adding VLAN to SONiC dut
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan add {}".format(vlan))

    @staticmethod
    def del_vlan(engine, vlan):
        """
        Method which removing VLAN from SONiC dut
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan del {}".format(vlan))

    @staticmethod
    def add_port_to_vlan(engine, port, vlan, mode='trunk'):
        """
        Method which adding physical port to VLAN on SONiC dut
        :param engine: ssh engine object
        :param port: network port which should be VLAN member
        :param vlan: vlan ID
        :param mode: port mode - access or trunk
        :return: command output
        """
        if mode == 'trunk':
            return engine.run_cmd("sudo config vlan member add {} {}".format(vlan, port))
        elif mode == 'access':
            return engine.run_cmd("sudo config vlan member add --untagged {} {}".format(vlan, port))
        else:
            raise Exception('Incorrect port mode: "{}" provided, expected "trunk" or "access"')

    @staticmethod
    def del_port_from_vlan(engine, port, vlan):
        """
        Method which deleting physical port from VLAN on SONiC dut
        :param engine: ssh engine object
        :param port: network port which should be deleted from VLAN members
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan member del {} {}".format(vlan, port))

    @staticmethod
    def show_vlan_config(engine):
        """
        This method performs show vlan command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd("show vlan config")

    @staticmethod
    def shutdown_vlan(engine, vlan):
        """
        This method is to shutdown vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo ip link set dev Vlan{} down".format(vlan))

    @staticmethod
    def startup_vlan(engine, vlan):
        """
        This method is to startup vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo ip link set dev Vlan{} up".format(vlan))

    @staticmethod
    def disable_vlan_arp_proxy(engine, vlan):
        """
        This method is to disable arp proxy in vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan proxy_arp {} disabled".format(vlan), validate=True)

    @staticmethod
    def enable_vlan_arp_proxy(engine, vlan):
        """
        This method is to enable arp proxy in vlan
        :param engine: ssh engine object
        :param vlan: vlan ID
        :return: command output
        """
        return engine.run_cmd("sudo config vlan proxy_arp {} enabled".format(vlan), validate=True)
