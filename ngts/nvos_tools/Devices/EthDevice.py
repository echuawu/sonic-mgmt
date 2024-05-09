import logging
import os

from ngts.nvos_constants.constants_nvos import NvosConst
from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts

logger = logging.getLogger()


class EthSwitch(BaseSwitch):

    def __init__(self, asic_amount):
        super().__init__()
        self.asic_amount = asic_amount
        self.open_api_port = "8765"
        self.default_password = os.environ["CUMULUS_SWITCH_PASSWORD"]
        self.default_username = os.environ["CUMULUS_SWITCH_USER"]
        self.manufacture_password = "cumulus"

    def _init_constants(self):
        super()._init_constants()
        self.pre_login_message = "None\n"
        self.post_login_message = "\nWelcome to NVIDIA Cumulus (R) Linux (R)\n\nFor support and online " \
                                  "technical documentation, visit\nhttps://www.nvidia.com/en-us/support\n\nThe " \
                                  "registered trademark Linux (R) is used pursuant to a sublicense from LMI,\nthe " \
                                  "exclusive licensee of Linus Torvalds, owner of the mark on a world-wide\nbasis.\n"
        self.install_from_onie_timeout = 10 * 60
        self.install_success_patterns = ['Debian GNU/Linux 10 .*', NvosConst.INSTALL_BOOT_PATTERN]

    def ib_ports_num(self):
        return 0

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        return DutUtilsTool.wait_for_cumulus_to_become_functional(engine)

    def reload_device(self, engine, cmd_set, validate=False):
        engine.run_cmd_set(cmd_set, validate=False)

    def _init_fan_list(self):
        self.fan_list = ["Fan1", "Fan2", "Fan3", "Fan4", "Fan5", "Fan6", "Fan7", "Fan8", "Fan9", "Fan10", "Fan11", "Fan12"]

    def _init_led_list(self):
        self.led_list = ["Fan Tray 1", "Fan Tray 2", "Fan Tray 3", "Fan Tray 4", "Fan Tray 5", "Fan Tray 6", "Psu", "System"]

    def _init_platform_lists(self):
        super()._init_platform_lists()
        self.platform_environment_list = self.fan_list + self.led_list + ["PSU1", "PSU2"] + self.psu_fan_list
        self.platform_hw_list = ["base-mac", "cpu", "disk-size", "manufacturer", "memory", "model", "onie-version",
                                 "part-number", "platform-name", "port-layout", "product-name", "serial-number",
                                 "system-mac", "asic-model", "asic-vendor"]
        self.hw_comp_list = ["device"]
        self.hw_comp_prop = ["model", "type"]
        self.fan_prop = ["max-speed", "min-speed", "speed", "state"]

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.psu_fan_list = ["PSU1Fan1", "PSU2Fan1"]
        self.platform_env_psu_prop = ["state"]

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]

    def _init_system_lists(self):
        self.user_fields = ['root', 'cumulus']

    def _init_security_lists(self):
        self.kex_algorithms = ['ecdh-sha2-nistp521', 'diffie-hellman-group-exchange-sha256',
                               'curve25519-sha256@libssh.org', 'diffie-hellman-group18-sha512',
                               'kex-strict-s-v00@openssh.com', 'ecdh-sha2-nistp256',
                               'curve25519-sha256', 'ecdh-sha2-nistp384', 'diffie-hellman-group14-sha256',
                               'sntrup761x25519-sha512@openssh.com', 'diffie-hellman-group16-sha512']

    def _init_password_hardening_lists(self):
        self.aaa_admin_role = 'nvue-admin'
        self.aaa_monitor_role = 'nvue-monitor'
        self.local_test_users = [{AaaConsts.USERNAME: AaaConsts.LOCALADMIN,
                                  AaaConsts.PASSWORD: AaaConsts.STRONG_PASSWORD,
                                  AaaConsts.ROLE: self.aaa_admin_role},
                                 {AaaConsts.USERNAME: AaaConsts.LOCALMONITOR,
                                  AaaConsts.PASSWORD: AaaConsts.STRONG_PASSWORD,
                                  AaaConsts.ROLE: self.aaa_monitor_role}]

    def _init_available_databases(self):
        super()._init_available_databases()

    def _init_services(self):
        super()._init_services()

    def _init_dependent_services(self):
        super()._init_dependent_services()

    def _init_dockers(self):
        super()._init_dockers()


# -------------------------- Anaconda Switch ----------------------------
class AnacondaSwitch(EthSwitch):
    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.core_count = 8
        self.asic_type = 'Spectrum2'


# -------------------------- Mlx4700 Switch -----------------------------
class Mlx4700Switch(EthSwitch):
    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.core_count = 8
        self.asic_type = 'Spectrum3'
