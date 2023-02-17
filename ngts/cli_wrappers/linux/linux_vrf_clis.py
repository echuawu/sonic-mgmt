from ngts.cli_wrappers.common.vrf_clis_common import VrfCliCommon


class LinuxVrfCli(VrfCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_vrf(self, vrf, table=10):
        """
        This method create VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be created
        :param table: the routing table that associated with vrf
        :return: command output
        """
        create_vrf_and_bind_table = f"sudo ip link add {vrf} type vrf table {table}"
        create_egress_ip_rule = f"sudo ip rule add oif {vrf} table {table}"
        create_ingress_ip_rule = f"sudo ip rule add iif {vrf} table {table}"
        set_vrf_up = f"sudo ip link set up {vrf}"

        self.engine.run_cmd(create_vrf_and_bind_table)
        self.engine.run_cmd(create_egress_ip_rule)
        self.engine.run_cmd(create_ingress_ip_rule)
        self.engine.run_cmd(set_vrf_up)

    def del_vrf(self, vrf):
        """
        This method deletes VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be deleted
        :return: command output
        """
        self.engine.run_cmd(f"sudo ip link del {vrf}")

    def add_interface_to_vrf(self, interface, vrf):
        """
        This method move interface from default VRF to specific
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name to which move interface
        :return: command output
        """
        raise NotImplementedError

    def del_interface_from_vrf(self, interface, vrf):
        """
        This method move interface from specific VRF to default
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name from which move interface
        :return: command output
        """
        raise NotImplementedError
