import logging

from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli

logger = logging.getLogger()


class NvueGeneralCli(SonicGeneralCli):
    """
    This class is for general cli commands for NVOS only
    Most of the methods are inherited from SonicGeneralCli
    """

    @staticmethod
    def verify_dockers_are_up(engine, dockers_list=None):
        """
        Verifying the dockers are in up state during a specific time interval
        :param engine: ssh engine object
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        # TODO: To implement the flow
        pass

    @staticmethod
    def verify_installed_extensions_running(dut_engine):
        """
        This method is not relevant for NVOS (at least for now)
        """
        pass
