import time
import logging
import allure
import pexpect
from retry.api import retry_call

from ngts.constants.constants import OnieConsts
from infra.tools.connection_tools.onie_engine import OnieEngine
from ngts.constants.constants import InfraConst
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive

logger = logging.getLogger()

ONIE_UPDATER_URL = f'http://10.208.1.55/onie_only/{OnieConsts.ONIE_VERSION}/9600/onie-updater-x86_64-mlnx_x86-r0'
DEFAULT_PROMPT = ["ONIE:.+ #", pexpect.EOF]


class OnieInstallationError(Exception):
    """
    An exception for errors that reflect problematic behavior of the OS installation
    """


class SonicOnieCli:
    """
    This class defines methods over Onie
    """
    def __init__(self, host_ip):
        self.ip = host_ip
        self.engine = None
        self.create_engine()

    def create_engine(self, create_force=False):
        if self.engine is None or create_force:
            self.engine = OnieEngine(self.ip, 'root').create_engine()
            retry_call(self.get_pexpect_entry,
                       fargs=[['#']],
                       tries=3,
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
        if not self.required_onie_version_installed():
            with allure.step(f"Install required ONIE version {OnieConsts.ONIE_VERSION}-9600"):
                logger.info(
                    f'Switch have not required ONIE version {OnieConsts.ONIE_VERSION}-9600, ONIE will be updated')
                self.confirm_onie_boot_mode_update()
                # restore engine after reboot
                self.create_engine(True)
                self.run_cmd_set([f'onie-self-update {ONIE_UPDATER_URL}'])
                self.post_reboot_delay()
        else:
            logger.info(f'Switch already installed with required ONIE version {OnieConsts.ONIE_VERSION}-9600')

    def required_onie_version_installed(self):
        onie_version_output, _ = self.run_cmd_set(['onie-sysinfo -v'])
        return OnieConsts.ONIE_VERSION in onie_version_output
