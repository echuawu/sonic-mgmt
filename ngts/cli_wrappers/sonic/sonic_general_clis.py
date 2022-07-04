import re
import allure
import logging
import time
import netmiko
import json
import traceback
import os
from retry import retry
from retry.api import retry_call

from ngts.cli_util.cli_constants import SonicConstant
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.linux.linux_general_clis import LinuxGeneralCli
from ngts.helpers.run_process_on_host import run_process_on_host
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from infra.tools.exceptions.real_issue import RealIssue
from ngts.constants.constants import SonicConst, InfraConst, ConfigDbJsonConst, \
    AppExtensionInstallationConstants, DefaultCredentialConstants, BluefieldConstants
from ngts.helpers.breakout_helpers import get_port_current_breakout_mode, get_all_split_ports_parents, \
    get_split_mode_supported_breakout_modes, get_split_mode_supported_speeds, get_all_unsplit_ports
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
import ngts.helpers.json_file_helper as json_file_helper
from ngts.helpers.interface_helpers import get_dut_default_ports_list
from ngts.tests.nightly.app_extension.app_extension_helper import get_installed_mellanox_extensions
from ngts.cli_wrappers.sonic.sonic_onie_clis import SonicOnieCli, OnieInstallationError
from ngts.tools.infra import ENV_LOG_FOLDER
from ngts.scripts.check_and_store_sanitizer_dump import check_sanitizer_and_store_dump


logger = logging.getLogger()
DUMMY_COMMAND = 'echo dummy_command'


class SonicGeneralCli:

    def __new__(cls, **kwargs):
        branch = kwargs.get('branch')
        engine = kwargs['engine']
        cli_obj = kwargs.get('cli_obj')
        dut_alias = kwargs.get('dut_alias', 'dut')

        supported_cli_classes = {'default': SonicGeneralCliDefault(engine, cli_obj, dut_alias),
                                 '202012': SonicGeneralCli202012(engine, cli_obj, dut_alias)}

        cli_class = supported_cli_classes.get(branch, supported_cli_classes['default'])
        cli_class_name = cli_class.__class__.__name__
        logger.info(f'Going to use General CLI class: {cli_class_name}')

        return cli_class


