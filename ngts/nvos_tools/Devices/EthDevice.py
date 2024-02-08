import logging
from abc import ABC
import os
from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool

logger = logging.getLogger()


class EthSwitch(BaseSwitch, ABC):

    def __init__(self, asic_amount):
        BaseSwitch.__init__(self)
        self.asic_amount = asic_amount
        self.open_api_port = "8765"
        self.default_password = os.environ["CUMULUS_SWITCH_PASSWORD"]
        self.default_username = os.environ["CUMULUS_SWITCH_USER"]

    def _init_constants(self):
        BaseSwitch._init_constants(self)
        self.pre_login_message = "None\n"
        self.post_login_message = "\nWelcome to NVIDIA Cumulus (R) Linux (R)\n\nFor support and online " \
                                  "technical documentation, visit\nhttps://www.nvidia.com/en-us/support\n\nThe " \
                                  "registered trademark Linux (R) is used pursuant to a sublicense from LMI,\nthe " \
                                  "exclusive licensee of Linus Torvalds, owner of the mark on a world-wide\nbasis.\n"

    def ib_ports_num(self):
        return 0

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        return DutUtilsTool.wait_for_cumulus_to_become_functional(engine)

    def reload_device(self, engine, cmd_set, validate=False):
        engine.run_cmd_set(cmd_set, validate=False)


# -------------------------- Anaconda Switch ----------------------------
class AnacondaSwitch(EthSwitch, ABC):

    def __init__(self):
        EthSwitch.__init__(self, asic_amount=1)

    def _init_constants(self):
        EthSwitch._init_constants(self)
        self.core_count = 8
        self.asic_type = 'GEN2'

    def _init_fan_list(self):
        EthSwitch._init_fan_list(self)

        self.fan_list = ["Fan1", "Fan2", "Fan3", "Fan4", "Fan5", "Fan6", "Fan7", "Fan8", "Fan9", "Fan10", "Fan11",
                         "Fan12"]
        self.psu_fan_list = ["PSU1Fan1", "PSU2Fan1"]
        self.fan_led_list = ["Fan Tray 1", "Fan Tray 2", "Fan Tray 3", "Fan Tray 4", "Fan Tray 5", "Fan Tray 6",
                             "Psu", "System"]
        self.fan_prop = ["max-speed", "min-speed", "speed", "state"]

    def _init_temperature(self):
        EthSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]
        self.platform_environment_list = self.fan_list + self.fan_led_list + ["PSU1", "PSU2"] + self.psu_fan_list

    def _init_platform_lists(self):
        self.platform_hw_list = ["base-mac", "cpu", "disk-size", "manufacturer", "memory", "model", "onie-version",
                                 "part-number", "platform-name", "port-layout", "product-name", "serial-number",
                                 "system-mac", "asic-model", "asic-vendor"]
        self.hw_comp_list = ["device"]
        self.hw_comp_prop = ["model", "type"]

    def _init_system_lists(self):
        self.system_list = []
        self.user_fields = ['root', 'cumulus']

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.platform_env_psu_prop = ["state"]
