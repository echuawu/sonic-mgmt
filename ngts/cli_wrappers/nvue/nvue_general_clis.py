import logging
import allure
from retry import retry
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCliDefault
from ngts.constants.constants_nvos import NvosConst
logger = logging.getLogger()


class NvueGeneralCli(SonicGeneralCliDefault):

    """
    This class is for general cli commands for NVOS only
    Most of the methods are inherited from SonicGeneralCli
    """

    def __init__(self, engine):
        self.engine = engine

    @retry(Exception, tries=15, delay=10)
    def verify_dockers_are_up(self, dockers_list=NvosConst.DOCKERS_LIST):
        """
        Verifying the dockers are in up state during a specific time interval
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of one or more dockers are down
        """
        with allure.step("Validate dockers are up"):
            NvueGeneralCli._verify_dockers_are_up(self, dockers_list)

    def _verify_dockers_are_up(self, dockers_list):
        """
        Verifying the dockers are in up state during a specific time interval
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of one or more dockers are down
        """
        err_flag = True
        for docker in dockers_list:
            cmd_output = self.engine.run_cmd('docker ps | grep {}'.format(docker))
            if NvosConst.DOCKER_STATUS not in cmd_output:
                logger.error("{} docker is not up".format(docker))
                err_flag = False
        assert err_flag, "one or more dockers are down"

    def verify_installed_extensions_running(self):
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
