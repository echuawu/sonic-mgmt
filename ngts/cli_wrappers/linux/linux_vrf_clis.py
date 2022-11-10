from ngts.cli_wrappers.common.vrf_clis_common import VrfCliCommon


class LinuxVrfCli(VrfCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_vrf(self, vrf):
        """
        This method create VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be created
        :return: command output
        """
        raise NotImplementedError

    def del_vrf(self, vrf):
        """
        This method deletes VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be deleted
        :return: command output
        """
        raise NotImplementedError

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
