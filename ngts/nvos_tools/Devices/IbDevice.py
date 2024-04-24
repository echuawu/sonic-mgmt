import logging
import os

import ngts.tests_nvos.general.security.tpm_attestation.constants as TpmConsts
from ngts.nvos_constants.constants_nvos import HealthConsts, PlatformConsts
from ngts.nvos_constants.constants_nvos import NvosConst, DatabaseConst, IbConsts, StatsConsts, FansConsts
from ngts.nvos_tools.Devices.BaseDevice import BaseSwitch
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.ValidationTool import ExpectedString

logger = logging.getLogger()


class IbSwitch(BaseSwitch):

    def __init__(self, asic_amount):
        super().__init__(asic_amount)
        self._init_sensors_dict()
        self.open_api_port = "443"
        self.default_password = os.environ["NVU_SWITCH_NEW_PASSWORD"]
        self.default_username = os.environ["NVU_SWITCH_USER"]
        self.prev_default_password = os.environ["NVU_SWITCH_PASSWORD"]
        self._init_ib_speeds()

    def verify_ib_ports_state(self, dut_engine, expected_port_state):
        logging.info(f"number of ports: {self.ib_ports_num}")
        output_dict = OutputParsingTool.parse_json_str_to_dictionary(
            Port.show_interface(dut_engine, '--applied')).returned_value
        err_msg = ""
        for key, value in output_dict.items():
            if value[IbInterfaceConsts.TYPE] == IbInterfaceConsts.IB_PORT_TYPE and expected_port_state not in \
                    value[IbInterfaceConsts.LINK][IbInterfaceConsts.DHCP_STATE].keys():
                err_msg += "{} state is {}".format(key,
                                                   value[IbInterfaceConsts.LINK][IbInterfaceConsts.DHCP_STATE].keys())

        return ResultObj(False, err_msg) if err_msg else ResultObj(True, "", "")

    def _init_ib_speeds(self):
        self.invalid_ib_speeds = {'qdr': '40G'}
        self.supported_ib_speeds = {'hdr': '200G', 'edr': '100G', 'fdr': '56G', 'sdr': '10G', 'ndr': '400G'}

    def _init_fan_list(self):
        super()._init_fan_list()
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1", "FAN2/2", "FAN3/1", "FAN3/2", "FAN4/1", "FAN4/2",
                         "FAN5/1", "FAN5/2", "FAN6/1", "FAN6/2"]
        self.fan_led_list = ['FAN1', 'FAN2', 'FAN3', 'FAN4', 'FAN5', 'FAN6', "PSU_STATUS", "STATUS", "UID"]

    def _init_system_lists(self):
        super()._init_system_lists()
        self.user_fields = ['admin', 'monitor']

    def _init_security_lists(self):
        super()._init_security_lists()
        self.kex_algorithms = ['curve25519-sha256', 'curve25519-sha256@libssh.org', 'diffie-hellman-group16-sha512',
                               'diffie-hellman-group18-sha512', 'diffie-hellman-group14-sha256']

    def _init_available_databases(self):
        super()._init_available_databases()
        self.available_databases.update(
            {DatabaseConst.APPL_DB_NAME: DatabaseConst.APPL_DB_ID,
             DatabaseConst.ASIC_DB_NAME: DatabaseConst.ASIC_DB_ID,
             # DatabaseConst.COUNTERS_DB_NAME: DatabaseConst.COUNTERS_DB_ID, - disabled for now
             DatabaseConst.CONFIG_DB_NAME: DatabaseConst.CONFIG_DB_ID,
             DatabaseConst.STATE_DB_NAME: DatabaseConst.STATE_DB_ID
             })

        self.available_tables['database'] = {
            DatabaseConst.APPL_DB_ID:
            {"ALIAS_PORT_MAP": self.get_ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
            {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.get_ib_ports_num() + 1,
             "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 1,
             "LANES": 1,
             "VIDCOUNTER": 1,
             "RIDTOVID": 1,
             "HIDDEN": 1,
             "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
            {"COUNTERS_PORT_NAME_MAP": 1,
             "COUNTERS:oid": self.get_ib_ports_num()},
            DatabaseConst.CONFIG_DB_ID:
            {"IB_PORT": self.get_ib_ports_num(),
             "FEATURE": 11,
             "CONFIG_DB_INITIALIZED": 1,
             "DEVICE_METADATA": 1,
             "VERSIONS": 1,
             "KDUMP": 1}
        }
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update(
            {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.get_ib_ports_num() / 2,
             "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
             "LANES": 0,
             "VIDCOUNTER": 0,
             "RIDTOVID": 0,
             "HIDDEN": 0,
             "COLDVIDS": 0})

        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update(
            {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.get_ib_ports_num(),
             "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
             "LANES": 0,
             "VIDCOUNTER": 0,
             "RIDTOVID": 0,
             "HIDDEN": 0,
             "COLDVIDS": 0})

        self.available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.get_ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.get_ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.get_ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.get_ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': self.available_tables_per_asic})

    def _init_services(self):
        super()._init_services()
        self.available_services.extend((
            'docker.service', 'database.service', 'hw-management.service', 'config-setup.service',
            'updategraph.service', 'ntp.service', 'hostname-config.service', 'ntp-config.service',
            'rsyslog-config.service', 'procdockerstatsd.service',
            'configmgrd.service', 'countermgrd.service', 'portsyncmgrd.service'
        ))
        for deamon in NvosConst.DOCKER_PER_ASIC_LIST:
            for asic_num in range(0, self.asic_amount):
                self.available_services.append('{deamon}@{asic_num}.service'.format(deamon=deamon, asic_num=asic_num))

    def _init_dependent_services(self):
        super()._init_dependent_services()
        self.dependent_services.append(NvosConst.SYM_MGR_SERVICES)

    def _init_dockers(self):
        super()._init_dockers()
        self.available_dockers.extend(('database', 'ib-utils', 'gnmi-server'))
        for deamon in NvosConst.DOCKER_PER_ASIC_LIST:
            for asic_num in range(0, self.asic_amount):
                self.available_dockers.append("{deamon}{asic_num}".format(deamon=deamon, asic_num=asic_num))

    def _init_constants(self):
        super()._init_constants()
        self.health_monitor_config_file_path = ""
        self.ib_ports_num = 64
        self.primary_asic = f"{IbConsts.DEVICE_ASIC_PREFIX}1"
        self.primary_swid = f"{IbConsts.SWID}0"
        self.primary_ipoib_interface = IbConsts.IPOIB_INT0
        self.multi_asic_system = False
        self.install_success_patterns = [NvosConst.INSTALL_SUCCESS_PATTERN]
        self.mst_dev_name = '/dev/mst/mt54002_pciconf0'  # TODO update
        self.category_list = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
        self.category_disk_interval_default = '30'
        self.system_profile_default_values = ['enabled', '2048', 'disabled', 'disabled', '1']
        self.switch_type = "ib"

        self.category_default_disabled_dict = {
            StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
            StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
            StatsConsts.STATE: StatsConsts.State.DISABLED.value
        }
        self.category_default_dict = {
            StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
            StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
            StatsConsts.STATE: StatsConsts.STATE_DEFAULT
        }
        self.category_disk_default_dict = {
            StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
            StatsConsts.INTERVAL: self.category_disk_interval_default,
            StatsConsts.STATE: StatsConsts.STATE_DEFAULT
        }
        self.category_disk_default_disable_dict = {
            StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
            StatsConsts.INTERVAL: self.category_disk_interval_default,
            StatsConsts.STATE: StatsConsts.State.DISABLED.value
        }
        self.category_disabled_dict = {
            self.category_list[0]: self.category_default_disabled_dict,
            self.category_list[1]: self.category_default_disabled_dict,
            self.category_list[2]: self.category_disk_default_disable_dict,
            self.category_list[3]: self.category_default_disabled_dict,
            self.category_list[4]: self.category_default_disabled_dict,
            self.category_list[5]: self.category_default_disabled_dict,
            self.category_list[6]: self.category_default_disabled_dict
        }
        self.category_list_default_dict = {
            self.category_list[0]: self.category_default_dict,
            self.category_list[1]: self.category_default_dict,
            self.category_list[2]: self.category_disk_default_dict,
            self.category_list[3]: self.category_default_dict,
            self.category_list[4]: self.category_default_dict,
            self.category_list[5]: self.category_default_dict,
            self.category_list[6]: self.category_default_dict
        }

        self.plane_port_list = ['pl1', 'pl2']
        self.default_aggregated_port = 'sw32p1'
        self.default_loopback_ports = ['sw31p1', 'sw31p2']
        self.loop_back_to_ports = {
            'sw31p1': 'sw32p1pl1',
            'sw31p2': 'sw32p1pl2'
        }
        self.aggregated_port_list = ['sw1p1', 'sw2p1', 'sw32p1']  # total 3 ports
        self.fnm_port_list = ['fnm1']
        self.aggregated_split_port_list = ['sw10p1']
        self.fnm_internal_port_list = ['fnma1p236']
        self.fnm_external_port_list = ['fnm1']
        self.fnm_external_child_port = 'fnm1s1'
        self.child_aggregated_port = 'sw10p1s1'
        self.aggregated_port_planarized_ports = 4
        self.fnm_plane_port_list = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
        self.network_ports = ['eth0', 'ib0', 'lo']  # total 3 ports
        self.non_aggregated_port_list = ['sw10p1', 'sw10p2', 'sw11p1', 'sw11p2', 'sw12p1', 'sw12p2', 'sw13p1', 'sw13p2',
                                         'sw14p1', 'sw14p2', 'sw15p1', 'sw15p2', 'sw16p1', 'sw16p2', 'sw17p1', 'sw17p2',
                                         'sw18p1', 'sw18p2', 'sw19p1', 'sw19p2', 'sw20p1', 'sw20p2', 'sw21p1', 'sw21p2',
                                         'sw22p1', 'sw22p2', 'sw23p1', 'sw23p2', 'sw24p1', 'sw24p2', 'sw25p1', 'sw25p2',
                                         'sw26p1', 'sw26p2', 'sw27p1', 'sw27p2', 'sw28p1', 'sw28p2', 'sw29p1', 'sw29p2',
                                         'sw30p1', 'sw3p1', 'sw3p2', 'sw4p1', 'sw4p2', 'sw5p1', 'sw5p2', 'sw6p1',
                                         'sw6p2',
                                         'sw7p1', 'sw7p2', 'sw8p1', 'sw8p2', 'sw9p1', 'sw9p2']  # total 55 ports
        self.all_plane_port_list = ['sw1p1pl1', 'sw1p1pl2', 'sw2p1pl1', 'sw2p1pl2', 'sw32p1pl1', 'sw32p1pl2']
        self.all_port_list = self.non_aggregated_port_list + self.aggregated_port_list + self.fnm_external_port_list
        self.all_port_list += self.fnm_external_port_list + self.network_ports
        self.fnm_link_speed = '400G'
        # TODO, ADD MORE PORTS, WE WANT IT TO BE MORE REALISTIC. MAYBE WE CAN USE THE FULL LIST OF ALL PORTS FOR NVL5
        self.fnm_port_type = 'fnm'
        self.all_fae_port_list = self.all_port_list + self.all_plane_port_list + self.fnm_plane_port_list
        self.asic0 = 'asic0'
        self.asic1 = 'asic1'
        self.counters_db_name = 'COUNTERS_DB'
        self.object_numbers = {  # TBD - update values
            'sw1p1': {
                'plane1': 'COUNTERS:oid:0x100000000001f',
                'plane2': 'COUNTERS:oid:0x100000000001f'
            },
            'sw2p1': {
                'plane1': 'COUNTERS:oid:0x100000000001f',
                'plane2': 'COUNTERS:oid:0x100000000001f'
            },
            'sw32p1': {
                'plane1': 'COUNTERS:oid:0x100000000001f',
                'plane2': 'COUNTERS:oid:0x100000000001f'
            }
        }

        self.voltage_sensors = ["PMIC-1-12V-ASIC-VCORE-In-1", "PMIC-1-ASIC-VCORE-Out-1", "PMIC-2-12V-ASIC-HVDD-DVDD-In-1",
                                "PMIC-2-ASIC-DVDD-WEST-Out-2", "PMIC-2-ASIC-HVDD-WEST-Out-1", "PMIC-3-12V-ASIC-HVDD-DVDD-In-1",
                                "PMIC-3-ASIC-DVDD-EAST-Out-2", "PMIC-3-ASIC-HVDD-EAST-Out-1", "PMIC-4-3.3V-OSFP-P01-P08-Out-1",
                                "PMIC-4-3.3V-OSFP-P09-P16-Out-2", "PMIC-4-12V-PORTS-WEST-In-1", "PMIC-5-3.3V-OSFP-P17-P24-Out-1",
                                "PMIC-5-3.3V-OSFP-P25-P32-Out-2", "PMIC-5-12V-PORTS-EAST-In-1", "PMIC-6-13V5-COMEX-VDD-In-1",
                                "PMIC-6-COMEX-VCCSA-Out-2", "PMIC-6-COMEX-VCORE-Out-1", "PSU-1-12V-Out", "PSU-2-12V-Out"]

        self.device_list = [IbConsts.DEVICE_ASIC_PREFIX + str(index) for index in range(1, self.asic_amount + 1)]
        self.device_list.append(IbConsts.DEVICE_SYSTEM)

        dump_files_to_replace_for_each_asic = ['docker.swss-ibv0{}.log', 'saidump{}']
        dump_files_to_add_for_each_asic = ['APPL_DB.json.{}', 'ASIC_DB.json.{}', 'CONFIG_DB.json.{}',
                                           'STATE_DB.json.{}', 'FLEX_COUNTER_DB.json.{}', 'COUNTERS_DB.json.{}',
                                           'COUNTERS_DB_1.json.{}', 'COUNTERS_DB_2.json.{}']

        for dump_file in dump_files_to_replace_for_each_asic:
            self.constants.dump_files.remove(dump_file.format(''))
            for asic_num in range(0, self.asic_amount):
                self.constants.dump_files.append(dump_file.format(asic_num))

        for dump_file in dump_files_to_add_for_each_asic:
            for asic_num in range(0, self.asic_amount):
                self.constants.dump_files.append(dump_file.format(asic_num))

        self.pre_login_message = "NVOS switch"
        self.post_login_message = "\n \u2588\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2557   " \
                                  "\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 " \
                                  "\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\n \u2588\u2588\u2588\u2588" \
                                  "\u2557  \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588" \
                                  "\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550" \
                                  "\u2550\u2550\u255d\n \u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588" \
                                  "\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551   " \
                                  "\u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\n " \
                                  "\u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u255a\u2588" \
                                  "\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2551   \u2588\u2588\u2551" \
                                  "\u255a\u2550\u2550\u2550\u2550\u2588\u2588\u2551\n \u2588\u2588\u2551 \u255a" \
                                  "\u2588\u2588\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2554\u255d " \
                                  "\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588" \
                                  "\u2588\u2588\u2588\u2588\u2551\n \u255a\u2550\u255d  \u255a\u2550\u2550" \
                                  "\u2550\u255d  \u255a\u2550\u2550\u2550\u255d   \u255a\u2550\u2550\u2550" \
                                  "\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\n"
        self.ssd_image = {
            'StorFly VSFBM4XC016G-MLX2': ('0202-002', '/auto/sw_system_project/NVOS_INFRA/verification_files/ssd_fw/virtium_ssd_fw_pkg.pkg'),
        }

    def get_ib_ports_num(self):
        return self.ib_ports_num

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp", "SODIMM-1-Temp"]

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.voltage_sensors,
                             "TEMPERATURE": self.temperature_sensors}

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        DutUtilsTool.check_ssh_for_authentication_error(engine, self)
        return DutUtilsTool.wait_for_nvos_to_become_functional(engine)

    def reload_device(self, engine, cmd_list, validate=False):
        engine.send_config_set(cmd_list, exit_config_mode=False, cmd_verify=False)


# -------------------------- Gorilla Switch ----------------------------
class GorillaSwitch(IbSwitch):

    def __init__(self, asic_amount=1):
        super().__init__(asic_amount=asic_amount)

    def _init_constants(self):
        IbSwitch._init_constants(self)
        self.core_count = 4
        self.asic_type = NvosConst.QTM2
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format(
            "x86_64-mlnx_mqm9700-r0")

        self.show_platform_output.update({
            "product-name": "MQM9700",
            "asic-model": self.asic_type,
        })
        self.current_bios_version_name = "0ACQF_06.01.003"
        self.current_bios_version_path = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x03/Release/0ACQF.cab"
        self.previous_bios_version_name = "0ACQF_06.01.002"
        self.previous_bios_version_path = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x02/Release/0ACQF.cab"
        self.current_cpld_version = BaseSwitch.CpldImageConsts(
            burn_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/FUI000258_BURN_Gorilla_MNG_CPLD000232_REV0700_CPLD000324_REV0300_CPLD000268_REV0700_IPN.vme",
            refresh_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/FUI000258_REFRESH_Gorilla_MNG_CPLD000232_REV0700_CPLD000324_REV0300_CPLD000268_REV0700.vme",
            version_names={
                "CPLD1": "CPLD000232_REV0700",
                "CPLD2": "CPLD000324_REV0300",
                "CPLD3": "CPLD000268_REV0700",
            }
        )
        self.previous_cpld_version = BaseSwitch.CpldImageConsts(
            burn_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/OLD/FUI000188_BURN_Gorilla_MNG_CPLD000324_REV0100_CPLD000268_REV0500_CPLD000232_REV0600_IPN.vme",
            refresh_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/OLD/FUI000188_REFRESH_Gorilla_MNG_CPLD000324_REV0100_CPLD000268_REV0500_CPLD000232_REV0600.vme",
            version_names={
                "CPLD1": "CPLD000232_REV0600",
                "CPLD2": "CPLD000324_REV0100",
                "CPLD3": "CPLD000268_REV0500",
            }
        )
        self.stats_fan_header_num_of_lines = 25
        self.stats_power_header_num_of_lines = 13
        self.stats_temperature_header_num_of_lines = 53
        self.supported_tpm_attestation_algos = [TpmConsts.SHA256]

    def _init_fan_list(self):
        super()._init_fan_list()
        self.fan_list += ["FAN7/1", "FAN7/2"]
        self.fan_led_list.append('FAN7')

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]

    def _init_platform_lists(self):
        super()._init_platform_lists()
        self.platform_environment_fan_values = {
            "state": FansConsts.STATE_OK, "direction": None, "current-speed": None,
            "min-speed": ExpectedString(range_min=2000, range_max=10000),
            "max-speed": ExpectedString(range_min=20000, range_max=40000)}
        self.platform_inventory_switch_values.update({"hardware-version": None,
                                                      "model": ExpectedString(regex="MQM9700.*")})


