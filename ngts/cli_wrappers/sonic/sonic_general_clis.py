import re
import allure
import logging
import random
import time
import pexpect
import netmiko
import json
import traceback
import os
from retry import retry
from retry.api import retry_call

from ngts.cli_util.cli_constants import SonicConstant
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.helpers.run_process_on_host import run_process_on_host
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from infra.tools.connection_tools.onie_engine import OnieEngine
from infra.tools.exceptions.real_issue import RealIssue
from ngts.constants.constants import SonicConst, InfraConst, ConfigDbJsonConst
from ngts.helpers.breakout_helpers import get_port_current_breakout_mode, get_all_split_ports_parents, \
    get_split_mode_supported_breakout_modes, get_split_mode_supported_speeds
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
import ngts.helpers.json_file_helper as json_file_helper
from ngts.helpers.interface_helpers import get_dut_default_ports_list

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
    def install_image(engine, image_path, delimiter='-', is_skipping_migrating_package=False):
        if not is_skipping_migrating_package:
            output = engine.run_cmd('sudo sonic{}installer install {} -y'.format(delimiter, image_path), validate=True)
        else:
            output = engine.run_cmd('sudo sonic{}installer install {} -y --skip-package-migration'.format(delimiter, image_path), validate=True)
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
    def check_link_state(engine, ifaces=None, expected_status='up'):
        """
        Verify that links in UP state. Default interface is  Ethernet0, this link exist in each Canonical setup
        :param engine: ssh engine object
        :param ifaces: list of interfaces to check
        :param expected_status: 'up' if expected UP, or 'down' if expected DOWN
        :return: None, raise error in case of unexpected result
        """
        if ifaces is None:
            ifaces = ['Ethernet0']
        with allure.step('Check that link in UP state'):
            retry_call(SonicInterfaceCli.check_ports_status,
                       fargs=[engine, ifaces, expected_status],
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
        cli_object = topology_obj.players['dut']['cli']
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

        if reboot_after_install:
            SonicGeneralCli.validate_dockers_are_up_reboot_if_fail(dut_engine)

        if apply_base_config:
            SonicGeneralCli.apply_basic_config(topology_obj, dut_engine, cli_object, setup_name, platform, hwsku)

        if wjh_deb_url:
            SonicGeneralCli.install_wjh(dut_engine, wjh_deb_url)

        SonicGeneralCli.verify_dockers_are_up(dut_engine)

    @staticmethod
    def deploy_sonic(dut_engine, image_path, is_skipping_migrating_package=False):
        tmp_target_path = '/tmp/sonic-mellanox.bin'
        delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)

        with allure.step('Deploying image via SONiC'):
            with allure.step('Copying image to dut'):
                SonicGeneralCli.download_file_from_http_url(dut_engine, image_path, tmp_target_path)

            with allure.step('Installing the image'):
                SonicGeneralCli.install_image(dut_engine, tmp_target_path, delimiter, is_skipping_migrating_package)

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
                dut_engine.reload(['sudo reboot'], wait_after_ping=25, ssh_after_reload=False)
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
    def apply_basic_config(topology_obj, dut_engine, cli_object, setup_name, platform, hwsku):
        shared_path = '{}{}{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_name)

        switch_config_ini_path = "/usr/share/sonic/device/{}/{}/{}".format(platform, hwsku, SonicConst.PORT_CONFIG_INI)
        dut_engine.run_cmd(
            'sudo curl {}/{} -o {}'.format(shared_path, SonicConst.PORT_CONFIG_INI, switch_config_ini_path))

        SonicGeneralCli.upload_config_db_file(topology_obj, setup_name, dut_engine, cli_object, hwsku, shared_path)

        dut_engine.reload(['sudo reboot'])

    @staticmethod
    def upload_config_db_file(topology_obj, setup_name, dut_engine, cli_object, hwsku, shared_path):
        config_db_file = SonicConst.CONFIG_DB_JSON
        if SonicGeneralCli.is_platform_supports_split_without_unmap(hwsku):
            config_db_file = SonicGeneralCli.update_config_db_file(topology_obj, setup_name, dut_engine,
                                                                   cli_object, hwsku)
        config_db_file = SonicGeneralCli.update_config_db_metadata_router(setup_name, config_db_file)
        dut_engine.run_cmd(
            'sudo curl {}/{} -o {}'.format(shared_path, config_db_file, SonicConst.CONFIG_DB_JSON_PATH))

    @staticmethod
    def update_config_db_metadata_router(setup_name, config_db_json_file_name):
        config_db_json = SonicGeneralCli.get_config_db_json_obj(setup_name,
                                                                config_db_json_file_name=config_db_json_file_name)
        config_db_json[ConfigDbJsonConst.DEVICE_METADATA][ConfigDbJsonConst.LOCALHOST][ConfigDbJsonConst.TYPE] =\
            ConfigDbJsonConst.TOR_ROUTER
        return SonicGeneralCli.create_extended_config_db_file(setup_name, config_db_json)

    @staticmethod
    def update_config_db_metadata_mgmt_ip(engine, setup_name, ip):
        def _get_subnet_mask(ip, interfaces_ips_output):
            for elem in interfaces_ips_output:
                if InfraConst.IP in elem:
                    if elem[InfraConst.IP] == ip:
                        return elem[InfraConst.MASK]

        config_db_json = SonicGeneralCli.get_config_db_json_obj(setup_name)
        mask = _get_subnet_mask(ip, SonicIpCli.get_interface_ips(engine, 'eth0'))
        routes = SonicRouteCli.show_ip_route(engine, route_type='kernel')
        default_gw = re.search('0\.0\.0\.0/0 \[0/0\] via (.*), eth0', routes)
        config_db_json[ConfigDbJsonConst.MGMT_INTERFACE] =\
            json.loads(ConfigDbJsonConst.MGMT_INTERFACE_VALUE % (ip, mask, default_gw.group(1)))

        return SonicGeneralCli.create_extended_config_db_file(setup_name, config_db_json, file_name=SonicConst.CONFIG_DB_JSON)

    @staticmethod
    def is_platform_supports_split_without_unmap(hwsku):
        platform_prefix_with_unmap = ["SN2410", "SN2700", "SN3800", "SN4600"]
        for platform_prefix in platform_prefix_with_unmap:
            if re.search(platform_prefix, hwsku):
                return False
        return True

    @staticmethod
    def update_config_db_file(topology_obj, setup_name, dut_engine, cli_object, hwsku):
        config_db_file = SonicConst.CONFIG_DB_JSON
        init_config_db_json = SonicGeneralCli.get_init_config_db_json_obj(dut_engine, hwsku)
        if init_config_db_json.get("BREAKOUT_CFG"):
            config_db_json = SonicGeneralCli.get_config_db_json_obj(setup_name)
            config_db_file = SonicGeneralCli.update_breakout_cfg(topology_obj, setup_name, dut_engine,
                                                                 cli_object, init_config_db_json, config_db_json)
        return config_db_file

    @staticmethod
    def get_config_db_json_obj(setup_name, config_db_json_file_name=SonicConst.CONFIG_DB_JSON ):
        config_db_path = str(os.path.join(InfraConst.MARS_TOPO_FOLDER_PATH, setup_name, config_db_json_file_name))
        with open(config_db_path) as config_db_json_file:
            config_db_json = json.load(config_db_json_file)
        return config_db_json

    @staticmethod
    def get_init_config_db_json_obj(dut_engine, hwsku):
        init_config_db = \
                dut_engine.run_cmd("sonic-cfggen -k {} -H -j /etc/sonic/init_cfg.json --print-data".format(hwsku),
                                   print_output=False)
        init_config_db_json = json.loads(init_config_db)
        return init_config_db_json

    @staticmethod
    def update_breakout_cfg(topology_obj, setup_name, dut_engine, cli_object,
                            init_config_db_json, config_db_json):
        """
        This function updates the config_sb.json file with BREAKOUT_CFG section
        :param topology_obj: a topology object fixture
        :param setup_name: i.e, sonic_anaconda_r-anaconda-51
        :param dut_engine: an ssh engine of the dut
        :param cli_object: a cli obj of the dut
        :param init_config_db_json: a json object of the initial config_db.json file on the dut
        :param config_db_json: a json object of the config_db.json file on the dut
        :return: the name of the updated config_db.json file with BREAKOUT_CFG section
        """
        breakout_cfg_dict = init_config_db_json.get("BREAKOUT_CFG")
        platform_json_obj = json_file_helper.get_platform_json(dut_engine, cli_object)
        parsed_platform_json_by_breakout_modes = SonicGeneralCli.parse_platform_json(topology_obj, platform_json_obj,
                                                                     parse_by_breakout_modes=True)
        ports_for_update = get_all_split_ports_parents(config_db_json)
        for port, split_num in ports_for_update:
            breakout_cfg_dict[port]["brkout_mode"] = get_port_current_breakout_mode(config_db_json, port,
                                                                                    split_num,
                                                                                    parsed_platform_json_by_breakout_modes)
        config_db_json["BREAKOUT_CFG"] = breakout_cfg_dict
        return SonicGeneralCli.create_extended_config_db_file(setup_name, config_db_json)

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
        return "extended_config_db.json"

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

    @staticmethod
    def get_config_db(dut_engine):
        config_db_json = dut_engine.run_cmd('cat {} ; echo'.format(SonicConst.CONFIG_DB_JSON_PATH), print_output=False)
        return json.loads(config_db_json)

    @staticmethod
    def is_spc1(cli_object, dut):
        """
        Function to check if the current DUT is SPC1
        :param dut: the DUT
        :param cli_object: cli_object
        """
        platform = cli_object.chassis.get_platform(dut)
        # if msn2 in platform, it's spc1. e.g. x86_64-mlnx_msn2700-r0
        if 'msn2' in platform:
            return True
        return False

    @staticmethod
    def show_version(dut_engine):
        return dut_engine.run_cmd('show version')

    @staticmethod
    def parse_platform_json(topology_obj, platform_json_obj, parse_by_breakout_modes=False):
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
            ports_speeds_by_modes_info = SonicGeneralCli.generate_mock_ports_speeds(topology_obj,
                                                                                    parse_by_breakout_modes)
        else:
            for port_name, port_dict in platform_json_obj["interfaces"].items():
                lanes = port_dict[SonicConstant.LANES].split(",")
                breakout_modes = re.findall(breakout_options, ",".join(list(port_dict[SonicConstant.BREAKOUT_MODES].keys())))
                breakout_ports = ["Ethernet{}".format(lane) for lane in lanes]
                for port in breakout_ports:
                    if port in topology_obj.players_all_ports['dut']:
                        if parse_by_breakout_modes:
                            ports_speeds_by_modes_info[port] = get_split_mode_supported_breakout_modes(breakout_modes)
                        else:
                            ports_speeds_by_modes_info[port] = get_split_mode_supported_speeds(breakout_modes)
        return ports_speeds_by_modes_info

    @staticmethod
    def generate_mock_ports_speeds(topology_obj,  parse_by_breakout_modes=False):
        if parse_by_breakout_modes:
            raise AssertionError("This version doesn't support platform.json,\n"
                                 "there no mock option for interfaces breakout mode option")
        else:
            mock_ports_speeds_by_modes_info ={}
            port_list = get_dut_default_ports_list(topology_obj)
            for port in port_list:
                mock_ports_speeds_by_modes_info[port] = {
                    1: ['100G', '50G', '25G', '10G'],
                    2: ['50G', '25G', '10G'],
                    4: ['25G', '10G']
                }
            logger.debug("Mock ports speed option dictionary: {}".format(mock_ports_speeds_by_modes_info))
            return mock_ports_speeds_by_modes_info

    @staticmethod
    def show_warm_restart_state(dut_engine):
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
        warm_restart_state = dut_engine.run_cmd("show warm_restart state")
        warm_restart_state_dict = generic_sonic_output_parser(warm_restart_state,
                                                              headers_ofset=0,
                                                              len_ofset=1,
                                                              data_ofset_from_start=2,
                                                              data_ofset_from_end=None,
                                                              column_ofset=2,
                                                              output_key='name')
        return warm_restart_state_dict


    @staticmethod
    def get_base_and_target_images(dut_engine):
        """
        This method getting base and target image from "sonic-installer list" output
        """
        installed_list_output = SonicGeneralCli.get_sonic_image_list(dut_engine)
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
