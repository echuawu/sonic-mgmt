import logging
import os

from ngts.nvos_constants.constants_nvos import NvosConst, FansConsts, PlatformConsts, CumulusConsts, DiskConsts
from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.nvos_tools.infra.ValidationTool import ExpectedString

logger = logging.getLogger()


class EthSwitch(BaseSwitch):

    def __init__(self, asic_amount):
        super().__init__()
        self.asic_amount = asic_amount
        self._init_sensors_dict()
        self.open_api_port = "8765"
        self.default_password = os.environ["CUMULUS_SWITCH_PASSWORD"]
        self.default_username = os.environ["CUMULUS_SWITCH_USER"]
        self.manufacture_password = "cumulus"
        self.switch_type = CumulusConsts.ETH_SWITCH_TYPE
        self.init_documents_consts()
        self.init_cli_coverage_prop("cumulus")

    def init_documents_consts(self):
        super().init_documents_consts()

    def get_voltage_sensors(self, dut_engine=None):
        return self.voltage_sensors

    def _init_constants(self):
        super()._init_constants()
        self.pre_login_message = "None\n"
        self.post_login_message = "\nWelcome to NVIDIA Cumulus (R) Linux (R)\n\nFor support and online " \
                                  "technical documentation, visit\nhttps://www.nvidia.com/en-us/support\n\nThe " \
                                  "registered trademark Linux (R) is used pursuant to a sublicense from LMI,\nthe " \
                                  "exclusive licensee of Linus Torvalds, owner of the mark on a world-wide\nbasis.\n"
        self.install_from_onie_timeout = 10 * 60
        self.login_pattern = CumulusConsts.LINUX_BOOT_PATTERN
        self.install_patterns = {self.login_pattern: 0, NvosConst.INSTALL_BOOT_PATTERN: 1,
                                 CumulusConsts.LOGIN_BOOT_PATTERN: 2}
        self.install_success_patterns = list(self.install_patterns.keys())

        self.voltage_sensors = ["PMIC-1-PSU-12V-RAIL-IN", "PMIC-2-PSU-12V-RAIL-IN",
                                "PMIC-2-ASIC-1.2V_MAIN-RAIL-OUT2", "PMIC-2-ASIC-1.8V_MAIN-RAIL-OUT1",
                                "PMIC-3-ASIC-1.8V_T0_3-RAIL-OUT2", "PMIC-3-COMEX-1.05V-RAIL-OUT",
                                "PMIC-3-PSU-12V-RAIL-IN", "PMIC-3-PSU-12V-RAIL-IN1",
                                "PMIC-5-ASIC-1.2V_T0_3-RAIL-OUT1", "PMIC-5-ASIC-1.2V_T4_7-RAIL-OUT2",
                                "PMIC-5-PSU-12V-RAIL-IN", "PMIC-6-COMEX-1.8V-RAIL-OUT1",
                                "PMIC-6-PSU-12V-RAIL-IN1", "PMIC-6-PSU-12V-RAIL-IN2",
                                "PMIC-7-COMEX-1.2V-RAIL-OUT", "PMIC-7-PSU-12V-RAIL-IN1",
                                "PMIC-7-PSU-12V-RAIL-IN2", "PSU-2L-12V-RAIL-OUT",
                                "PSU-2L-220V-RAIL-IN"]
        self.constants.firmware.remove(PlatformConsts.FW_ASIC)

        self.show_platform_output.update({
            "system-mac": ExpectedString(regex=r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}"),
            "manufacturer": "Mellanox"
        })

        self.disk_partition_capacity_limit = 70  # Percent value
        self.disk_minimum_free_space = 5.5  # Gig

    def ib_ports_num(self):
        return 0

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        return DutUtilsTool.wait_for_cumulus_to_become_functional(engine)

    def reload_device(self, engine, cmd_set, validate=False):
        engine.run_cmd_set(cmd_set, validate=False)

    def _init_fan_list(self):
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1", "FAN2/2", "FAN3/1", "FAN3/2", "FAN4/1", "FAN4/2",
                         "FAN5/1", "FAN5/2", "FAN6/1", "FAN6/2"]

    def _init_led_list(self):
        self.led_list = ["FAN1", "FAN2", "FAN3", "FAN4", "FAN5", "FAN6", "PSU", "SYSTEM"]

    def _init_platform_lists(self):
        super()._init_platform_lists()
        self.platform_hw_list = ["base-mac", "cpu", "disk-size", "manufacturer", "memory", "model", "onie-version",
                                 "part-number", "platform-name", "port-layout", "product-name", "serial-number",
                                 "system-mac", "asic-model", "asic-vendor"]
        self.hw_comp_list = ["device"]
        self.hw_comp_prop = ["model", "type"]
        self.fan_prop = ["max-speed", "min-speed", "speed", "state"]
        self.platform_environment_fan_values = {
            "state": FansConsts.STATE_OK, "direction": None, "current-speed": None,
            "min-speed": ExpectedString(range_min=2000, range_max=10000),
            "max-speed": ExpectedString(range_min=20000, range_max=40000)}
        self.platform_environment_absent_fan_values = {
            "state": FansConsts.STATE_ABSENT, "direction": "N/A", "current-speed": "N/A",
            "min-speed": "N/A", "max-speed": "N/A"}
        self.platform_inventory_items = self.fan_list + self.psu_list + self.psu_fan_list \
            + [PlatformConsts.HW_COMP_SWITCH]
        self.platform_inventory_switch_values = {
            "model": ExpectedString(regex="MSN.*"),
            "serial": None,
            "hardware-version": None,
            "state": FansConsts.STATE_OK,
            "type": PlatformConsts.HW_COMP_SWITCH.lower()}

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.psu_fan_list = ["PSU1/FAN", "PSU2/FAN"]
        self.platform_env_psu_prop = ["state"]

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors = ["Asic-Temp-Sensor", "CPU-Package-Sensor", "Main-Board-Ambient-Sensor",
                                    "CPU-Core-Sensor-0", "CPU-Core-Sensor-1",
                                    "CPU-Core-Sensor-2", "CPU-Core-Sensor-3",
                                    "PSU1-Temp-Sensor", "PSU2-Temp-Sensor",
                                    "CPU-Core-Sensor-0", "CPU-Core-Sensor-1", "Port-Ambient-Sensor"]

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.voltage_sensors,
                             "TEMPERATURE": self.temperature_sensors}

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
        self.asic_type = 'Spectrum-2'
        self.constants.firmware.append(PlatformConsts.FW_SPECTRUM2)
        self.show_platform_output.update({
            "product-name": "MSN3700",
            "asic-model": self.asic_type
        })