# -------------------------- Gorilla BF3 Switch ----------------------------
class GorillaSwitchBF3(GorillaSwitch):

    def __init__(self):
        super().__init__(asic_amount=1)

    def _init_constants(self):
        super()._init_constants()
        self.constants.firmware.remove(PlatformConsts.FW_BIOS)
        self.ib_ports_num = 64
        self.core_count = 16
        self.asic_type = NvosConst.QTM2

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["xSFP-module-26-Temp", "xSFP-module-29-Temp"]


# -------------------------- BlackMamba Switch ----------------------------
class BlackMambaSwitch(IbSwitch):

    def __init__(self):
        super().__init__(asic_amount=4)

    def _init_constants(self):
        self.asic_amount = 4
        super()._init_constants()
        self.ib_ports_num = 64
        self.core_count = 4
        self.asic_type = NvosConst.QTM3
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH. \
            format("x86_64-mlnx_qm8790-r0")

        self.voltage_sensors = ["PMIC-1+12V_VDD_ASIC1+Vol+In+1", "PMIC-1+ASIC1_VDD+Vol+Out+1",
                                "PMIC-2+12V_HVDD_DVDD_ASIC1+Vol+In+1", "PMIC-2+ASIC1_DVDD_PL0+Vol+Out+2",
                                "PMIC-2+ASIC1_HVDD_PL0+Vol+Out+1", "PMIC-3+12V_HVDD_DVDD_ASIC1+Vol+In+1",
                                "PMIC-3+ASIC1_DVDD_PL1+Vol+Out+2", "PMIC-3+ASIC1_HVDD_PL1+Vol+Out+1",
                                "PMIC-4+12V_VDD_ASIC2+Vol+In+1", "PMIC-4+ASIC2_VDD+Vol+Out+1",
                                "PMIC-5+12V_HVDD_DVDD_ASIC2+Vol+In+1", "PMIC-5+ASIC2_DVDD_PL0+Vol+Out+2",
                                "PMIC-5+ASIC2_HVDD_PL0+Vol+Out+1", "PMIC-6+12V_HVDD_DVDD_ASIC2+Vol+In+1",
                                "PMIC-6+ASIC2_DVDD_PL1+Vol+Out+2", "PMIC-6+ASIC2_HVDD_PL1+Vol+Out+1",
                                "PMIC-7+12V_VDD_ASIC3+Vol+In+1", "PMIC-7+ASIC3_VDD+Vol+Out+1",
                                "PMIC-8+12V_HVDD_DVDD_ASIC3+Vol+In+1", "PMIC-8+ASIC3_DVDD_PL0+Vol+Out+2",
                                "PMIC-8+ASIC3_HVDD_PL0+Vol+Out+1", "PMIC-9+12V_HVDD_DVDD_ASIC3+Vol+In+1",
                                "PMIC-9+ASIC3_DVDD_PL1+Vol+Out+2", "PMIC-9+ASIC3_HVDD_PL1+Vol+Out+1",
                                "PMIC-10+12V_VDD_ASIC4+Vol+In+1", "PMIC-10+ASIC4_VDD+Vol+Out+1",
                                "PMIC-11+12V_HVDD_DVDD_ASIC4+Vol+In+1", "PMIC-11+ASIC4_DVDD_PL0+Vol+Out+2",
                                "PMIC-11+ASIC4_HVDD_PL0+Vol+Out+1", "PMIC-12+12V_HVDD_DVDD_ASIC4+Vol+In+1",
                                "PMIC-12+ASIC4_DVDD_PL1+Vol+Out+2", "PMIC-12+ASIC4_HVDD_PL1+Vol+Out+1",
                                "PMIC-13+12V_MAIN+Vol+In+1", "PMIC-13+CEX_VDD+Vol+Out+1", "PSU-1+12V+Vol+Out",
                                "PSU-2+12V+Vol+Out", "PSU-3+12V+Vol+Out", "PSU-4+12V+Vol+Out", "PSU-5+12V+Vol+Out",
                                "PSU-6+12V+Vol+Out", "PSU-7+12V+Vol+Out", "PSU-8+12V+Vol+Out"]

    def _init_fan_list(self):
        super()._init_fan_list()
        self.fan_list += ["FAN7/1", "FAN7/2", "FAN8/1", "FAN8/2", "FAN9/1", "FAN9/2", "FAN10/1", "FAN10/2"]
        self.fan_led_list += ['FAN7', 'FAN8', 'FAN9', 'FAN10']

    def _init_psu_list(self):
        super()._init_psu_list()
        self.psu_list += ["PSU3", "PSU4", "PSU5", "PSU6", "PSU7", "PSU8"]
        self.psu_fan_list += ["PSU3/FAN", "PSU4/FAN", "PSU5/FAN", "PSU6/FAN", "PSU7/FAN", "PSU8/FAN"]

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["ASIC2", "ASIC3", "ASIC4", "PSU-7-Temp", "SODIMM-2-Temp"]
        self.temperature_sensors.remove("PSU-1-Temp")


