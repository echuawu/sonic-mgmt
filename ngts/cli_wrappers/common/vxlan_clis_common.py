from ngts.cli_wrappers.interfaces.interface_vxlan_clis import VxlanCliInterface


class VxlanCliCommon(VxlanCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass
