from ngts.cli_wrappers.common.route_clis_common import RouteCliCommon


class LinuxRouteCli(RouteCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_del_route(self, action, dst, via, dst_mask, vrf):
        """
        This method create/remove static IP route
        :param action: action which should be executed - add or del
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add/remove route in custom vrf
        :return: command output
        """
        if vrf:
            raise NotImplementedError('VRF not supported for Linux host')
        if action not in ['add', 'del']:
            raise NotImplementedError('Incorrect action {} provided, supported only add/del'.format(action))

        return self.engine.run_cmd("sudo ip route {} {}/{} via {}".format(action, dst, dst_mask, via))

    def add_route(self, dst, via, dst_mask, vrf=None):
        """
        This method create static IP route
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add route in custom vrf
        :return: command output
        """
        self.add_del_route('add', dst, via, dst_mask, vrf)

    def del_route(self, dst, via, dst_mask, vrf=None):
        """
        This method deletes static IP route
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to del route in custom vrf
        :return: command output
        """
        self.add_del_route('del', dst, via, dst_mask, vrf)
