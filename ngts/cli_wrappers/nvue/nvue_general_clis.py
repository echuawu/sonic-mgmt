import logging

from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCliDefault

logger = logging.getLogger()


class NvueGeneralCli(SonicGeneralCliDefault):
    """
    This class is for general cli commands for NVOS only
    Most of the methods are inherited from SonicGeneralCli
    """

    def __init__(self, engine):
        self.engine = engine

    def verify_dockers_are_up(self, dockers_list=None):
        """
        Verifying the dockers are in up state during a specific time interval
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        # TODO: To implement the flow
        pass

    def verify_installed_extensions_running(self, cli_object):
        """
        This method is not relevant for NVOS (at least for now)
        """
        pass

    def show_version(self):
        return self.engine.run_cmd('show version')

    @staticmethod
    def apply_config(engine):
        """
        Apply configuration
        :param engine: ssh engine object
        """
        logging.info("Running 'nv config apply' on dut")
        return engine.run_cmd('nv config apply')