# -------------------------- Crocodile Switch ----------------------------
class CrocodileSwitch(IbSwitch):

    def __init__(self):
        super().__init__(asic_amount=2)

    def _init_constants(self):
        super()._init_constants()
        self.ib_ports_num = 64
        self.core_count = 4
        self.asic_type = NvosConst.QTM3
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH. \
            format("x86_64-nvidia_qm3400-r0")

    def _init_fan_list(self):
        super()._init_fan_list()
        self.fan_list.remove("FAN6/1")
        self.fan_list.remove("FAN6/2")
        self.fan_led_list.remove('FAN6')

    def _init_psu_list(self):
        super()._init_psu_list()
        self.psu_list += ["PSU3", "PSU4"]
        self.psu_fan_list += ["PSU3/FAN", "PSU4/FAN"]

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors += ["PSU-3-Temp", "PSU-4-Temp"]
        self.temperature_sensors.remove("ASIC")


# -------------------------- Crocodile Simx Switch ----------------------------
class CrocodileSimxSwitch(IbSwitch):

    def __init__(self):
        super().__init__(asic_amount=1)


# -------------------------- NvLink Switch ----------------------------
class NvLinkSwitch(IbSwitch):

    def __init__(self, asic_amount):
        super().__init__(asic_amount)

    def _init_constants(self):
        super()._init_constants()
        self.ib_ports_num = 64
        self.core_count = 4
        self.asic_type = NvosConst.QTM3
        # self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format(
        #     "x86_64-mlnx_mqm9700-r0")
        self.switch_type = "nvl"