# -------------------------- Mlx2410 Switch -----------------------------


class Mlx2410Switch(EthSwitch):
    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.core_count = 2
        self.asic_type = 'Spectrum-1'
        self.constants.firmware.append(PlatformConsts.FW_SPECTRUM1)

        self.show_platform_output.update({
            "product-name": "MSN2410",
            "asic-model": self.asic_type
        })

        self.voltage_sensors = ["VIN", "VOUT1", "VOUT2"]

    def _init_fan_list(self):
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1", "FAN2/2", "FAN3/1", "FAN3/2", "FAN4/1", "FAN4/2"]

# -------------------------- Mlx4600 Switch -----------------------------


class Mlx4600Switch(EthSwitch):
    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.core_count = 8
        self.asic_type = 'Spectrum-3'
        self.constants.firmware.append(PlatformConsts.FW_SPECTRUM3)

        self.show_platform_output.update({
            "product-name": "MSN4600",
            "asic-model": self.asic_type
        })

        self.voltage_sensors = ["PMIC-1-PSU-12V-RAIL-IN", "PMIC-2-PSU-12V-RAIL-IN",
                                "PMIC-2-ASIC-1.2V_MAIN-RAIL-OUT2", "PMIC-2-ASIC-1.8V_MAIN-RAIL-OUT1",
                                "PMIC-3-ASIC-1.8V_T0_3-RAIL-OUT2", "PMIC-3-COMEX-1.05V-RAIL-OUT",
                                "PMIC-3-PSU-12V-RAIL-IN", "PMIC-3-PSU-12V-RAIL-IN1",
                                "PMIC-5-ASIC-1.2V_T0_3-RAIL-OUT1", "PMIC-5-ASIC-1.2V_T4_7-RAIL-OUT2",
                                "PMIC-5-PSU-12V-RAIL-IN", "PMIC-6-COMEX-1.8V-RAIL-OUT1",
                                "PMIC-6-PSU-12V-RAIL-IN1", "PMIC-6-PSU-12V-RAIL-IN2",
                                "PMIC-7-COMEX-1.2V-RAIL-OUT", "PMIC-7-PSU-12V-RAIL-IN1",
                                "PMIC-7-PSU-12V-RAIL-IN2", "PSU-1R-12V-RAIL-OUT",
                                "PSU-1R-220V-RAIL-IN"]

    def _init_fan_list(self):
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1"]

# -------------------------- Mlx4700 Switch -----------------------------


class Mlx4700Switch(EthSwitch):
    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.core_count = 8
        self.asic_type = 'Spectrum-3'
        self.constants.firmware.append(PlatformConsts.FW_SPECTRUM3)

        self.show_platform_output.update({
            "product-name": "MSN4700",
            "asic-model": self.asic_type
        })
