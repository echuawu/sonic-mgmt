import logging
import allure
import time
from retry import retry
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCliDefault
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.constants.constants_nvos import NvosConst, ActionConsts
from ngts.constants.constants import InfraConst

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
    def diff_config(engine, revision_1='', revision_2='', output_type='json'):
        logging.info("Running 'nv config diff' on dut")
        cmd = 'nv config diff ' + revision_1 + ' ' + revision_2
        output = engine.run_cmd(cmd + ' --output {output_type}'.format(output_type=output_type))
        return output

    @staticmethod
    def history_config(engine, revision='', output_type='json'):
        logging.info("Running 'nv config history' on dut")
        cmd = 'nv config history ' + revision
        output = engine.run_cmd(cmd + ' --output {output_type}'.format(output_type=output_type))
        return output

    @staticmethod
    def show_config(engine, output_type='json'):
        logging.info("Running 'nv config show' on dut")
        output = engine.run_cmd('nv config show --output {output_type}'.format(output_type=output_type))
        return output

    @staticmethod
    def replace_config(engine, file, output_type='json'):
        logging.info("Running 'nv config replace' on dut")
        output = engine.run_cmd('nv config replace {file} --output {output_type}'.format(file=file,
                                                                                         output_type=output_type))
        return output

    @staticmethod
    def save_config(engine):
        logging.info("Running 'nv config save' on dut")
        output = engine.run_cmd('nv config save')

        return output

    @staticmethod
    def patch_config(engine, file, output_type='json'):
        logging.info("Running 'nv config patch' on dut")
        output = engine.run_cmd('nv config patch {file} --output {output_type}'.format(file=file,
                                                                                       output_type=output_type))
        return output

    @staticmethod
    def apply_config(engine, ask_for_confirmation=False, option=''):
        """
        Apply configuration
        :param option: could be [-y, --assume-yes, --assume-no, --confirm-yes, --confirm-no, --confirm-status]
        :param engine: ssh engine object
        :param ask_for_confirmation: True or False
        """
        logging.info("Checking the config to be applied")
        NvueGeneralCli.diff_config(engine=engine)

        logging.info("Running 'nv config apply' on dut")
        if ask_for_confirmation:
            output = engine.run_cmd_set(['nv config apply', 'y'], patterns_list=[r"Are you sure?"],
                                        tries_after_run_cmd=1)
            if 'Declined apply after warnings' in output:
                output = "Error: " + output
            elif 'y: command not found' in output and 'applied' in output:
                output = 'applied'
        else:
            output = engine.run_cmd('nv {option} config apply'.format(option=option))
        return output

    @staticmethod
    def detach_config(engine):
        logging.info("Running 'nv config detach' on dut")
        output = engine.run_cmd('nv config detach')
        return output

    @staticmethod
    @retry(Exception, tries=20, delay=10)
    def wait_for_nvos_to_become_functional(engine):
        """
        Waiting for NVOS to complete the init and become functional after the installation
        """
        logger.info('Checking the status of nvued ')
        if ("active (running)" not in engine.run_cmd("sudo systemctl status nvued")) and \
           ("active (running)" not in engine.run_cmd("sudo systemctl status nvue")):
            raise Exception("Waiting for NVUE to become functional")

    @staticmethod
    def upgrade_dut(engine, path_to_image):
        """
        Installing the provided image on dut
        """
        logging.info("Installing {}".format(path_to_image))

        with allure.step("Copying image to dut"):
            logging.info("Copy image from {src} to {dest}".format(src=path_to_image,
                                                                  dest=NvosConst.IMAGES_PATH_ON_SWITCH))
            if not path_to_image.startswith('http'):
                image_path = '{}{}'.format(InfraConst.HTTP_SERVER, path_to_image)
                engine.run_cmd('sudo curl {} -o {}'.format(image_path, NvosConst.IMAGES_PATH_ON_SWITCH), validate=True)

        with allure.step("Installing image {}".format(NvosConst.IMAGES_PATH_ON_SWITCH)):
            logging.info("Installing image '{}'".format(NvosConst.IMAGES_PATH_ON_SWITCH))
            NvueSystemCli.action_image(engine=engine, action_str=ActionConsts.INSTALL,
                                       action_component_str="image", op_param=NvosConst.IMAGES_PATH_ON_SWITCH)

        with allure.step("Reboot dut"):
            NvueGeneralCli.reboot(engine)

        with allure.step("Verifying NVOS initialized successfully"):
            NvueGeneralCli.verify_dockers_are_up()
            NvueGeneralCli.wait_for_nvos_to_become_functional(engine)

    @staticmethod
    def upgrade_firmware(engine, path_to_fw_img):
        """
        Installing provided firmware image on dut
        """
        logging.info("Installing platform firmware")

        with allure.step("Copying firmware image to dut"):
            logging.info("Copy fw from {src} to {dest}".format(src=path_to_fw_img,
                                                               dest=NvosConst.FM_PATH_ON_SWITCH))
            if not path_to_fw_img.startswith('http'):
                fw_image_path = '{}{}'.format(InfraConst.HTTP_SERVER, path_to_fw_img)
                engine.run_cmd('sudo curl {} -o {}'.format(fw_image_path, NvosConst.FM_PATH_ON_SWITCH), validate=True)

        with allure.step("Install system firmware file - " + NvosConst.FM_PATH_ON_SWITCH):
            NvueSystemCli.action_firmware_install(engine=engine, action_component_str="firmware",
                                                  op_param=NvosConst.FM_PATH_ON_SWITCH)

        with allure.step("Reboot dut"):
            NvueGeneralCli.reboot(engine)

        with allure.step("Verifying NVOS initialized successfully"):
            NvueGeneralCli.verify_dockers_are_up()
            NvueGeneralCli.wait_for_nvos_to_become_functional(engine)