# -------------------------- Juliet Switch ----------------------------
class JulietSwitch(NvLinkSwitch):

    def __init__(self, asic_amount):
        super().__init__(asic_amount=asic_amount)

    def _init_constants(self):
        super()._init_constants()


# -------------------------- JulietScaleout Switch ----------------------------
class JulietScaleoutSwitch(JulietSwitch):

    def __init__(self):
        super().__init__(asic_amount=2)

    def _init_constants(self):
        super()._init_constants()
        firmware = [PlatformConsts.FW_ASIC, PlatformConsts.FW_BIOS, PlatformConsts.FW_SSD,
                    PlatformConsts.FW_CPLD + '1', PlatformConsts.FW_CPLD + '2', PlatformConsts.FW_CPLD + '3',
                    PlatformConsts.FW_FPGA, PlatformConsts.FW_BMC]
        self.constants.firmware = firmware

        self.voltage_sensors = [
            "PMIC-1-12V-VDD-ASIC1-In-1",
            "PMIC-1-ASIC1-VDD-Out-1",
            "PMIC-2-12V-HVDD-DVDD-ASIC1-In-1",
            "PMIC-2-ASIC1-DVDD-PL0-Out-2",
            "PMIC-2-ASIC1-HVDD-PL0-Out-1",
            "PMIC-3-12V-HVDD-DVDD-ASIC1-In-1",
            "PMIC-3-ASIC1-DVDD-PL1-Out-2",
            "PMIC-3-ASIC1-HVDD-PL1-Out-1",
            "PMIC-4-12V-VDD-ASIC2-In-1",
            "PMIC-4-ASIC2-VDD-Out-1",
            "PMIC-5-12V-HVDD-DVDD-ASIC2-In-1",
            "PMIC-5-ASIC2-DVDD-PL0-Out-2",
            "PMIC-5-ASIC2-HVDD-PL0-Out-1",
            "PMIC-6-12V-HVDD-DVDD-ASIC2-In-1",
            "PMIC-6-ASIC2-DVDD-PL1-Out-2",
            "PMIC-6-ASIC2-HVDD-PL1-Out-1"
        ]
        # TBD
        # self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format(
        #     "x86_64-mlnx_mqm9700-r0")
        # self.show_platform_output.update({
        #     "product-name": "MQM9700",
        #     "asic-model": self.asic_type,
        # })

        # TODO - Check if it needs to be changed.
        # self.current_bios_version_name = "0ACQF_06.01.003"
        # self.current_bios_version_path = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x03/Release/0ACQF.cab"
        # self.previous_bios_version_name = "0ACQF_06.01.002"
        # self.previous_bios_version_path = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x02/Release/0ACQF.cab"
        # self.current_cpld_version = BaseSwitch.CpldImageConsts(
        #     burn_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/FUI000258_BURN_Gorilla_MNG_CPLD000232_REV0700_CPLD000324_REV0300_CPLD000268_REV0700_IPN.vme",
        #     refresh_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/FUI000258_REFRESH_Gorilla_MNG_CPLD000232_REV0700_CPLD000324_REV0300_CPLD000268_REV0700.vme",
        #     version_names={
        #         "CPLD1": "CPLD000232_REV0700",
        #         "CPLD2": "CPLD000324_REV0300",
        #         "CPLD3": "CPLD000268_REV0700",
        #     }
        # )
        # self.previous_cpld_version = BaseSwitch.CpldImageConsts(
        #     burn_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/OLD/FUI000188_BURN_Gorilla_MNG_CPLD000324_REV0100_CPLD000268_REV0500_CPLD000232_REV0600_IPN.vme",
        #     refresh_image_path="/auto/sw_system_project/NVOS_INFRA/verification_files/cpld_fw/OLD/FUI000188_REFRESH_Gorilla_MNG_CPLD000324_REV0100_CPLD000268_REV0500_CPLD000232_REV0600.vme",
        #     version_names={
        #         "CPLD1": "CPLD000232_REV0600",
        #         "CPLD2": "CPLD000324_REV0100",
        #         "CPLD3": "CPLD000268_REV0500",
        #     }
        # )
        # self.stats_fan_header_num_of_lines = 25
        # self.stats_power_header_num_of_lines = 13
        # self.stats_temperature_header_num_of_lines = 53
        self.supported_tpm_attestation_algos = [TpmConsts.SHA256]
        self.nvl5_access_ports_list = ['access1p1', 'access1p2', 'access1p3', 'access1p4', 'access1p5', 'access1p6',
                                       'access1p7', 'access1p8',
                                       'access1p9', 'access1p10', 'access1p11', 'access1p12', 'access1p13', 'access1p14',
                                       'access1p15', 'access1p16', 'access1p17', 'access1p18', 'access1p19', 'access1p20',
                                       'access1p21', 'access1p22', 'access1p23', 'access1p24', 'access1p25', 'access1p26',
                                       'access1p27', 'access1p28', 'access1p29', 'access1p30', 'access1p31', 'access1p32',
                                       'access1p33', 'access1p34', 'access1p35', 'access1p36']

        self.nvl5_trunk_ports_list = ['sw1p1s1', 'sw1p1s2', 'sw1p2s1', 'sw1p2s2',
                                      'sw2p1s1', 'sw2p1s2', 'sw2p2s1', 'sw2p2s2',
                                      'sw3p1s1', 'sw3p1s2', 'sw3p2s1', 'sw3p2s2',
                                      'sw4p1s1', 'sw4p1s2', 'sw4p2s1', 'sw4p2s2',
                                      'sw5p1s1', 'sw5p1s2', 'sw5p2s1', 'sw5p2s2',
                                      'sw6p1s1', 'sw6p1s2', 'sw6p2s1', 'sw6p2s2',
                                      'sw7p1s1', 'sw7p1s2', 'sw7p2s1', 'sw7p2s2',
                                      'sw8p1s1', 'sw8p1s2', 'sw8p2s1', 'sw8p2s2',
                                      'sw9p1s1', 'sw9p1s2', 'sw9p2s1', 'sw9p2s2',
                                      'sw10p1s1', 'sw10p1s2', 'sw10p2s1', 'sw10p2s2',
                                      'sw11p1s1', 'sw11p1s2', 'sw11p2s1', 'sw11p2s2',
                                      'sw12p1s1', 'sw12p1s2', 'sw12p2s1', 'sw12p2s2',
                                      'sw13p1s1', 'sw13p1s2', 'sw13p2s1', 'sw13p2s2',
                                      'sw14p1s1', 'sw14p1s2', 'sw14p2s1', 'sw14p2s2',
                                      'sw15p1s1', 'sw15p1s2', 'sw15p2s1', 'sw15p2s2',
                                      'sw16p1s1', 'sw16p1s2', 'sw16p2s1', 'sw16p2s2',
                                      'sw17p1s1', 'sw17p1s2', 'sw17p2s1', 'sw17p2s2',
                                      'sw18p1s1', 'sw18p1s2', 'sw18p2s1', 'sw18p2s2'
                                      ]
        self.network_ports = ['eth0', 'eth1', 'lo']
        self.all_nvl5_ports_list = self.nvl5_access_ports_list + self.nvl5_trunk_ports_list + self.network_ports
        self.nvl5_fnm_ports = ['fnma1p1', 'fnma1p2', 'fnma2p1', 'fnma2p2']
        self.all_fae_nvl5_ports_list = self.all_nvl5_ports_list + self.nvl5_fnm_ports
        self.nvl5_port = ['access1p48']
        self.nvl5_port_speed = '400G'
        self.nvl5_port_type = 'nvl'
        # will be updated

    def _init_temperature(self):
        super()._init_temperature()
        self.temperature_sensors = ["ASIC", "Ambient-Port-Side-Temp",
                                    "CPU-Core-0-Temp", "CPU-Core-1-Temp", "CPU-Core-2-Temp", "CPU-Core-3-Temp",
                                    "swb_asic1", "swb_asic2", "SODIMM-1-Temp"]

    def _init_fan_list(self):
        super()._init_fan_list()
        self.fan_led_list = []


