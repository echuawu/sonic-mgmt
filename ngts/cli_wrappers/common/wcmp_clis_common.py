from ngts.cli_wrappers.interfaces.interface_wcmp_clis import WcmpCliInterface


class WcmpCliCommon(WcmpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass
