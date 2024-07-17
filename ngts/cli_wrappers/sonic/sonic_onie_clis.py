import time
import logging
import allure
import pexpect
from retry.api import retry_call

from infra.tools.connection_tools.onie_engine import OnieEngine
from infra.tools.general_constants.constants import SonicNvidiaAirConstants
from ngts.constants.constants import InfraConst, PlatformTypesConstants
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from ngts.helpers.json_file_helper import extract_fw_data
from ngts.helpers.run_process_on_host import run_process_on_host
from ngts.constants.constants import MarsConstants

logger = logging.getLogger()

BASE_ONIE_UPDATER_URL = InfraConst.HTTTP_SERVER_FIT16 + '/onie_only/{}/9600/onie-updater-x86_64-mlnx_x86-r0'
SPECIAL_ONIE_UPDATER_URL = {
    PlatformTypesConstants.FILTERED_PLATFORM_ALLIGATOR:
        InfraConst.HTTTP_SERVER_FIT16 + '/onie_only/sn2201/{}/115200/onie-updater-x86_64-nvidia_sn2201-r0'
}
DEFAULT_PROMPT = ["ONIE:.+ #", pexpect.EOF]


class OnieInstallationError(Exception):
    """
    An exception for errors that reflect problematic behavior of the OS installation
    """