# -------------------------- Caiman Switch ----------------------------
class CaimanSwitch(NvLinkSwitch):

    def __init__(self):
        super().__init__(asic_amount=4)

    def _init_constants(self):
        super()._init_constants()
        self.ib_ports_num = 64
        self.core_count = 4
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format(
            "x86_64-mlnx_mqm9700-r0")


# -------------------------- Marlin Switch ----------------------------
class MarlinSwitch(IbSwitch):

    def __init__(self):
        super().__init__(asic_amount=2)

    def _init_constants(self):
        super()._init_constants()
        self.ib_ports_num = 128
        self.core_count = 4
        self.asic_type = NvosConst.QTM2
        self.primary_asic = f"{IbConsts.DEVICE_ASIC_PREFIX}2"
        self.primary_swid = f"{IbConsts.SWID}1"
        self.primary_ipoib_interface = IbConsts.IPOIB_INT1
        self.secondary_ipoib_interface = IbConsts.IPOIB_INT0
        self.multi_asic_system = True
        del self.show_platform_output['manufacturer']

    def _init_available_databases(self):
        super()._init_available_databases()
        self.available_tables_per_asic[DatabaseConst.APPL_DB_ID] = {"ALIAS_PORT_MAP": self.get_ib_ports_num() / 2}
        self.available_tables.update({'database0': self.available_tables_per_asic,
                                      'database1': self.available_tables_per_asic})
