import logging
from collections import namedtuple
from abc import abstractmethod, ABCMeta, ABC
from ngts.nvos_constants.constants_nvos import NvosConst, DatabaseConst
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.DatabaseTool import DatabaseTool
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts, PlatformConsts
import time

logger = logging.getLogger()


# -------------------------- Base Device ----------------------------
class BaseDevice(ABC):

    def __init__(self):
        self.default_password = ""
        self.default_username = ""
        self.prev_default_password = ""
        self.open_api_port = ""
        self.available_databases = {}
        self.available_tables = {}
        self.available_services = []
        self.available_dockers = []
        self.dependent_dockers = []
        self.dependent_services = []
        self.constants = None
        self.fan_list = []
        self.psu_list = []
        self.psu_fan_list = []
        self.fan_led_list = []
        self.fan_direction_dir = ""
        self.temperature_list = []
        self.health_components = []
        self.platform_hw_list = []
        self.platform_list = []
        self.system_list = []
        self.platform_environment_list = []
        self.platform_env_psu_prop = []
        self.hw_comp_prop = []
        self.pre_login_message = ""
        self.post_login_message = ""
        self.asic_amount = 1
        self.core_count = 1
        self.asic_type = ""
        self.voltage_sensors = []
        self.temperature_sensors = []
        self.available_tables_per_asic = {}
        self.ib_ports_num = 0
        self.user_fields = []
        self.install_from_onie_timeout = 360  # seconds
        self.install_success_patterns = ""
        self.mst_dev_name = ""

        self._init_constants()
        self._init_available_databases()
        self._init_services()
        self._init_dependent_services()
        self._init_dockers()
        self._init_fan_list()
        self._init_psu_list()
        self._init_fan_direction_dir()
        self._init_temperature()
        self._init_health_components()
        self._init_platform_lists()
        self._init_system_lists()
        self._init_sensors_dict()

    @abstractmethod
    def _init_available_databases(self):
        pass

    @abstractmethod
    def _init_services(self):
        pass

    @abstractmethod
    def _init_dependent_services(self):
        pass

    @abstractmethod
    def _init_dockers(self):
        pass

    @abstractmethod
    def _init_constants(self):
        pass

    @abstractmethod
    def _init_fan_list(self):
        pass

    @abstractmethod
    def _init_sensors_dict(self):
        pass

    @abstractmethod
    def _init_psu_list(self):
        pass

    @abstractmethod
    def _init_fan_direction_dir(self):
        pass

    @abstractmethod
    def _init_temperature(self):
        pass

    @abstractmethod
    def _init_health_components(self):
        pass

    @abstractmethod
    def _init_platform_lists(self):
        pass

    @abstractmethod
    def _init_system_lists(self):
        pass

    @abstractmethod
    def get_ib_ports_num(self):
        pass

    def verify_databases(self, dut_engine):
        """
        validate the redis includes all expected tables
        :param dut_engine: ssh dut engine
        Return result_obj with True result if all tables exists, False and a relevant info if one or more tables are missing
        """
        time.sleep(10)
        result_obj = ResultObj(True, "")
        for db_name, db_id in self.available_databases.items():
            if db_name == DatabaseConst.STATE_DB_NAME:
                continue

            for database_docker in self.available_tables.keys():
                table_info = self.available_tables[database_docker][db_id]
                for table_name, expected_entries in table_info.items():
                    output = self.get_all_table_names_in_database(dut_engine, db_name, table_name,
                                                                  database_docker=database_docker).returned_value
                    if len(output) < expected_entries:
                        result_obj.result = False
                        result_obj.info += "Database docker: {database_docker} DB: {db_name}, Table: {table_name}. Table count mismatch, Expected: {expected} != Actual {actual}\n" \
                            .format(database_docker=database_docker, db_name=db_name, table_name=table_name,
                                    expected=str(expected_entries),
                                    actual=str(len(output)))

        return result_obj

    def verify_dockers(self, dut_engine, dockers_list=""):
        """
        Validate existing dockers
        """
        result_obj = ResultObj(True, "")
        cmd_output = dut_engine.run_cmd('docker ps --format \"table {{.Names}}\"')
        list_of_dockers = dockers_list if dockers_list else self.available_dockers
        for docker in list_of_dockers:
            if docker not in cmd_output:
                result_obj.result = False
                result_obj.info += "{} docker is not active.\n".format(docker)

        return result_obj

    def verify_services(self, dut_engine):
        """
        Validate expected dockers
        """
        result_obj = ResultObj(True, "")
        for service in self.available_services:
            cmd_output = dut_engine.run_cmd('systemctl --type=service | grep {}'.format(service))
            if NvosConst.SERVICE_STATUS_ACTIVE not in cmd_output:
                result_obj.result = False
                result_obj.info += "{} service is not active. {} \n".format(service, cmd_output)

        temp_res = self.verify_nvue_service(dut_engine)
        if not temp_res.result:
            result_obj.result = False
            result_obj.info += temp_res.info

        return result_obj

    def verify_nvue_service(self, dut_engine):
        logging.info("Verify nvued service is active")
        nvued_cmd_output = dut_engine.run_cmd("sudo systemctl status nvued")
        if NvosConst.SERVICE_STATUS_ACTIVE not in nvued_cmd_output:
            return ResultObj(False, "nvued service is not active. info: {}".format(nvued_cmd_output))
        return ResultObj(True)

    def get_database_id(self, db_name):
        return self.available_databases[db_name]

    def get_all_table_names_in_database(self, engine, database_name, table_name_substring='.', database_docker=None):
        """
        :param engine: dut engine
        :param database_name: database name
        :param table_name_substring: full or partial table name
        :return: any database table that includes the substring, if table_name_substring is none we will return all the tables
        """
        result_obj = ResultObj(True, "")
        # docker_exec_cmd = 'docker exec -it {database_docker} '.format(database_docker=database_docker) if database_docker else ''
        output = DatabaseTool.sonic_db_run_get_keys_in_docker(
            docker_name=database_docker if database_docker else '', engine=engine, asic="",
            db_name=DatabaseConst.REDIS_DB_NUM_TO_NAME[self.get_database_id(database_name)],
            grep_str=table_name_substring)

        # cmd = docker_exec_cmd + "redis-cli -n {database_name} keys * | grep {prefix}".format(
        #    database_name=self.get_database_id(database_name), prefix=table_name_substring)
        # output = engine.run_cmd(cmd)
        result_obj.returned_value = output.splitlines()
        return result_obj

    @abstractmethod
    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        raise Exception(f"Not implemented for this switch {self.__class__.__name__}")

    @abstractmethod
    def reload_device(self, engine, cmd_list, validate=False):
        raise Exception(f"Not implemented for this switch {self.__class__.__name__}")


