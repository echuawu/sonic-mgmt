from ngts.cli_wrappers.common.vrf_clis_common import VrfCliCommon


class SonicVrfCli(VrfCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_vrf(self, vrf):
        """
        This method creates VRF
        :param vrf: vrf name which should be created
        :return: command output
        """
        return self.engine.run_cmd("sudo config vrf add {}".format(vrf))

    def del_vrf(self, vrf):
        """
        This method deletes VRF
        :param vrf: vrf name which should be deleted
        :return: command output
        """
        return self.engine.run_cmd("sudo config vrf del {}".format(vrf))

    def add_interface_to_vrf(self, interface, vrf):
        """
        This method moves interface from default VRF to specific
        :param interface: interface name which should be moved
        :param vrf: vrf name to which move interface
        :return: command output
        """
        return self.engine.run_cmd("sudo config interface vrf bind {} {}".format(interface, vrf))

    def del_interface_from_vrf(self, interface, vrf):
        """
        This method moves interface from specific VRF to default
        :param interface: interface name which should be moved
        :param vrf: vrf name from which move interface
        :return: command output
        """
        return self.engine.run_cmd("sudo config interface vrf unbind {}".format(interface))
