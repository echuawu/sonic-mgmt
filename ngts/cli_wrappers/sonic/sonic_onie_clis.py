import time
import logging
import allure
import pexpect
from retry.api import retry_call

from infra.tools.connection_tools.onie_engine import OnieEngine
from ngts.constants.constants import InfraConst, PlatformTypesConstants
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from ngts.helpers.json_file_helper import extract_fw_data

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

    def __init__(self, host_ip, fw_pkg_path=None, platform_params=None):
        self.ip = host_ip
        self.engine = None
        self.latest_onie_version = ''
        self.latest_onie_url = ''
        self.is_nos_installed = False
        self.fw_pkg_path = fw_pkg_path
        self.platform_params = platform_params
        self.create_engine()

    def create_engine(self, create_force=False):
        if self.engine is None or create_force:
            self.engine = OnieEngine(self.ip, 'root').create_engine()
            retry_call(self.get_pexpect_entry,
                       fargs=[['#'], 60],
                       tries=5,
                       delay=5,
                       logger=logger)
            self.engine.timeout = 10

    def run_cmd_set(self, cmd_list, custum_prompts=""):
        prompts = custum_prompts if custum_prompts else DEFAULT_PROMPT
        stdout = ""
        pexpect_entry = ""
        for cmd in cmd_list:
            logger.info(f'Executing command: {cmd}')
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
        get_boot_info_cmd = 'cat /proc/cmdline'
        boot_info_output, _ = self.run_cmd_set([get_boot_info_cmd])
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

    def reboot(self):
        self.run_cmd_set(['reboot'])
        self.post_reboot_delay()

    def post_reboot_delay(self):
        ping_till_alive(should_be_alive=False, destination_host=self.ip, tries=10)
        ping_till_alive(should_be_alive=True, destination_host=self.ip)
        logger.info(
            f'Sleeping {InfraConst.SLEEP_AFTER_RRBOOT} seconds after switch reply to ping to handle ssh session')
        time.sleep(InfraConst.SLEEP_AFTER_RRBOOT)

    def install_image(self, image_url, timeout=60, num_retry=10):
        self.confirm_onie_boot_mode_install()

        # restore engine after reboot
        self.create_engine(True)

        prompts = ["Installed SONiC base image SONiC-OS successfully"] +\
                  [str(pexpect.TIMEOUT)] + DEFAULT_PROMPT

        stdout, pexpect_entry = self.run_cmd_set([f"onie-nos-install {image_url}"])
        if 'wget: download timed out' in stdout:
            logger.error('Failed to download SONiC image from ONIE. Trying again.')
            stdout, pexpect_entry = self.run_cmd_set([f"onie-nos-install {image_url}"])

        while num_retry > 0:
            if pexpect_entry == 0:
                break
            elif pexpect_entry == 3:
                num_retry = num_retry - 1
                pexpect_entry = self.get_pexpect_entry(prompts)
                logger.info(f"Got timeout on {num_retry} time..")
                logger.info(f"Printing output: {self.engine.before}")
            else:
                logger.info(f'Catched pexpect entry: {pexpect_entry}')
                raise OnieInstallationError(f"Failed to install sonic image. {stdout}")
        else:
            logger.info(f"Did not installed image in {num_retry * timeout} seconds.")
            raise OnieInstallationError(f"Failed to install sonic image. {stdout}")
        logger.info('SONiC installed')
        prompts = [pexpect.EOF, pexpect.TIMEOUT]
        self.get_pexpect_entry(prompts, timeout=15)
        stdout = self.get_stdout()
        return stdout

    def update_onie(self):
        if self.required_onie_installation():
            with allure.step(f"Install required ONIE version {self.latest_onie_version}"):
                logger.info(
                    f'Switch have not required ONIE version {self.latest_onie_version}, ONIE will be updated')
                self.confirm_onie_boot_mode_update()
                # restore engine after reboot
                self.create_engine(True)
                if self.is_nos_installed:
                    # If NOS installed - set GRUB force boot into ONIE
                    cmds_list = ['mkdir /boot',
                                 'mount /dev/sda3  /boot/',
                                 'grub-editenv /boot/grub/grubenv set next_entry=ONIE']
                    self.run_cmd_set(cmds_list)
                self.run_cmd_set([f'onie-self-update {self.latest_onie_url}'])
                self.post_reboot_delay()
        else:
            with allure.step(f"Doesn't required ONIE installation"):
                logger.info(f"Doesn't required ONIE installation")

    def required_onie_installation(self):
        onie_version_output, _ = self.run_cmd_set(['onie-sysinfo -v'])
        self.latest_onie_version, self.latest_onie_url = get_latest_onie_version(self.fw_pkg_path, self.platform_params)
        return self.latest_onie_version not in onie_version_output


def get_latest_onie_version(fw_pkg_path, platform_params):
    latest_onie_version = ''
    latest_onie_url = ''
    if fw_pkg_path is None:
        logger.warning("No firmware package file path specified.")
    else:
        logger.info(f"Get latest ONIE version from specified file {fw_pkg_path}")
        fw_data = extract_fw_data(fw_pkg_path)
        if platform_params.filtered_platform.upper() in fw_data["chassis"]:
            onie_info_list = fw_data["chassis"][platform_params.filtered_platform.upper()]["component"]["ONIE"]
            for onie_version_info in onie_info_list:
                if latest_onie_version < onie_version_info["version"]:
                    latest_onie_version = onie_version_info["version"]
                    latest_onie_url = onie_version_info["firmware"]
        else:
            logger.warning(f"The specified platform {platform_params.filtered_platform.upper()} not in the"
                           f" provided firmware package file {fw_pkg_path}")
        logger.info(f"The latest ONIE version is {latest_onie_version}, the latest ONIE url is {latest_onie_url}")
    return latest_onie_version, latest_onie_url
