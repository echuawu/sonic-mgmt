from ngts.cli_wrappers.common.ifconfig_clis_common import IfconfigCliCommon


class SonicIfconfigCli(IfconfigCliCommon):
    """
    This class is for ifconfig cli commands for sonic only
    """

    def __init__(self, engine):
        self.engine = engine
