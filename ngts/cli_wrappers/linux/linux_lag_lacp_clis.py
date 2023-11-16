from ngts.cli_wrappers.common.lag_lacp_clis_common import LagLacpCliCommon


class LinuxLagLacpCli(LagLacpCliCommon):

    def __init__(self, engine, cli_obj):
        self.engine = engine
        self.cli_obj = cli_obj

    def create_lag_interface_and_assign_physical_ports(self, lag_lacp_info):
        """
        This method applies LAG configuration, according to the parameters specified in the configuration dict
        :param lag_lacp_info: configuration dictionary with all LAG/LACP related info
        Syntax: {'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}
        Example: {'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}
        """
        lag_lacp_iface_name = lag_lacp_info['name']
        lag_type = lag_lacp_info['type']
        if lag_type == 'lag':
            self.engine.run_cmd("sudo teamd -t {} -d".format(lag_lacp_iface_name))
        elif lag_type == 'lacp':
            self.engine.run_cmd("sudo teamd -t {} -d -c '{{\"runner\": {{\"name\": \"lacp\"}}}}'".format(lag_lacp_iface_name))
        else:
            raise Exception('Unknown lag type was provided by the user: {}. The valid types are: lacp.'
                            .format(lag_type))
        for member_port in lag_lacp_info['members']:
            self.cli_obj.interface.disable_interface(member_port)
            self.cli_obj.interface.add_port_to_bond(member_port, lag_lacp_iface_name)
            self.cli_obj.interface.enable_interface(member_port)

        self.cli_obj.interface.enable_interface(lag_lacp_iface_name)

    def delete_lag_interface_and_unbind_physical_ports(self, lag_lacp_info):
        """
        This method deletes LAG configuration, according to the parameters specified in the configuration dict
        :param lag_lacp_info: configuration dictionary with all LAG/LACP related info
        Syntax: {'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}
        Example: {'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}
        """
        lag_lacp_iface_name = lag_lacp_info['name']
        self.engine.run_cmd("sudo ip link set {} nomaster".format(lag_lacp_iface_name))
        for member_port in lag_lacp_info['members']:
            self.engine.run_cmd("sudo ip link set {} nomaster".format(member_port))
            self.engine.run_cmd("sudo ip link set {} up".format(member_port))
        self.cli_obj.interface.del_interface(lag_lacp_iface_name)

    def set_bond_mode(self, bond_name, bond_mode):
        """
        This method sets bond mode for a given bond name
        :param bond_name: bond interface name
        :param bond_mode: bond mode which will be set
        :return: command output
        """
        return self.engine.run_cmd("sudo ip link set dev {} type bond mode {}".format(bond_name, bond_mode))