class SonicOnieCli:
    """
    This class defines methods over Onie
    """

    def __init__(self, host_ip, ssh_port=22, fw_pkg_path=None, platform_params=None):
        self.ip = host_ip
        self.ssh_port = ssh_port
        self.engine = None
        self.latest_onie_version = ''
        self.latest_onie_url = ''
        self.is_nos_installed = False
        self.fw_pkg_path = fw_pkg_path
        self.platform_params = platform_params
        self.create_engine()

    def create_engine(self, create_force=False):
        if self.engine is None or create_force:
            self.engine = OnieEngine(self.ip, 'root', self.ssh_port).create_engine()
            retry_call(self.get_pexpect_entry,
                       fargs=[['#'], 10],
                       tries=3,
                       delay=5,
                       logger=logger)
            self.engine.timeout = 10

    def run_cmd_set(self, cmd_list, custum_prompts=""):
        prompts = custum_prompts if custum_prompts else DEFAULT_PROMPT
        stdout = ""
        pexpect_entry = ""
        for cmd in cmd_list:
            logger.info(f'Executing command on {self.ip}: {cmd}')
            self.engine.sendline(cmd)
            pexpect_entry = self.get_pexpect_entry(prompts)
            stdout = self.get_stdout(stdout)
        return stdout, pexpect_entry

    def get_pexpect_entry(self, prompts, timeout=None):
        return self.engine.expect(prompts, timeout=timeout)

    def get_stdout(self, stdout=""):
        stdout += self.engine.before.decode('ascii')
        logger.info(stdout)
        return stdout

    def confirm_onie_boot_mode_install(self):
        self.confirm_onie_boot_mode('install')

    def confirm_onie_boot_mode_update(self):
        self.confirm_onie_boot_mode('update')

    def confirm_onie_boot_mode(self, mode):
        boot_info_output = self.get_boot_info()
        if f'boot_reason={mode}' not in boot_info_output:
            logger.info(f'Changing the ONIE boot mode to {mode}')
            self.is_nos_installed, _ = self.run_cmd_set(['ls /dev/sda3'])
            if self.is_nos_installed:
                # If NOS installed - set GRUB force boot into ONIE
                cmds_list = ['mkdir /boot',
                             'mount /dev/sda3  /boot/',
                             'grub-editenv /boot/grub/grubenv set next_entry=ONIE',
                             'mount LABEL=ONIE-BOOT /mnt/onie-boot',
                             'onie-nos-mode -c -v']
                self.run_cmd_set(cmds_list)
            self.run_cmd_set([f'onie-boot-mode -o {mode}'])
            self.reboot()
        else:
            logger.info(f'Switch is in ONIE {mode} mode')

    def get_boot_info(self):
        get_boot_info_cmd = 'cat /proc/cmdline'
        # right after reboot, we can get the empty output from cmd run.
        for _ in range(3):
            boot_info_output, _ = self.run_cmd_set([get_boot_info_cmd])
            if 'boot_reason' in boot_info_output:
                break
            time.sleep(1)
        return boot_info_output

    def reboot(self):
        self.run_cmd_set(['reboot'])
        self.post_reboot_delay()

    def post_reboot_delay(self):
        check_port_status_till_alive(should_be_alive=False, destination_host=self.ip, destination_port=self.ssh_port,
                                     tries=30)
        check_port_status_till_alive(should_be_alive=True, destination_host=self.ip, destination_port=self.ssh_port)
        logger.info(
            f'Sleeping {InfraConst.SLEEP_AFTER_RRBOOT} seconds after switch reply to ping to handle ssh session')
        time.sleep(InfraConst.SLEEP_AFTER_RRBOOT)

    def install_image(self, image_path, platform_params, topology_obj, timeout=60, num_retry=10):
        self.confirm_onie_boot_mode_install()

        # restore engine after reboot
        self.create_engine(True)

        prompts = ["Installed.*base\\s+image.*successfully", pexpect.TIMEOUT]

        full_image_path = f"{MarsConstants.HTTP_SERVER_NBU_NFS}{image_path}"
        image_name = image_path.split('/')[-1]
        local_image_file = '/tmp/' + image_name

        logger.info('Starting download sonic image via http')
        download_image_cmd = f"wget -O {local_image_file} {full_image_path}"
        retry_call(self.run_cmd_set, fargs=[[download_image_cmd]], tries=5, delay=10, logger=logger)

        logger.info('Starting onie-nos-install sonic image')
        stdout, pexpect_entry = self.run_cmd_set([f"onie-nos-install {local_image_file}"], prompts)

        while num_retry > 0:
            if pexpect_entry == 0:
                break
            elif pexpect_entry == 1:
                num_retry = num_retry - 1
                pexpect_entry = self.get_pexpect_entry(prompts)
                logger.info(f"Got timeout on {num_retry} time..")
                logger.info(f"Printing output: {self.engine.before}")
            else:
                logger.info(f'Caught pexpect entry: {pexpect_entry}')
                raise OnieInstallationError(f"Failed to install sonic image. {stdout}")
        else:
            logger.info(f"Did not installed image in {num_retry * timeout} seconds.")
            raise OnieInstallationError(f"Failed to install sonic image. {stdout}")
        logger.info('SONiC installed')
        prompts = [pexpect.EOF, pexpect.TIMEOUT]
        self.get_pexpect_entry(prompts, timeout=15)
        stdout = self.get_stdout()
        return stdout

    def download_image(self, image_path, platform_params, topology_obj):
        """
        Download SONiC image into /tmp/sonic-mellanox.bin on DUT(ONIE)
        """
        logger.info(f'Getting SONiC image from: {image_path} using SCP')
        image_name = 'sonic-mellanox.bin'
        dst_image_file_path = f'/tmp/{image_name}'

        with allure.step('Downloading SONiC image'):
            if 'air' in platform_params.setup_name:
                self.download_image_into_air(topology_obj, image_path, image_name, dst_image_file_path)
                dst_image_file_path = f'http://{SonicNvidiaAirConstants.NVIDIA_AIR_OOB_MGMT_SERVER_IP}/{image_name}'
            else:
                self.download_image_into_nvidia_lab(image_path, dst_image_file_path)

        return dst_image_file_path

    @staticmethod
    def download_image_into_air(topology_obj, image_path, image_name, dst_image_file_path):
        """
        Download SONiC image into NvidiaAir simulation
        First download image to oob-mgmt-server
        Second download image from oob-mgmt-server to DUT(ONIE)
        """
        # Copy to oob-mgmt-server
        oob_engine = topology_obj.players['oob-mgmt-server']['engine']
        oob_engine.copy_file(source_file=image_path, file_system='/tmp', dest_file=image_name)
        oob_engine.run_cmd(f'sudo mv {dst_image_file_path} /var/www/html/')

    def download_image_into_nvidia_lab(self, image_path, dst_image_file_path):
        """
        Download SONiC image using SCP directly to DUT(ONIE)
        """
        # Copy directly to DUT
        scp_cmd = f'sshpass -p \'root\' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P {self.ssh_port} ' \
            f'{image_path} root@{self.ip}:{dst_image_file_path}'
        out, err, rc = run_process_on_host(scp_cmd, timeout=1800)
        if rc:
            logger.error(f'Failed copy SONiC image, std_out: {out}, std_err: {err}, rc: {rc}')
            raise AssertionError('SCP copy file to DUT failed')

    def update_onie(self):
        if self.required_onie_installation():
            with allure.step(f"Install on {self.ip} required ONIE version {self.latest_onie_version}"):
                logger.info(
                    f'Switch {self.ip} have not required ONIE version {self.latest_onie_version}, ONIE will be updated')
                self.confirm_onie_boot_mode_update()
                # restore engine after reboot
                self.create_engine(True)
                if self.is_nos_installed:
                    # If NOS installed - set GRUB force boot into ONIE
                    cmds_list = ['mkdir /boot',
                                 'mount /dev/sda3  /boot/',
                                 'grub-editenv /boot/grub/grubenv set next_entry=ONIE']
                    self.run_cmd_set(cmds_list)
                cmd_output, _ = self.run_cmd_set([f'onie-self-update {self.latest_onie_url}'])
                logger.info(f'onie-self-update command output:\n{cmd_output}')
                self.post_reboot_delay()
        else:
            with allure.step(f"Switch {self.ip} doesn't required ONIE installation"):
                logger.info(f"Switch {self.ip} doesn't required ONIE installation")

    def required_onie_installation(self):
        # right after reboot, we can get the empty output from cmd run.
        install_required = True
        for _ in range(3):
            onie_version_output, _ = self.run_cmd_set(['onie-sysinfo -v'])
            if '9600' in onie_version_output or '115200' in onie_version_output:
                break
            time.sleep(1)
        self.latest_onie_version, self.latest_onie_url = get_latest_onie_version(self.fw_pkg_path,
                                                                                 self.platform_params)
        # switch 10.245.20.39 is prod device, can't be updated by regular ONIE
        if self.latest_onie_version in onie_version_output or self.ip == '10.245.20.39':
            install_required = False
        return install_required