# -------------------------- Base Appliance ----------------------------
class BaseAppliance(BaseDevice):
    def __init__(self):
        BaseDevice.__init__(self)

    @abstractmethod
    def eth_ports_num(self):
        pass


# -------------------------- Base Switch ----------------------------
class BaseSwitch(BaseDevice):
    __metaclass__ = ABCMeta

    CpldImageConsts = namedtuple('CpldImageConsts', ('burn_image_path', 'refresh_image_path', 'version_names'))

    def __init__(self):
        super().__init__()

    def _init_available_databases(self):
        BaseDevice._init_available_databases(self)
        self.available_databases.update(
            {DatabaseConst.APPL_DB_NAME: DatabaseConst.APPL_DB_ID,
             DatabaseConst.ASIC_DB_NAME: DatabaseConst.ASIC_DB_ID,
             # DatabaseConst.COUNTERS_DB_NAME: DatabaseConst.COUNTERS_DB_ID, - disabled for now
             DatabaseConst.CONFIG_DB_NAME: DatabaseConst.CONFIG_DB_ID,
             DatabaseConst.STATE_DB_NAME: DatabaseConst.STATE_DB_ID
             })

        self.available_tables.update(
            {
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
            })

    def _init_services(self):
        BaseDevice._init_services(self)
        self.available_services.extend((
            'docker.service', 'database.service', 'hw-management.service', 'config-setup.service',
            'updategraph.service', 'ntp.service', 'hostname-config.service', 'ntp-config.service',
            'rsyslog-config.service', 'procdockerstatsd.service'))

    def _init_dependent_services(self):
        BaseDevice._init_dependent_services(self)

    def get_ib_ports_num(self):
        return self.ib_ports_num

    def _init_dockers(self):
        BaseDevice._init_dockers(self)
        self.available_dockers.extend(('database', 'ib-utils', 'gnmi-server'))

    def _init_constants(self):
        BaseDevice._init_constants(self)
        Constants = namedtuple('Constants', ['system', 'dump_files', 'sdk_dump_files', 'firmware'])
        system_dic = {
            'system': [SystemConsts.BUILD, SystemConsts.HOSTNAME, SystemConsts.PLATFORM, SystemConsts.PRODUCT_NAME,
                       SystemConsts.PRODUCT_RELEASE, SystemConsts.SWAP_MEMORY, SystemConsts.SYSTEM_MEMORY,
                       SystemConsts.UPTIME, SystemConsts.TIMEZONE, SystemConsts.HEALTH_STATUS, SystemConsts.DATE_TIME,
                       SystemConsts.STATUS],
            'message': [SystemConsts.PRE_LOGIN_MESSAGE, SystemConsts.POST_LOGIN_MESSAGE],
            'reboot': [SystemConsts.REBOOT_REASON],
            'version': [SystemConsts.VERSION_BUILD_DATE, SystemConsts.VERSION_IMAGE, SystemConsts.VERSION_KERNEL]
        }
        dump_files = ['APPL_DB.json', 'ASIC_DB.json', 'boot.conf', 'bridge.fdb', 'bridge.vlan', 'CONFIG_DB.json',
                      'COUNTERS_DB_1.json', 'COUNTERS_DB_2.json', 'COUNTERS_DB.json', 'date.counter_1',
                      'date.counter_2', 'df', 'dmesg', 'docker.pmon', 'docker.ps', 'docker.stats',
                      'docker.swss-ibv0.log', 'dpkg', 'fan', 'FLEX_COUNTER_DB.json', 'free', 'hdparm', 'ib-utils.dump',
                      'ifconfig.counters_1', 'ifconfig.counters_2', 'interface.status', 'interface.xcvrs.eeprom',
                      'interface.xcvrs.presence', 'ip.addr', 'ip.interface', 'ip.link', 'ip.link.stats', 'ip.neigh',
                      'ip.neigh.noarp', 'ip.route', 'ip.rule', 'lspci', 'lsusb', 'machine.conf', 'mount',
                      'netstat.counters_1', 'netstat.counters_2', 'platform.summary', 'ps.aux', 'ps.extended',
                      'psustatus', 'queue.counters_1', 'queue.counters_2', 'reboot.cause',
                      'saidump', 'sensors', 'services.summary', 'ssdhealth', 'STATE_DB.json', 'swapon', 'sysctl',
                      'syseeprom', 'systemd.analyze.blame', 'systemd.analyze.dump', 'systemd.analyze.plot.svg',
                      'temperature', 'top', 'version', 'vlan.summary', 'vmstat', 'vmstat.m', 'vmstat.s', 'who']
        sdk_dump_files = ["fw_trace_attr.json", "fw_trace_attr.json.gz", "fw_trace_string_db.json",
                          "fw_trace_string_db.json.gz"]
        firmware = [PlatformConsts.FW_BIOS, PlatformConsts.FW_ONIE, PlatformConsts.FW_SSD, PlatformConsts.FW_CPLD + '1',
                    PlatformConsts.FW_CPLD + '2', PlatformConsts.FW_CPLD + '3']
        self.constants = Constants(system_dic, dump_files, sdk_dump_files, firmware)
        self.current_bios_version_name = ""
        self.current_bios_version_path = ""
        self.previous_bios_version_name = ""
        self.previous_bios_version_path = ""
        self.current_cpld_version = None
        self.previous_cpld_version = None

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.psu_fan_list = ["PSU1/FAN", "PSU2/FAN"]
        self.platform_env_psu_prop = ["capacity", "current", "power", "state", "voltage"]

    def _init_temperature(self):
        self.temperature_list = ["ASIC", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp",
                                 "CPU-Core-1-Temp", "CPU-Pack-Temp", "PSU-1-Temp"]

    def _init_health_components(self):
        self.health_components = self.fan_list + self.psu_list + self.psu_fan_list + \
            ["ASIC Temperature", "Containers", "CPU utilization", "Disk check", "Disk space",
             "Disk space log"]

    def _init_platform_lists(self):
        self.platform_hw_list = ["asic-count", "cpu", "cpu-load-averages", "disk-size", "hw-revision", "manufacturer",
                                 "memory", "model", "onie-version", "part-number", "product-name", "serial-number",
                                 "system-mac", "system-uuid"]
        self.platform_list = ["fan", "led", "psu", "temperature", "component", "hardware", "environment"]
        self.platform_environment_list = ["fan", "led", "psu", "temperature"]
        self.fan_prop = ["max-speed", "min-speed", "current-speed", "state"]
        self.hw_comp_list = self.fan_list + self.psu_list + ["SWITCH"]
        self.hw_comp_prop = ["hardware-version", "model", "serial", "state", "type"]

    def _init_fan_direction_dir(self):
        self.fan_direction_dir = "/var/run/hw-management/thermal"
