from ngts.cli_wrappers.interfaces.interface_flowcnt_clis import FlowcntCliInterface


class FlowcntCliCommon(FlowcntCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    def __init__(self):
        pass