def get_latest_onie_version(fw_pkg_path, platform_params):
    latest_onie_version = ''
    latest_onie_url = ''
    if fw_pkg_path is None:
        logger.warning("No firmware package file path specified.")
    else:
        logger.info(f"Get latest ONIE version from specified file {fw_pkg_path}")
        fw_data = extract_fw_data(fw_pkg_path)
        chassis = platform_params.filtered_platform.upper()
        if chassis in fw_data["chassis"]:
            component = fw_data["chassis"][chassis]["component"]
        else:
            component = {}
        hostname = platform_params.host_name
        if "host" in fw_data and hostname in fw_data["host"]:
            for component_type in list(fw_data["host"][hostname]["component"].keys()):
                component[component_type] = fw_data["host"][hostname]["component"][component_type]

        if "ONIE" in component:
            onie_info_list = component["ONIE"]
            for onie_version_info in onie_info_list:
                if latest_onie_version < onie_version_info["version"]:
                    latest_onie_version = onie_version_info["version"]
                    latest_onie_url = onie_version_info["firmware"]
        else:
            logger.warning(f"The specified platform {platform_params.filtered_platform.upper()} not in the"
                           f" provided firmware package file {fw_pkg_path}")
        logger.info(f"The latest ONIE version is {latest_onie_version}, the latest ONIE url is {latest_onie_url}")
    return latest_onie_version, latest_onie_url
