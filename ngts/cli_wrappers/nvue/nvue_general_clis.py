import logging
import allure
import time
from retry import retry
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCliDefault
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.nvos_constants.constants_nvos import NvosConst, ActionConsts
from ngts.constants.constants import InfraConst
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine


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
        return self.engine.run_cmd('nv show system version')

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
    def apply_config(engine, ask_for_confirmation=False, option='', validate_apply_message=''):
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
        elif validate_apply_message:
            output = engine.run_cmd('nv {option} config apply'.format(option=option))
            assert validate_apply_message in output, 'Message {0} not exist in output {1}'.\
                format(validate_apply_message, output)
        else:
            output = engine.run_cmd('nv {option} config apply'.format(option=option))
        return output

    @staticmethod
    def detach_config(engine):
        logging.info("Running 'nv config detach' on dut")
        output = engine.run_cmd('nv config detach')
        return output

    @staticmethod
    def apply_empty_config(engine):
        logging.info("Running 'nv config apply empty' on dut")
        output = engine.run_cmd_set(['nv config apply empty', 'y'],
                                    patterns_list=[r"Are you sure?"],
                                    tries_after_run_cmd=1)
        if 'Declined apply after warnings' in output or "Aborted apply after warnings" in output:
            output = "Error: " + output
        elif 'y: command not found' in output and 'applied' in output:
            output = 'applied'
        return "applied" in output

    @staticmethod
    def list_commands(engine):
        logging.info("Running 'nv list-commands' on dut")
        output = engine.run_cmd('nv list-commands')
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

    def remote_reboot(self, topology_obj):
        '''
        @summary: perform remote reboot from the physical server using the noga remote reboot command,
        usually the command should be like this: '/auto/mswg/utils/bin/rreboot <ip|hostname>'
        '''
        cmd = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']['Specific'][
            'remote_reboot']
        assert cmd, "Reboot command is empty"
        topology_obj.players['server']['engine'].run_cmd(cmd)

    def enter_serial_connection_context(self, topology_obj):
        '''
        @summary: in this function we will execute the rcon command and return the serial engine
        :return: serial connection engine
        '''
        att = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']
        # add connection options to pass connection problems
        extended_rcon_command = att['Specific']['serial_conn_cmd'].split(' ')
        extended_rcon_command.insert(1, DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS)
        extended_rcon_command = ' '.join(extended_rcon_command)
        serial_engine = PexpectSerialEngine(ip=att['Specific']['ip'],
                                            username=att['Topology Conn.']['CONN_USER'],
                                            password=att['Topology Conn.']['CONN_PASSWORD'],
                                            rcon_command=extended_rcon_command,
                                            timeout=120)
        # we don't want to login to switch becuase we are doing remote reboot
        serial_engine.create_serial_engine(login_to_switch=False)
        return serial_engine

    def enter_onie_install_mode(self, topology_obj):
        '''
        @summary: in this function we want to enter install mode,
        we are doing so by the following step:
            1.create a serial engine
            2.remote reboot
            3.wait till GRUB menu appears:
                a. if the NVOS grub menu appears then select ONIE entry (pressing down 2 key arrows)
                b. if the ONIE grun menu appears just do nothing (the install entry will be marked and after 5 secs it
                will enter the install mode)
        '''
        logger.info("Initializing serial connection to device")
        serial_engine = self.enter_serial_connection_context(topology_obj)
        logger.info('Executing remote reboot')
        self.remote_reboot(topology_obj)
        logger.info("Enter ONIE install mode")
        output, respond = serial_engine.run_cmd('', ['ONIE\\s+', '\\*ONIE: Install OS'], timeout=240,
                                                send_without_enter=True)
        if respond == 0:
            logger.info("System in NVOS grub menu, entering ONIE grub menu")
            for i in range(2):
                logger.info("Sending one arrow down")
                serial_engine.run_cmd("\x1b[B", expected_value='.*', send_without_enter=True)

            if "MLNX_" in topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific'].get('TYPE', ''):
                serial_engine.run_cmd('\r', 'Due to security constraints, this option will uninstall your current OS',
                                      timeout=60, send_without_enter=True)
                serial_engine.run_cmd('YES', '\\*ONIE: Install OS', timeout=420)

        logger.info("Pressing Enter to enter ONIE menu")
        self.wait_for_onie_prompt(serial_engine)

    def prepare_for_installation(self, topology_obj):
        '''
        @summary: in this function we will enter onie install mode using remolte reboot
        '''
        switch_in_onie = False
        try:
            self.enter_onie(topology_obj)
            switch_in_onie = True
        except Exception as err:
            logger.info("Got an exception: {}".format(str(err)))
            switch_in_onie = False
        finally:
            return switch_in_onie

    @retry(Exception, tries=4, delay=5)
    def wait_for_onie_prompt(self, serial_engine):
        serial_engine.run_cmd('\r', ['Please press Enter to activate this console', 'ONIE:/\\s+'], timeout=60)

    @retry(Exception, tries=3, delay=5)
    def enter_onie(self, topology_obj):
        self.enter_onie_install_mode(topology_obj)

    def confirm_in_onie_install_mode(self, topology_obj):
        pass
