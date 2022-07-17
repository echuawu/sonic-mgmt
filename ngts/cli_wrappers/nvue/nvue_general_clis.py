import logging
import allure
import time
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

    @retry(Exception, tries=25, delay=10)
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
            if NvosConst.DOCKER_STATUS_UP not in cmd_output:
                logger.error("{} docker is not up".format(docker))
                err_flag = False
        assert err_flag, "one or more dockers are down"

    def verify_installed_extensions_running(self):
        """
        This method is not relevant for NVOS (at least for now)
        """
        pass

    def show_version(self, validate=False):
        return self.engine.run_cmd('show version')

    @staticmethod
    def apply_config(engine, ask_for_confirmation=False):
        """
        Apply configuration
        :param engine: ssh engine object
        :param ask_for_confirmation: True or False
        """
        logging.info("Running 'nv config apply' on dut")
        if ask_for_confirmation:
            output = engine.run_cmd_set(['nv config apply', 'y'], patterns_list=[r"Are you sure?"],
                                        tries_after_run_cmd=1)
            if 'Declined apply after warnings' in output:
                output = "Error: " + output
            elif 'y: command not found' in output and 'applied' in output:
                output = 'applied'
        else:
            output = engine.run_cmd('nv config apply')
        return output

    @staticmethod
    def detach_config(engine):
        logging.info("Running 'nv config detach' on dut")
        output = engine.run_cmd('nv config detach')
        return output

    @staticmethod
    def reboot(engine):
        """
        Rebooting the switch
        """
        logger.info('Reboot Switch')
        return engine.run_cmd('sudo reboot')

    @staticmethod
    @retry(Exception, tries=20, delay=10)
    def wait_for_nvos_to_become_functional(engine):
        """
        Waiting for NVOS to complete the init and become functional after the installation
        """
        logger.info('Checking the status of nvue ')
        if "active (running)" not in engine.run_cmd("sudo systemctl status nvue"):
            raise Exception("Waiting for NVUE to become functional")