class SonicGeneralCliDefault(GeneralCliCommon):
    """
    This class is for general cli commands for sonic only
    """

    def __init__(self, engine, cli_obj, dut_alias):
        self.engine = engine
        self.cli_obj = cli_obj
        self.dut_alias = dut_alias

    def show_feature_status(self):
        """
        This method show feature status on the sonic switch
        :return: command output
        """
        return self.engine.run_cmd('show feature status')

    def show_and_parse_feature_status(self):
        """
        This method show feature status on the sonic switch
        :return: command output
        """
        output_content = self.show_feature_status()
        return generic_sonic_output_parser(output_content, output_key="Feature")

    def set_feature_state(self, feature_name, state):
        """
        This method to set feature state on the sonic switch
        :param feature_name: the feature name
        :param state: state
        """
        self.engine.run_cmd('sudo config feature state {} {}'.format(feature_name, state), validate=True)

    def get_installer_delimiter(self):
        dash_installer = 'sonic-installer'
        delimiter = '_'
        output = self.engine.run_cmd('which {}'.format(dash_installer))
        if dash_installer in output:
            delimiter = '-'
        return delimiter

    def install_image(self, image_path, delimiter='-', is_skipping_migrating_package=False):
        if not is_skipping_migrating_package:
            output = self.engine.run_cmd('sudo sonic{}installer install {} -y'.format(delimiter, image_path), validate=True)
        else:
            output = self.engine.run_cmd('sudo sonic{}installer install {} -y --skip-package-migration'.format(delimiter, image_path), validate=True)
        return output

    def get_image_binary_version(self, image_path, delimiter='-'):
        output = self.engine.run_cmd('sudo sonic{}installer binary{}version {}'.format(delimiter, delimiter, image_path),
                                     validate=True)
        return output

    def get_image_sonic_version(self):
        output = self.engine.run_cmd('sudo show boot')
        current_image = re.search(r"Current:\s*SONiC-OS-([\d|\w|\-]*)\..*", output, re.IGNORECASE).group(1)
        return current_image

    def set_default_image(self, image_binary, delimiter='-'):
        output = self.engine.run_cmd('sudo sonic{}installer set{}default {}'.format(delimiter, delimiter, image_binary),
                                     validate=True)
        return output

    def set_next_boot_entry_to_onie(self):
        self.engine.run_cmd('sudo grub-editenv /host/grub/grubenv set next_entry=ONIE', validate=True)

    def get_sonic_image_list(self, delimiter='-'):
        output = self.engine.run_cmd('sudo sonic{}installer list'.format(delimiter), validate=True)
        return output

    def load_configuration(self, config_file):
        self.engine.run_cmd('sudo config load -y {}'.format(config_file), validate=True)

    def reload_configuration(self, force=False):
        cmd = 'sudo config reload -y'
        if force:
            cmd += ' -f'
        self.engine.run_cmd(cmd, validate=True)

    def save_configuration(self):
        self.engine.run_cmd('sudo config save -y', validate=True)

    def download_file_from_http_url(self, url, target_file_path):
        self.engine.run_cmd('sudo curl {} -o {}'.format(url, target_file_path), validate=True)

    def reboot_reload_flow(self, r_type='reboot', ports_list=None, topology_obj=None, wait_after_ping=45, reload_force=False):
        """
        Wrapper for reboot and reload methods - which executes appropriate method based on reboot/reload type
        """
        if r_type == 'config reload -y':
            self.reload_flow(ports_list, topology_obj, reload_force)
        else:
            self.reboot_flow(r_type, ports_list, topology_obj, wait_after_ping)

    def reboot_flow(self, reboot_type='reboot', ports_list=None, topology_obj=None, wait_after_ping=45):
        """
        Rebooting switch by given way(reboot, fast-reboot, warm-reboot) and validate dockers and ports state
        :param reboot_type: reboot type
        :param ports_list: list of the ports to check status after reboot
        :param topology_obj: topology object
        :param wait_after_ping: how long in second wait after ping before ssh connection
        :return: None, raise error in case of unexpected result
        """
        if not (ports_list or topology_obj):
            raise Exception('ports_list or topology_obj must be passed to reboot_flow method')
        if not ports_list:
            ports_list = topology_obj.players_all_ports[self.dut_alias]
        with allure.step('Reboot switch by CLI - sudo {}'.format(reboot_type)):
            self.safe_reboot_flow(topology_obj, reboot_type, wait_after_ping=wait_after_ping)
            self.port_reload_reboot_checks(ports_list)

    def safe_reboot_flow(self, topology_obj, reboot_type='reboot', wait_after_ping=45):
        self.engine.reload([f'sudo {reboot_type}'], wait_after_ping=wait_after_ping)
        sanitizer = topology_obj.players['dut']['sanitizer']
        if sanitizer:
            test_name = os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]
            dumps_folder = os.environ.get(ENV_LOG_FOLDER)
            check_sanitizer_and_store_dump(self.engine, dumps_folder, test_name)

    def reload_flow(self, ports_list=None, topology_obj=None, reload_force=False):
        """
        Reloading switch and validate dockers and ports state
        :param ports_list: list of the ports to check status after reboot
        :param topology_obj: topology object
        :param reload_force: provide if want to do reload with -f flag(force)
        :return: None, raise error in case of unexpected result
        """
        if not (ports_list or topology_obj):
            raise Exception('ports_list or topology_obj must be passed to reload_flow method')
        if not ports_list:
            ports_list = topology_obj.players_all_ports[self.dut_alias]
        with allure.step('Reloading dut'):
            logger.info("Reloading dut")
            self.reload_configuration(reload_force)
            self.port_reload_reboot_checks(ports_list)

    def port_reload_reboot_checks(self, ports_list):
        self.verify_dockers_are_up(SonicConst.DOCKERS_LIST)
        self.cli_obj.interface.check_link_state(ports_list)

    def validate_dockers_are_up_reboot_if_fail(self, retries=2):
        """
        Reboot and validate docker containers are up on the switch
        :param retries: int how many times do reboot of switch
        """
        initial_count = retries
        while retries:
            try:
                self.verify_dockers_are_up()
                break
            except BaseException:
                logger.error('Catched exception {} during verifing docker conatiners are up.'
                             ' Rebooting dut and try again, try number {}'.format(traceback.print_exc(),
                                                                                  initial_count - retries + 1))
                self.engine.reload(['sudo reboot'])
            retries = retries - 1

    @retry(Exception, tries=15, delay=10)
    def verify_dockers_are_up(self, dockers_list=None):
        """
        Verifying the dockers are in up state during a specific time interval
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        self._verify_dockers_are_up(dockers_list)

    def _verify_dockers_are_up(self, dockers_list):
        """
        Verifying the dockers are in up state
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        if dockers_list is None:
            dockers_list = SonicConst.DOCKERS_LIST_LEAF

            # Try to get extended docker list for DUT type ToRRouter
            try:
                config_db = self.get_config_db()
                if self.is_bluefield(config_db['DEVICE_METADATA']['localhost']['hwsku']):
                    dockers_list = SonicConst.DOCKERS_LIST_BF
                elif config_db['DEVICE_METADATA']['localhost']['type'] == 'ToRRouter':
                    dockers_list = SonicConst.DOCKERS_LIST_TOR
            except json.JSONDecodeError:
                logger.warning('Can not get device type from config_db.json. Unable to parse config_db.json file')
            except KeyError:
                logger.warning('Can not get device type from config_db.json. Key does not exist')

        for docker in dockers_list:
            try:
                self.engine.run_cmd('docker ps | grep {}'.format(docker), validate=True)
            except BaseException:
                raise Exception("{} docker is not up".format(docker))

    def verify_processes_of_dockers(self, docker_list, hwsku):
        """
        Verifying the processes of dockers are in RUNNING state
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        success = True
        if self.is_bluefield(hwsku):
            expected_processes = SonicConst.DAEMONS_DICT_BF
        else:
            expected_processes = SonicConst.DAEMONS_DICT

        for docker in docker_list:
            running_processes = []
            processes_output = self.engine.run_cmd(f'docker exec {docker} supervisorctl status')
            for process_info in processes_output.splitlines():
                logger.info(f"process info:   {process_info}")
                process_name = process_info.split()[0].strip()
                process_status = process_info.split()[1].strip()
                if process_name in expected_processes[docker] and process_status == "RUNNING":
                    running_processes.append(process_name)
            if len(running_processes) != len(expected_processes[docker]):
                logger.error(f"Not all expected processes of docker {docker} are running.\n"
                             f"Expected: {expected_processes[docker]}\nRunning: {running_processes}")
                success = False
        assert(success, 'Not all expected processes in RUNNING status')

    def generate_techsupport(self, duration=60):
        """
        Generate sysdump for a given time frame in seconds
        :param duration: time frame in seconds
        :return: dump path
        """
        with allure.step('Generate Techsupport of last {} seconds'.format(duration)):
            output = self.engine.run_cmd('sudo generate_dump -s \"-{} seconds\"'.format(duration))
            return output.splitlines()[-1]

    def do_installation(self, topology_obj, image_path, deploy_type, fw_pkg_path, platform_params):
        with allure.step('Preparing switch for installation'):
            in_onie = self.prepare_for_installation(topology_obj)

        if deploy_type == 'sonic':
            if in_onie:
                raise AssertionError("The request deploy type is 'sonic'(upgrade sonic to sonic)"
                                     " while the switch is running ONIE instead of SONiC OS.")
            self.deploy_sonic(image_path)

        if deploy_type == 'onie':
            self.deploy_onie(image_path, in_onie, fw_pkg_path, platform_params)

        if deploy_type == 'bfb':
            self.deploy_bfb(image_path, topology_obj)

        if deploy_type == 'pxe':
            self.deploy_pxe(image_path, topology_obj, platform_params['hwsku'])

    def deploy_image(self, topology_obj, image_path, apply_base_config=False, setup_name=None,
                     platform_params=None, wjh_deb_url=None, deploy_type='sonic',
                     reboot_after_install=None, fw_pkg_path=None, set_timezone='Israel', disable_ztp=False):
        if not image_path.startswith('http'):
            image_path = '{}{}'.format(InfraConst.HTTP_SERVER, image_path)
        try:
            with allure.step("Trying to install sonic image"):
                self.do_installation(topology_obj, image_path, deploy_type, fw_pkg_path, platform_params)
        except OnieInstallationError:
            with allure.step("Catched exception OnieInstallationError during install. Perform reboot and trying again"):
                logger.error('Catched exception OnieInstallationError during install. Perform reboot and trying again')
                self.engine.disconnect()
                self.remote_reboot(topology_obj)
                logger.info('Sleeping %s seconds to handle ssh flapping' % InfraConst.SLEEP_AFTER_RRBOOT)
                time.sleep(InfraConst.SLEEP_AFTER_RRBOOT)
                self.do_installation(topology_obj, image_path, deploy_type, fw_pkg_path, platform_params)

        if disable_ztp:
            with allure.step('Disable ZTP after image install'):
                retry_call(self.cli_obj.ztp.disable_ztp,
                           fargs=[],
                           tries=3,
                           delay=10,
                           logger=logger)
                self.save_configuration()

        if reboot_after_install:
            with allure.step("Validate dockers are up, reboot if any docker is not up"):
                self.validate_dockers_are_up_reboot_if_fail()

        if set_timezone:
            with allure.step("Set dut NTP timezone to {} time.".format(set_timezone)):
                dut_engine = topology_obj.players['dut']['engine']
                dut_engine.run_cmd('sudo timedatectl set-timezone {}'.format(set_timezone), validate=True)

        if apply_base_config:
            with allure.step("Apply port_config.ini and config_db.json"):
                self.apply_basic_config(topology_obj, setup_name, platform_params)

        if wjh_deb_url:
            with allure.step("Installing wjh deb url"):
                self.install_wjh(wjh_deb_url)

        with allure.step("Validate dockers are up"):
            self.verify_dockers_are_up()
        with allure.step("Validate app extensions are up"):
            self.verify_installed_extensions_running()
        self.configure_dhclient_if_simx()

    def deploy_sonic(self, image_path, is_skipping_migrating_package=False):
        tmp_target_path = '/tmp/sonic-mellanox.bin'
        delimiter = self.get_installer_delimiter()

        with allure.step('Deploying image via SONiC'):
            self.configure_dhclient_if_simx()
            with allure.step('Copying image to dut'):
                self.download_file_from_http_url(image_path, tmp_target_path)

            with allure.step('Installing the image'):
                self.install_image(tmp_target_path, delimiter, is_skipping_migrating_package)

            with allure.step('Setting image as default'):
                image_binary = self.get_image_binary_version(tmp_target_path, delimiter)
                self.set_default_image(image_binary, delimiter)

        with allure.step('Rebooting the dut'):
            self.engine.reload(['sudo reboot'])

        with allure.step('Verifying installation'):
            with allure.step('Verifying dut booted with correct image'):
                # installer flavor might change after loading a different version
                delimiter = self.get_installer_delimiter()
                image_list = self.get_sonic_image_list(delimiter)
                assert 'Current: {}'.format(image_binary) in image_list

    def configure_dhclient_if_simx(self):
        if 'simx' in self.engine.run_cmd("hostname"):
            with allure.step('Configure dhclient on simx dut'):
                self.engine.run_cmd('sudo dhclient', validate=True)

    def deploy_bfb(self, image_path, topology_obj):
        sonic_cli_ssh_connect_timeout = 30
        rshim = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['Parent_device_NIC_name']
        hyper_engine = topology_obj.players['hyper']['engine']

        with allure.step('Installing image by "bfb-install" on server'):
            LinuxGeneralCli(hyper_engine).install_bfb_image(image_path=image_path, rshim_num=rshim)

        # Broken engine after install. Disconnect it. In next run_cmd, it will connect back
        self.engine.disconnect()

        with allure.step('Waiting for CLI bring-up after instalation'):
            logger.info('Waiting for CLI bring-up after instalation')
            time.sleep(sonic_cli_ssh_connect_timeout)

    def deploy_pxe(self, image_path, topology_obj, hwsku):
        bf_cli_ssh_connect_bringup = 480
        if not self.is_bluefield(hwsku):
            raise Exception('The installation via PXE available only for Bluefield Devices')

        with allure.step('Installing image by PXE'):
            logger.info('Installing image by PXE')

        self.update_bf_slinks_to_files(image_path, topology_obj)

        bmc_cli_obj = self.get_bf_bmc_cli_obj(topology_obj)
        with allure.step('Set next boot to PXE'):
            bmc_cli_obj.set_next_boot_pxe_bf()
        with allure.step('Reboot remotely the dut'):
            bmc_cli_obj.remote_reboot_bf()

        with allure.step(f'Wait {bf_cli_ssh_connect_bringup} seconds for downloading the image'):
            logger.info(f'Wait {bf_cli_ssh_connect_bringup} seconds for downloading the image')
            time.sleep(bf_cli_ssh_connect_bringup)

        with allure.step('Start to check if CLI connection is available'):
            logger.info('Start to check if CLI connection is available')
            retry_call(self.check_bf_cli_connection,
                       fargs=[],
                       tries=12,
                       delay=60,
                       logger=logger)

    def check_bf_cli_connection(self):
        """
        This function checks the connection to switch via mgmt.
        During installation the Bluefield have flapped ping,
        so it can't be checked in regular way.

        :return: exception if connection not available
        """
        self.engine.disconnect()
        self.engine.run_cmd(DUMMY_COMMAND, validate=True)

    def update_bf_slinks_to_files(self, image_path, topology_obj):
        """
        This function updating the symbolic links to Image and initramfs files
          for Bluefield device to required version.
        These links used by grub file via PXE boot.
        """
        with allure.step('Update soft links to Image and initramfs files'):
            logger.info('Update soft links to Image and initramfs files')

        if image_path.startswith('http'):
            image_path = '/auto' + image_path.split('/auto')[1]

        image_path = os.path.realpath(image_path)  # in case provided image as symbolic link(for example the latest)

        pxe_dir_path = image_path[:image_path.rfind('/')] + '/pxe'
        switch_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']

        slink_image = BluefieldConstants.BASE_SLINK_BF_IMAGE.format(switch_name)
        slink_initramfs = BluefieldConstants.BASE_SLINK_BF_INITRAMFS.format(switch_name)

        self.update_bf_slink(slink_image, pxe_dir_path, 'Image')
        self.update_bf_slink(slink_initramfs, pxe_dir_path, 'initramfs')

    @staticmethod
    def update_bf_slink(slink, pxe_dir_path, file):
        logger.info(f'Update symbolic link {slink} to the file {pxe_dir_path}/{file}')
        if os.path.exists(slink):
            os.remove(slink)
        create_slink_cmd = f'ln -s {pxe_dir_path}/{file} {slink}'
        os.system(create_slink_cmd)

    @staticmethod
    def get_bf_bmc_cli_obj(topology_obj):
        bmc_ip = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['BF Switch']['bmc']
        bmc_engine = LinuxSshEngine(ip=bmc_ip,
                                    username=BluefieldConstants.BMC_USER,
                                    password=BluefieldConstants.BMC_PASS)
        return LinuxGeneralCli(bmc_engine)

    def deploy_onie(self, image_path, in_onie=False, fw_pkg_path=None, platform_params=None):
        if not in_onie:
            with allure.step('Setting boot order to onie'):
                self.set_next_boot_entry_to_onie()
            with allure.step('Rebooting the switch'):
                self.engine.reload(['sudo reboot'], wait_after_ping=25, ssh_after_reload=False)
        SonicOnieCli(self.engine.ip, fw_pkg_path, platform_params).update_onie()
        self.install_image_onie(self.engine.ip, image_path)

    @staticmethod
    def install_image_onie(dut_ip, image_url):
        sonic_cli_ssh_connect_timeout = 10

        with allure.step('Installing image by "onie-nos-install"'):
            SonicOnieCli(dut_ip).install_image(image_url=image_url)

        with allure.step('Waiting for switch shutdown after reload command'):
            logger.info('Waiting for switch shutdown after reload command')
            ping_till_alive(False, dut_ip)

        with allure.step('Waiting for switch bring-up after reload'):
            logger.info('Waiting for switch bring-up after reload')
            ping_till_alive(True, dut_ip)

        with allure.step('Waiting for CLI bring-up after reload'):
            logger.info('Waiting for CLI bring-up after reload')
            time.sleep(sonic_cli_ssh_connect_timeout)

    def check_is_alive_and_revive(self, topology_obj):
        ip = self.engine.ip
        try:
            logger.info('Checking whether device is alive')
            ping_till_alive(should_be_alive=True, destination_host=ip, tries=2)
            logger.info('Device is alive')
        except RealIssue:
            logger.info('Device is not alive, reviving')
            self.remote_reboot(topology_obj)
            logger.info('Device is revived')
        return True

    def remote_reboot(self, topology_obj):
        ip = self.engine.ip
        logger.info('Executing remote reboot')
        cmd = topology_obj.players[self.dut_alias]['attributes'].noga_query_data['attributes']['Specific']['remote_reboot']
        _, _, rc = run_process_on_host(cmd)
        if rc == InfraConst.RC_SUCCESS:
            ping_till_alive(should_be_alive=True, destination_host=ip)
        else:
            raise Exception('Remote reboot rc is other then 0')

    def prepare_for_installation(self, topology_obj):
        switch_in_onie = False
        self.check_is_alive_and_revive(topology_obj)
        try:
            # Checking if device is in sonic
            self.engine.run_cmd(DUMMY_COMMAND, validate=True)
        except netmiko.ssh_exception.NetmikoAuthenticationException:
            self.if_other_credentials_used_set_boot_order_onie()
            logger.info('Next boot set to onie succeed')

            SonicOnieCli(self.engine.ip).confirm_onie_boot_mode_install()
            switch_in_onie = True
        return switch_in_onie

    def apply_basic_config(self, topology_obj, setup_name, platform_params, reload_before_qos=False):
        platform = platform_params['platform']
        hwsku = platform_params['hwsku']
        shared_path = '{}{}{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_name)

        self.upload_port_config_ini(platform, hwsku, shared_path)
        self.upload_config_db_file(topology_obj, setup_name, hwsku, shared_path)

        with allure.step("Reboot the dut"):
            self.engine.reload(['sudo reboot'])
            if reload_before_qos:
                with allure.step("Reload the dut"):
                    self.reload_configuration(force=True)
            self.verify_dockers_are_up()

        with allure.step("Apply qos and dynamic buffer config"):
            self.cli_obj.qos.reload_qos()
            self.verify_dockers_are_up(dockers_list=['swss'])
            self.cli_obj.qos.stop_buffermgrd()
            self.cli_obj.qos.start_buffermgrd()
            self.save_configuration()

        with allure.step("Enable INFO logging on swss"):
            self.enable_info_logging_on_docker(docker_name='swss')
            self.save_configuration()

    def upload_port_config_ini(self, platform, hwsku, shared_path):
        switch_config_ini_path = "/usr/share/sonic/device/{}/{}/{}".format(platform, hwsku, SonicConst.PORT_CONFIG_INI)
        self.engine.run_cmd('sudo curl {}/{} -o {}'.format(shared_path,
                                                           SonicConst.PORT_CONFIG_INI,
                                                           switch_config_ini_path), validate=True)

    def upload_config_db_file(self, topology_obj, setup_name, hwsku, shared_path):
        config_db_file = self.get_updated_config_db(topology_obj, setup_name, hwsku)
        self.engine.run_cmd(
            'sudo curl {}/{} -o {}'.format(shared_path, config_db_file, SonicConst.CONFIG_DB_JSON_PATH), validate=True)

    def get_updated_config_db(self, topology_obj, setup_name, hwsku):
        config_db_file_name = "{}_config_db.json".format(self.get_image_sonic_version())
        base_config_db_json = self.get_config_db_json_obj(setup_name)
        self.create_extended_config_db_file(setup_name, base_config_db_json, file_name=config_db_file_name)
        self.update_config_db_metadata_router(setup_name, config_db_file_name)
        self.update_config_db_docker_routing_config_mode(setup_name, config_db_file_name)
        self.update_config_db_metadata_mgmt_port(setup_name, config_db_file_name)
        self.update_config_db_features(setup_name, hwsku, config_db_file_name)
        self.update_config_db_feature_config(setup_name, "database", "auto_restart", "always_enabled",
                                             config_db_file_name)
        default_mtu = "9100"
        self.update_config_db_port_mtu_config(setup_name, default_mtu, config_db_file_name)
        self.update_config_db_breakout_cfg(topology_obj, setup_name, hwsku, config_db_file_name)
        return config_db_file_name

    def update_config_db_features(self, setup_name, hwsku, config_db_json_file_name):
        init_config_db_json = self.get_init_config_db_json_obj(hwsku)
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        image_supported_features = init_config_db_json[ConfigDbJsonConst.FEATURE]
        current_features = config_db_json[ConfigDbJsonConst.FEATURE]
        for feature, feature_properties in image_supported_features.items():
            if feature not in current_features:
                config_db_json[ConfigDbJsonConst.FEATURE][feature] = feature_properties
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_metadata_router(self, setup_name, config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        config_db_json[ConfigDbJsonConst.DEVICE_METADATA][ConfigDbJsonConst.LOCALHOST][ConfigDbJsonConst.TYPE] =\
            ConfigDbJsonConst.TOR_ROUTER
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_docker_routing_config_mode(self, setup_name, config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        config_db_json[ConfigDbJsonConst.DEVICE_METADATA][ConfigDbJsonConst.LOCALHOST].update(
            {ConfigDbJsonConst.DOCKER_ROUTING_CONFIG_MODE: ConfigDbJsonConst.SPLIT})
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_metadata_mgmt_port(self, setup_name, config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)

        config_db_json[ConfigDbJsonConst.MGMT_PORT] = json.loads(ConfigDbJsonConst.MGMT_PORT_VALUE)
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_hostname(self, setup_name, hostname, config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        config_db_json[ConfigDbJsonConst.DEVICE_METADATA][ConfigDbJsonConst.LOCALHOST][ConfigDbJsonConst.HOSTNAME] = \
            hostname
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_feature_config(self, setup_name, feature_name, feature_config_key, feature_config_value,
                                        config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        config_db_json[ConfigDbJsonConst.FEATURE][feature_name][feature_config_key] = feature_config_value
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_port_mtu_config(self, setup_name, mtu, config_db_json_file_name):
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name=config_db_json_file_name)
        for k, _ in config_db_json[ConfigDbJsonConst.PORT].items():
            config_db_json[ConfigDbJsonConst.PORT][k]["mtu"] = mtu
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    def update_config_db_metadata_mgmt_ip(self, setup_name, ip, file_name=SonicConst.CONFIG_DB_JSON):
        def _get_subnet_mask(ip, interfaces_ips_output):
            for elem in interfaces_ips_output:
                if InfraConst.IP in elem:
                    if elem[InfraConst.IP] == ip:
                        return elem[InfraConst.MASK]

        def _get_default_gw():
            def _get_by_iproute():
                routes = self.cli_obj.route.show_ip_route()
                default_gw_obj = re.search(r'0\.0\.0\.0\/0 \[.*\] via (.*), eth0', routes)
                return default_gw_obj.group(1) if default_gw_obj else None

            def _get_by_arp():
                arp_table_dict = self.cli_obj.arp.show_arp_table()
                for arp_ip, arp_info in arp_table_dict.items():
                    if arp_info['Iface'] == 'eth0' and arp_info['MacAddress'] != '(incomplete)':
                        return arp_ip

            _default_gw = _get_by_iproute()
            if not _default_gw:
                _default_gw = _get_by_arp()
            return _default_gw

        config_db_json = self.get_config_db()
        mask = _get_subnet_mask(ip, self.cli_obj.ip.get_interface_ips('eth0'))
        default_gw = _get_default_gw()
        config_db_json[ConfigDbJsonConst.MGMT_INTERFACE] =\
            json.loads(ConfigDbJsonConst.MGMT_INTERFACE_VALUE % (ip, mask, default_gw))

        return self.create_extended_config_db_file(setup_name, config_db_json, file_name)

    @staticmethod
    def is_platform_supports_split_without_unmap(hwsku):
        platform_prefix_with_unmap = ["SN2410", "SN2700", "SN4600"]
        for platform_prefix in platform_prefix_with_unmap:
            if re.search(platform_prefix, hwsku):
                return False
        return True

    def update_config_db_breakout_cfg(self, topology_obj, setup_name, hwsku, config_db_json_file_name):
        init_config_db_json = self.get_init_config_db_json_obj(hwsku)
        config_db_json = self.get_config_db_json_obj(setup_name, config_db_json_file_name)
        if init_config_db_json.get("BREAKOUT_CFG") and not self.is_bluefield(hwsku):
            config_db_json = self.update_breakout_cfg(topology_obj, init_config_db_json, config_db_json, hwsku)
        return self.create_extended_config_db_file(setup_name, config_db_json, file_name=config_db_json_file_name)

    @staticmethod
    def is_bluefield(hwsku):
        bluefield_hwsku = 'mbf2h536c'
        return bluefield_hwsku in hwsku.lower()

    @staticmethod
    def get_config_db_json_obj(setup_name, config_db_json_file_name=SonicConst.CONFIG_DB_JSON):
        config_db_path = str(os.path.join(InfraConst.MARS_TOPO_FOLDER_PATH, setup_name, config_db_json_file_name))
        with open(config_db_path) as config_db_json_file:
            config_db_json = json.load(config_db_json_file)
        return config_db_json

    def get_init_config_db_json_obj(self, hwsku):
        init_config_db = \
            self.engine.run_cmd("sonic-cfggen -k {} -H -j /etc/sonic/init_cfg.json --print-data".format(hwsku),
                                print_output=False)
        init_config_db_json = json.loads(init_config_db)
        return init_config_db_json

    def get_hwsku_json_as_dict(self, platform, hwsku):
        hwsku_path = f'/usr/share/sonic/device/{platform}/{hwsku}/hwsku.json'
        data = self.engine.run_cmd(f'cat {hwsku_path}')
        return json.loads(data)

    def update_breakout_cfg(self, topology_obj, init_config_db_json, config_db_json, hwsku):
        """
        This function updates the config_sb.json file with BREAKOUT_CFG section.
        In cases of systems where the consecutive port is unmapped after split of 4,
        the static split ports of 4, will not be include in the BREAKOUT_CFG.

        :param topology_obj: a topology object fixture
        :param init_config_db_json: a json object of the initial config_db.json file on the dut
        :param config_db_json: a json object of the config_db.json file on the dut
        :param hwsku:  hwsku of the dut  i.e, Mellanox-SN2700
        :return: the name of the updated config_db.json file with BREAKOUT_CFG section
        """
        breakout_cfg_dict = init_config_db_json.get("BREAKOUT_CFG")
        platform_json_obj = json_file_helper.get_platform_json(self.engine, self.cli_obj)
        parsed_platform_json_by_breakout_modes = self.parse_platform_json(topology_obj, platform_json_obj,
                                                                          parse_by_breakout_modes=True)
        split_ports_for_update = get_all_split_ports_parents(config_db_json)
        unsplit_ports_for_update = get_all_unsplit_ports(config_db_json)
        self.update_breakout_mode_for_split_ports(split_ports_for_update, hwsku, breakout_cfg_dict,
                                                  config_db_json, parsed_platform_json_by_breakout_modes)
        self.update_breakout_mode_for_unsplit_ports(unsplit_ports_for_update, breakout_cfg_dict,
                                                    config_db_json, parsed_platform_json_by_breakout_modes)
        port_info_dict = config_db_json.get(ConfigDbJsonConst.PORT, [])
        breakout_cfg_dict = {port: breakout_mode for port, breakout_mode in breakout_cfg_dict.items()
                             if port in port_info_dict}
        config_db_json["BREAKOUT_CFG"] = breakout_cfg_dict
        return config_db_json

    def is_supported_split_mode(self, hwsku, split_num):
        split_supported_without_unmap = self.is_platform_supports_split_without_unmap(hwsku) or split_num is 2
        platform_not_sn3800 = not re.search("SN3800", hwsku)
        return split_supported_without_unmap and platform_not_sn3800

    def update_breakout_mode_for_split_ports(self, split_ports_for_update, hwsku, breakout_cfg_dict,
                                             config_db_json, parsed_platform_json_by_breakout_modes):
        for port, split_num in split_ports_for_update:
            if self.is_supported_split_mode(hwsku, split_num):
                self.update_port_breakout_cfg_mode(breakout_cfg_dict, port, config_db_json, split_num,
                                                   parsed_platform_json_by_breakout_modes)

    def update_breakout_mode_for_unsplit_ports(self, unsplit_ports_for_update, breakout_cfg_dict,
                                               config_db_json, parsed_platform_json_by_breakout_modes):
        unsplit_ports_split_num = 1
        for port in unsplit_ports_for_update:
            self.update_port_breakout_cfg_mode(breakout_cfg_dict, port, config_db_json,
                                               unsplit_ports_split_num,
                                               parsed_platform_json_by_breakout_modes)

    @staticmethod
    def update_port_breakout_cfg_mode(breakout_cfg_dict, port, config_db_json,
                                      split_num, parsed_platform_json_by_breakout_modes):
        breakout_cfg_dict[port]["brkout_mode"] = get_port_current_breakout_mode(config_db_json, port, split_num,
                                                                                parsed_platform_json_by_breakout_modes)

    @staticmethod
    def create_extended_config_db_file(setup_name, config_db_json, file_name=SonicConst.EXTENDED_CONFIG_DB_PATH):
        new_config_db_json_path = str(os.path.join(InfraConst.MARS_TOPO_FOLDER_PATH,
                                                   setup_name,
                                                   file_name))
        if os.path.exists(new_config_db_json_path):
            os.remove(new_config_db_json_path)
        with open(new_config_db_json_path, 'w') as f:
            json.dump(config_db_json, f, indent=4)
            f.write('\n')
        os.chmod(new_config_db_json_path, 0o777)
        return file_name

    def update_dhclient_lease_time(self):
        dhclient_lease_time = 'send dhcp-lease-time 7200;'
        dhclient_conf_file = '/usr/share/sonic/templates/dhclient.conf.j2'
        update_dhclient_lease_time_cmd = f"""
        if grep -q dhcp-lease-time {dhclient_conf_file}; then
            sudo sed -i 's/^send dhcp-lease-time.*/{dhclient_lease_time}/g' {dhclient_conf_file}
        else
            sudo sed -i '/^send host-name = gethostname();/a {dhclient_lease_time}' {dhclient_conf_file}
        fi
        """
        self.engine.run_cmd(update_dhclient_lease_time_cmd, validate=True)

    def install_wjh(self, wjh_deb_url):
        wjh_package_local_name = '/home/admin/wjh.deb'
        self.engine.run_cmd('sudo curl {} -o {}'.format(wjh_deb_url, wjh_package_local_name))
        self.engine.run_cmd('sudo dpkg -i {}'.format(wjh_package_local_name), validate=True)
        logger.info('Sleep {} after what-just-happened installation'.format(InfraConst.SLEEP_AFTER_WJH_INSTALLATION))
        time.sleep(InfraConst.SLEEP_AFTER_WJH_INSTALLATION)
        self.set_feature_state('what-just-happened', 'enabled')
        self.save_configuration()
        self.engine.run_cmd('sudo rm -f {}'.format(wjh_package_local_name))
        retry_call(self._verify_dockers_are_up,
                   fargs=[[AppExtensionInstallationConstants.WJH_APP_NAME]],
                   tries=24,
                   delay=10,
                   logger=logger)

    def execute_command_in_docker(self, docker, command):
        return self.engine.run_cmd('docker exec -i {} {}'.format(docker, command))

    def copy_to_docker(self, docker, src_path_on_host, dst_path_in_docker):
        return self.engine.run_cmd('docker cp {} {}:{}'.format(src_path_on_host, docker, dst_path_in_docker))

    def copy_from_docker(self, docker, dst_path_on_host, src_path_in_docker):
        return self.engine.run_cmd('sudo docker cp {}:{} {}'.format(docker, src_path_in_docker, dst_path_on_host))

    def get_warm_reboot_status(self):
        return self.engine.run_cmd('systemctl is-active warmboot-finalizer')

    def check_warm_reboot_status(self, expected_status):
        warm_reboot_status = self.get_warm_reboot_status()
        if expected_status not in warm_reboot_status:
            raise Exception('warm-reboot status "{}" not as expected "{}"'.format(warm_reboot_status, expected_status))

    def get_config_db(self):
        config_db_json = self.engine.run_cmd('cat {} ; echo'.format(SonicConst.CONFIG_DB_JSON_PATH), print_output=False)
        return json.loads(config_db_json)

    def get_config_db_from_running_config(self):
        config = self.engine.run_cmd('sudo show runningconfiguration all', print_output=False)
        return json.loads(config)

    def is_dpu(self):
        """
        Function to check if the current DUT is DPU
        """
        platform = self.cli_obj.chassis.get_platform()
        return 'arm64-nvda_bf-mbf2h536c' in platform

    def is_spc1(self, cli_object):
        """
        Function to check if the current DUT is SPC1
        :param cli_object: cli_object
        """
        platform = cli_object.chassis.get_platform()
        # if sn2 in platform, it's spc1. e.g. x86_64-mlnx_msn2700-r0
        return 'sn2' in platform

    def show_version(self, validate=False):
        return self.engine.run_cmd('show version', validate=validate)

    def parse_platform_json(self, topology_obj, platform_json_obj, parse_by_breakout_modes=False):
        """
        parsing platform breakout options and config_db.json breakout configuration.
        :param topology_obj: topology object fixture
        :param platform_json_obj: a json object of platform.json file
        :param parse_by_breakout_modes: If true the function will return a dictionary with
        available breakout options by split number for all dut ports
        :return: a dictionary with available speeds option/ breakout options for each split number on all dut ports
        i.e, parse_by_breakout_modes = FALSE

           { 'Ethernet0' :{'1': [200G,100G,50G,40G,25G,10G,1G],
                           '2': [100G, 50G,40G,25G,10G,1G],
                           '4': [50G,40G,25G,10G,1G]},..}

        OR Iin case of: parse_by_breakout_modes = TRUE

           { 'Ethernet0' :    {1:{'1x100G[50G,40G,25G,10G]'},
                               2: {'2x50G[40G,25G,10G]'},
                               4: {'4x25G[10G]'},...}

        """
        ports_speeds_by_modes_info = {}
        breakout_options = SonicConst.BREAKOUT_MODES_REGEX
        if not platform_json_obj.get("interfaces"):
            ports_speeds_by_modes_info = self.generate_mock_ports_speeds(topology_obj, parse_by_breakout_modes)
        else:
            for port_name, port_dict in platform_json_obj["interfaces"].items():
                port_start_index = int(re.search(r'Ethernet(.*)', port_name).group(1))
                lanes = port_dict[SonicConstant.LANES].split(",")
                breakout_modes = re.findall(breakout_options, ",".join(list(port_dict[SonicConstant.BREAKOUT_MODES].keys())))
                lane_count = len(lanes)
                breakout_ports = ["Ethernet{}".format(port_start_index + i) for i in range(lane_count)]
                for port in breakout_ports:
                    if port in topology_obj.players_all_ports[self.dut_alias]:
                        if parse_by_breakout_modes:
                            ports_speeds_by_modes_info[port] = get_split_mode_supported_breakout_modes(breakout_modes)
                        else:
                            ports_speeds_by_modes_info[port] = get_split_mode_supported_speeds(breakout_modes)
        return ports_speeds_by_modes_info

    @staticmethod
    def generate_mock_ports_speeds(topology_obj, parse_by_breakout_modes=False):
        if parse_by_breakout_modes:
            raise AssertionError("This version doesn't support platform.json,\n"
                                 "there no mock option for interfaces breakout mode option")
        else:
            mock_ports_speeds_by_modes_info = {}
            port_list = get_dut_default_ports_list(topology_obj)
            for port in port_list:
                mock_ports_speeds_by_modes_info[port] = {
                    1: ['100G', '50G', '25G', '10G'],
                    2: ['50G', '25G', '10G'],
                    4: ['25G', '10G']
                }
            logger.debug("Mock ports speed option dictionary: {}".format(mock_ports_speeds_by_modes_info))
            return mock_ports_speeds_by_modes_info

    def show_warm_restart_state(self):
        """
        Show warm_sestart_state
        Example:
            name             restore_count  state
            -------------  ---------------  ----------------------
            warm-shutdown                0  pre-shutdown-succeeded
            vlanmgrd                     4  reconciled
            cpu-report                   1  reconciled
            vrfmgrd                      4  reconciled
            syncd                        4
            neighsyncd                   4  reconciled
        return: warm_restart stat dict like below, or raise exception
            { "warm-shutdown": {"name":"warm-shutdown", "restore_count":"0", "state": "pre-shutdown-succeeded"},
              "vlanmgrd": {"name":"vlanmgrd", "restore_count":"4", "state": "reconciled"},
              "cpu-report": {"name":"cpu-report", "restore_count":"1", "state": "reconciled"},
              "vrfmgrd": {"name":"vrfmgrd", "restore_count":"4", "state": "reconciled"},
              "syncd": {"name":"syncd", "restore_count":"4", "state": ""},
              "neighsyncd", {"name":"neighsyncd", "restore_count":"4", "state": "reconciled"}
            }
        """
        warm_restart_state = self.engine.run_cmd("show warm_restart state")
        warm_restart_state_dict = generic_sonic_output_parser(warm_restart_state,
                                                              headers_ofset=0,
                                                              len_ofset=1,
                                                              data_ofset_from_start=2,
                                                              data_ofset_from_end=None,
                                                              column_ofset=2,
                                                              output_key='name')
        return warm_restart_state_dict

    def get_base_and_target_images(self):
        """
        This method getting base and target image from "sonic-installer list" output
        """
        installed_list_output = self.get_sonic_image_list()
        target_image = re.search(r'Current:\s(.*)', installed_list_output, re.IGNORECASE).group(1)
        try:
            available_images = re.search(r'Available:\s\n(.*)\n(.*)', installed_list_output, re.IGNORECASE)
            available_image_1 = available_images.group(1)
            available_image_2 = available_images.group(2)
            if target_image == available_image_1:
                base_image = available_image_2
            else:
                base_image = available_image_1
        except Exception as err:
            logger.warning('Only 1 installed image available')
            base_image = None

        return base_image, target_image

    def verify_installed_extensions_running(self):
        """
        Verify installed mellanox app_extension to image exist in docker ps output
        :return: None if successful, otherwise Exception
        """
        if self.cli_obj.app_ext.verify_version_support_app_ext():
            installed_mellanox_ext = get_installed_mellanox_extensions(self.cli_obj)
            if installed_mellanox_ext:
                retry_call(self._verify_dockers_are_up,
                           fargs=[installed_mellanox_ext],
                           tries=36,
                           delay=10,
                           logger=logger)

    def is_dummy_command_succeed(self):
        try:
            self.engine.run_cmd(DUMMY_COMMAND, validate=True)
            logger.info('login with credentials username: {} ,password:{} succeed!'.
                        format(self.engine.username, self.engine.password))
            return True
        except netmiko.ssh_exception.NetmikoAuthenticationException:
            logger.info('login with credentials username: {} ,password:{} did not succeed!'.
                        format(self.engine.username, self.engine.password))
            return False

    def if_other_credentials_used_set_boot_order_onie(self):
        engine = self.get_sonic_engine_try_different_passwords()
        if engine:
            with allure.step("Other credentials used then default"):
                logger.info('Other credentials used then default')
                with allure.step('Setting boot order to onie'):
                    self.set_next_boot_entry_to_onie()
                    self.engine = engine
                with allure.step('Rebooting the switch'):
                    engine.reload(['sudo reboot'], wait_after_ping=25, ssh_after_reload=False)

    def get_sonic_engine_try_different_passwords(self):
        for password in DefaultCredentialConstants.OTHER_SONIC_PASSWORD_LIST:
            engine = LinuxSshEngine(
                self.engine.ip, username=DefaultCredentialConstants.OTHER_SONIC_USER, password=password)
            if self.is_dummy_command_succeed():
                return engine

    def enable_info_logging_on_docker(self, docker_name):
        self.engine.run_cmd(f"{docker_name}loglevel -l INFO -a")


class SonicGeneralCli202012(SonicGeneralCliDefault):

    def __init__(self, engine, cli_obj, dut_alias):
        self.engine = engine
        self.cli_obj = cli_obj
        self.dut_alias = dut_alias

    def reload_flow(self, ports_list=None, topology_obj=None, reload_force=False):
        """
        Reloading switch and validate dockers and ports state
        :param ports_list: list of the ports to check status after reboot
        :param topology_obj: topology object
        :param reload_force: provide if want to do reload with -f flag(force)
        :return: None, raise error in case of unexpected result
        """
        if not (ports_list or topology_obj):
            raise Exception('ports_list or topology_obj must be passed to reload_flow method')
        if not ports_list:
            ports_list = topology_obj.players_all_ports[self.dut_alias]
        with allure.step('Reloading dut'):
            logger.info("Reloading dut")
            self.reload_configuration(reload_force)
            self.port_reload_reboot_checks(ports_list)

    def reload_configuration(self, force=False):
        if force:
            logger.warning('Force reload config not supported on branch 202012, using default cmd "config reload -y"')

        cmd = 'sudo config reload -y'
        self.engine.run_cmd(cmd, validate=True)
