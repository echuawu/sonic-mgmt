from ngts.cli_wrappers.common.chassis_clis_common import ChassisCliCommon


class LinuxChassisCli(ChassisCliCommon):
    """
    This class is for chassis cli commands for linux only
    """

    def __init__(self, engine):
        self.engine = engine
