import allure
import logging
import random
import time
import pexpect
import netmiko
import traceback
from retry import retry
from retry.api import retry_call
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.helpers.run_process_on_host import run_process_on_host
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from infra.tools.connection_tools.onie_engine import OnieEngine
from infra.tools.exceptions.real_issue import RealIssue
from ngts.constants.constants import SonicConst, InfraConst


logger = logging.getLogger()


class OnieInstallationError(Exception):
    """
    An exception for errors that reflect problematic behavior of the OS installation
    """


class SonicGeneralCli(GeneralCliCommon):
    """
    This class is for general cli commands for sonic only
    """

    @staticmethod
    def show_feature_status(engine):
        """
        This method show feature status on the sonic switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show feature status')

    @staticmethod
    def set_feature_state(engine, feature_name, state):
        """
        This method to set feature state on the sonic switch
        :param engine: ssh engine object
        :param feature_name: the feature name
        :param state: state
        """
        engine.run_cmd('sudo config feature state {} {}'.format(feature_name, state), validate=True)

    @staticmethod
    def get_installer_delimiter(engine):
        dash_installer = 'sonic-installer'
        delimiter = '_'
        output = engine.run_cmd('which {}'.format(dash_installer))
        if dash_installer in output:
            delimiter = '-'
        return delimiter

    @staticmethod
    def install_image(engine, image_path, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer install {} -y'.format(delimiter, image_path), validate=True)
        return output

    @staticmethod
    def get_image_binary_version(engine, image_path, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer binary{}version {}'.format(delimiter, delimiter, image_path),
                                validate=True)
        return output

    @staticmethod
    def set_default_image(engine, image_binary, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer set{}default {}'.format(delimiter, delimiter, image_binary),
                                validate=True)
        return output

    @staticmethod
    def set_next_boot_entry_to_onie(engine):
        engine.run_cmd('sudo grub-editenv /host/grub/grubenv set next_entry=ONIE', validate=True)

    @staticmethod
    def get_sonic_image_list(engine, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer list'.format(delimiter), validate=True)
        return output

    @staticmethod
    def load_configuration(engine, config_file):
        engine.run_cmd('sudo config load -y {}'.format(config_file), validate=True)

    @staticmethod
    def reload_configuration(engine):
        engine.run_cmd('sudo config reload -y', validate=True)

    @staticmethod
    def save_configuration(engine):
        engine.run_cmd('sudo config save -y', validate=True)

    @staticmethod
    def download_file_from_http_url(engine, url, target_file_path):
        engine.run_cmd('sudo curl {} -o {}'.format(url, target_file_path), validate=True)

    @staticmethod
    def reboot_flow(engine, reboot_type='', ports_list=None, topology_obj=None, wait_after_ping=45):
        """
        Rebooting switch by given way(reboot, fast-reboot, warm-reboot) and validate dockers and ports state
        :param engine: ssh engine object
        :param reboot_type: reboot type
        :param ports_list: list of the ports to check status after reboot
        :param topology_obj: topology object
        :param wait_after_ping: how long in second wait after ping before ssh connection
        :return: None, raise error in case of unexpected result
        """
        if not (ports_list or topology_obj):
            raise Exception('ports_list or topology_obj must be passed to reboot_flow method')
        if not reboot_type:
            reboot_type = random.choice(['reboot', 'fast-reboot', 'warm-reboot'])
        if not ports_list:
            ports_list = topology_obj.players_all_ports['dut']
        with allure.step('Reboot switch by CLI - sudo {}'.format(reboot_type)):
            engine.reload(['sudo {}'.format(reboot_type)], wait_after_ping=wait_after_ping)
            SonicGeneralCli.verify_dockers_are_up(engine, SonicConst.DOCKERS_LIST)
            SonicGeneralCli.check_link_state(engine, ports_list)

    @staticmethod
    def validate_dockers_are_up_reboot_if_fail(engine, retries=2):
        """
        Reboot and validate docker containers are up on the switch
        :param engine: dut engine
        :param retries: int how many times do reboot of switch
        """
        initial_count = retries
        while retries:
            try:
                SonicGeneralCli.verify_dockers_are_up(engine)
                break
            except:
                logger.error('Catched exception {} during verifing docker conatiners are up.'
                             ' Rebooting dut and try again, try number {}'.format(traceback.print_exc(),
                                                                                  initial_count - retries + 1))
                engine.reload(['sudo reboot'])
            retries = retries - 1

    @staticmethod
    @retry(Exception, tries=15, delay=10)
    def verify_dockers_are_up(engine, dockers_list=None):
        """
        Verifying the dockers are in up state
        :param engine: ssh engine object
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        if dockers_list is None:
            dockers_list = SonicConst.DOCKERS_LIST
        for docker in dockers_list:
            engine.run_cmd('docker ps | grep {}'.format(docker), validate=True)

    @staticmethod
    def check_link_state(engine, ifaces=None):
        """
        Verify that links in UP state. Default interface is  Ethernet0, this link exist in each Canonical setup
        :param engine: ssh engine object
        :param ifaces: list of interfaces to check
        :return: None, raise error in case of unexpected result
        """
        if ifaces is None:
            ifaces = ['Ethernet0']
        with allure.step('Check that link in UP state'):
            retry_call(SonicInterfaceCli.check_ports_status,
                       fargs=[engine, ifaces],
                       tries=8,
                       delay=10,
                       logger=logger)

    @staticmethod
    def generate_techsupport(engine, duration=60):
        """
        Generate sysdump for a given time frame in seconds
        :param engine: ssh engine object
        :param duration: time frame in seconds
        :return: dump path
        """
        with allure.step('Generate Techsupport of last {} seconds'.format(duration)):
            output = engine.run_cmd('sudo generate_dump -s \"-{} seconds\"'.format(duration))
            return output.splitlines()[-1]

    @staticmethod
    def do_installation(topology_obj, dut_engine, image_path, deploy_type):
        with allure.step('Preparing switch for installation'):
            in_onie = SonicGeneralCli.prepare_for_installation(topology_obj)

        if deploy_type == 'sonic':
            if in_onie:
                raise AssertionError("The request deploy type is 'sonic'(upgrade sonic to sonic)"
                                     " while the switch is running ONIE instead of SONiC OS.")
            SonicGeneralCli.deploy_sonic(dut_engine, image_path)

        if deploy_type == 'onie':
            SonicGeneralCli.deploy_onie(dut_engine, image_path, in_onie)

    @staticmethod
    def deploy_image(topology_obj, image_path, apply_base_config=False, setup_name=None,
                     platform=None, hwsku=None,
                     wjh_deb_url=None, deploy_type='sonic', reboot_after_install=None):
        dut_engine = topology_obj.players['dut']['engine']
        if not image_path.startswith('http'):
            image_path = '{}{}'.format(InfraConst.HTTP_SERVER, image_path)
        try:
            with allure.step("Trying to install sonic image"):
                SonicGeneralCli.do_installation(topology_obj, dut_engine, image_path, deploy_type)
        except OnieInstallationError:
            with allure.step("Catched exception OnieInstallationError during install. Perform reboot and trying again"):
                logger.error('Catched exception OnieInstallationError during install. Perform reboot and trying again')
                SonicGeneralCli.remote_reboot(topology_obj)
                logger.info('Sleeping %s seconds to handle ssh flapping' % InfraConst.SLEEP_AFTER_RRBOOT)
                time.sleep(InfraConst.SLEEP_AFTER_RRBOOT)
                SonicGeneralCli.do_installation(topology_obj, dut_engine, image_path, deploy_type)

        if apply_base_config:
            SonicGeneralCli.apply_basic_config(dut_engine, setup_name, platform, hwsku)

        if reboot_after_install:
            SonicGeneralCli.validate_dockers_are_up_reboot_if_fail(dut_engine)

        if wjh_deb_url:
            SonicGeneralCli.install_wjh(dut_engine, wjh_deb_url)

        SonicGeneralCli.verify_dockers_are_up(dut_engine)

    @staticmethod
    def deploy_sonic(dut_engine, image_path):
        tmp_target_path = '/tmp/sonic-mellanox.bin'
        delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)

        with allure.step('Deploying image via SONiC'):
            with allure.step('Copying image to dut'):
                SonicGeneralCli.download_file_from_http_url(dut_engine, image_path, tmp_target_path)

            with allure.step('Installing the image'):
                SonicGeneralCli.install_image(dut_engine, tmp_target_path, delimiter)

            with allure.step('Setting image as default'):
                image_binary = SonicGeneralCli.get_image_binary_version(dut_engine, tmp_target_path, delimiter)
                SonicGeneralCli.set_default_image(dut_engine, image_binary, delimiter)

        with allure.step('Rebooting the dut'):
            dut_engine.reload(['sudo reboot'])

        with allure.step('Verifying installation'):
            with allure.step('Verifying dut booted with correct image'):
                # installer flavor might change after loading a different version
                delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)
                image_list = SonicGeneralCli.get_sonic_image_list(dut_engine, delimiter)
                assert 'Current: {}'.format(image_binary) in image_list

    @staticmethod
    def deploy_onie(dut_engine, image_path, in_onie=False):
        if not in_onie:
            with allure.step('Setting boot order to sonic'):
                SonicGeneralCli.set_next_boot_entry_to_onie(dut_engine)
            with allure.step('Rebooting the switch'):
                dut_engine.reload(['sudo reboot'], wait_after_ping=15, ssh_after_reload=False)
        SonicGeneralCli.install_image_onie(dut_engine.ip, image_path)

    @staticmethod
    def install_image_onie(dut_ip, image_url):
        sonic_cli_ssh_connect_timeout = 10

        def install_image(host, url, timeout=60, num_retry=10):
            client = OnieEngine(host, 'root').create_engine()
            client.expect(['#'])

            client.timeout = timeout
            prompts = ["ONIE:.+ #", pexpect.EOF]
            stdout = ""
            logger.info('Stopping onie discovery')
            client.sendline('onie-discovery-stop')
            client.expect(prompts)
            stdout += client.before.decode('ascii')
            logger.info(stdout)
            attempt = 0
            logger.info('Installing image')
            client.sendline("onie-nos-install %s" % url)
            i = client.expect(["Installed SONiC base image SONiC-OS successfully"] + prompts + [pexpect.TIMEOUT])
            stdout += client.before.decode('ascii')
            logger.info(stdout)
            while num_retry > 0:
                if i == 0:
                    break
                elif i == 3:
                    num_retry = num_retry - 1
                    i = client.expect(
                        ["Installed SONiC base image SONiC-OS successfully"] + prompts + [pexpect.TIMEOUT])
                    logger.info("Got timeout on %d time.." % num_retry)
                    logger.info("Printing output: %s" % client.before)
                else:
                    logger.info('Catched pexpect entry: %d' % i)
                    raise OnieInstallationError("Failed to install sonic image. %s" % stdout)
            else:
                logger.info("Did not installed image in %d seconds." % num_retry * timeout)
                raise OnieInstallationError("Failed to install sonic image. %s" % stdout)
            logger.info('SONiC installed')
            client.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=15)
            stdout += client.before.decode('ascii')
            logger.info(stdout)
            return stdout

        with allure.step('Installing image by "onie-nos-install"'):
            install_image(host=dut_ip, url=image_url)
        with allure.step('Waiting for switch shutdown after reload command'):
            logger.info('Waiting for switch shutdown after reload command')
            ping_till_alive(False, dut_ip)

        with allure.step('Waiting for switch bring-up after reload'):
            logger.info('Waiting for switch bring-up after reload')
            ping_till_alive(True, dut_ip)

        with allure.step('Waiting for CLI bring-up after reload'):
            logger.info('Waiting for CLI bring-up after reload')
            time.sleep(sonic_cli_ssh_connect_timeout)


    @staticmethod
    def check_is_alive_and_revive(topology_obj):
        ip = topology_obj.players['dut']['engine'].ip
        try:
            logger.info('Checking whether device is alive')
            ping_till_alive(should_be_alive=True, destination_host=ip, tries=2)
            logger.info('Device is alive')
        except RealIssue:
            logger.info('Device is not alive, reviving')
            SonicGeneralCli.remote_reboot(topology_obj)
            logger.info('Device is revived')
        return True

    @staticmethod
    def remote_reboot(topology_obj):
        ip = topology_obj.players['dut']['engine'].ip
        logger.info('Executing remote reboot')
        cmd = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['remote_reboot']
        _, _, rc = run_process_on_host(cmd)
        if rc == InfraConst.RC_SUCCESS:
            ping_till_alive(should_be_alive=True, destination_host=ip)
        else:
            raise Exception('Remote reboot rc is other then 0')

    @staticmethod
    def check_in_onie(ip, cmd):
        client = OnieEngine(ip, 'root').create_engine()
        client.expect(['#'])

        client.timeout = 10
        prompts = ["ONIE:.+ #", pexpect.EOF]
        stdout = ""
        logger.info('Executing command {}'.format(cmd))
        client.sendline(cmd)
        client.expect(prompts)
        stdout += client.before.decode('ascii')
        logger.info(stdout)
        return stdout

    @staticmethod
    def check_onie_mode_and_set_install(ip):
        if 'boot_reason=install' not in SonicGeneralCli.check_in_onie(ip, 'cat /proc/cmdline'):
            logger.info('Switch is not in ONIE install mode, fixing')
            SonicGeneralCli.check_in_onie(ip, 'onie-boot-mode -o install')
            SonicGeneralCli.check_in_onie(ip, 'reboot')
            logger.info('Sleep %s seconds before doing ping till alive' % InfraConst.SLEEP_BEFORE_RRBOOT)
            time.sleep(InfraConst.SLEEP_BEFORE_RRBOOT)
            ping_till_alive(should_be_alive=True, destination_host=ip)
            logger.info('Sleeping %s seconds after switch reply to ping to handle ssh session' % InfraConst.SLEEP_AFTER_RRBOOT)
            time.sleep(InfraConst.SLEEP_AFTER_RRBOOT)
        else:
            logger.info('Switch is in ONIE install mode')


    @staticmethod
    def prepare_for_installation(topology_obj):
        switch_in_onie = False
        dut_engine = topology_obj.players['dut']['engine']
        SonicGeneralCli.check_is_alive_and_revive(topology_obj)
        dummy_command = 'echo dummy_command'
        try:
            # Checking if device is in sonic
            dut_engine.run_cmd(dummy_command, validate=True)
        except netmiko.ssh_exception.NetmikoAuthenticationException:
            logger.info('Login to onie succeed!')
            SonicGeneralCli.check_onie_mode_and_set_install(dut_engine.ip)
            switch_in_onie = True
        return switch_in_onie

    @staticmethod
    def apply_basic_config(dut_engine, setup_name, platform, hwsku):
        shared_path = '{}{}{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_name)

        switch_config_ini_path = "/usr/share/sonic/device/{}/{}/{}".format(platform, hwsku, SonicConst.PORT_CONFIG_INI)
        dut_engine.run_cmd(
            'sudo curl {}/{} -o {}'.format(shared_path, SonicConst.PORT_CONFIG_INI, switch_config_ini_path))
        dut_engine.run_cmd(
            'sudo curl {}/{} -o {}'.format(shared_path, SonicConst.CONFIG_DB_JSON, SonicConst.CONFIG_DB_JSON_PATH))

        dut_engine.reload(['sudo reboot'])

    @staticmethod
    def install_wjh(dut_engine, wjh_deb_url):
        wjh_package_local_name = '/home/admin/wjh.deb'
        dut_engine.run_cmd('sudo curl {} -o {}'.format(wjh_deb_url, wjh_package_local_name))
        dut_engine.run_cmd('sudo dpkg -i {}'.format(wjh_package_local_name), validate=True)
        SonicGeneralCli.set_feature_state(dut_engine, 'what-just-happened', 'enabled')
        SonicGeneralCli.save_configuration(dut_engine)
        dut_engine.run_cmd('sudo rm -f {}'.format(wjh_package_local_name))

    @staticmethod
    def execute_command_in_docker(dut_engine, docker, command):
        return dut_engine.run_cmd('docker exec -i {} {}'.format(docker, command))

    @staticmethod
    def get_warm_reboot_status(dut_engine):
        return dut_engine.run_cmd('systemctl is-active warmboot-finalizer')

    @staticmethod
    def check_warm_reboot_status(dut_engine, expected_status):
        warm_reboot_status = SonicGeneralCli.get_warm_reboot_status(dut_engine)
        if expected_status not in warm_reboot_status:
            raise Exception('warm-reboot status "{}" not as expected "{}"'.format(warm_reboot_status, expected_status))
