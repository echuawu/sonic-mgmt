import re
import logging
from collections import namedtuple
from abc import abstractmethod, ABCMeta, ABC
from ngts.nvos_constants.constants_nvos import NvosConst, DatabaseConst, IbConsts, StatsConsts
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.InterfaceConfiguration.Port import Port
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import IbInterfaceConsts
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts, PlatformConsts
import time

logger = logging.getLogger()


class BaseDevice:

    def __init__(self):
        self.available_databases = {}
        self.available_tables = {}
        self.available_services = []
        self.available_dockers = []
        self.dependent_dockers = []
        self.dependent_services = []
        self.constants = None
        self.supported_ib_speeds = {}
        self.invalid_ib_speeds = {}
        self.fan_list = []
        self.psu_list = []
        self.psu_fan_list = []
        self.fan_led_list = []
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

        self._init_available_databases()
        self._init_services()
        self._init_dependent_services()
        self._init_dockers()
        self._init_dependent_dockers()
        self._init_constants()
        self._init_ib_speeds()
        self._init_fan_list()
        self._init_psu_list()
        self._init_temperature()
        self._init_health_components()
        self._init_platform_lists()
        self._init_system_lists()
        self._init_sensors_dict()

    @abstractmethod
    def _init_available_databases(self):
        pass

    @abstractmethod
    def ib_ports_num(self):
        pass

    @abstractmethod
    def _init_services(self):
        pass

    @abstractmethod
    def _init_dependent_services(self):
        pass

    @abstractmethod
    def _init_dependent_dockers(self):
        pass

    @abstractmethod
    def _init_dockers(self):
        pass

    @abstractmethod
    def _init_constants(self):
        pass

    @abstractmethod
    def _init_ib_speeds(self):
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

    def verify_databases(self, dut_engine):
        """
        validate the redis includes all expected tables
        :param dut_engine: ssh dut engine
        Return result_obj with True result if all tables exists, False and a relevant info if one or more tables are missing
        """
        result_obj = ResultObj(True, "")
        for db_name, db_id in self.available_databases.items():
            if db_name == DatabaseConst.STATE_DB_NAME:
                continue

            table_info = self.available_tables[db_id]
            for table_name, expected_entries in table_info.items():
                output = self.get_all_table_names_in_database(dut_engine, db_name, table_name).returned_value
                if len(output) < expected_entries:
                    result_obj.result = False
                    result_obj.info += "DB: {db_name}, Table: {table_name}. Table count mismatch, Expected: {expected} != Actual {actual}\n" \
                        .format(db_name=db_name, table_name=table_name, expected=str(expected_entries),
                                actual=str(len(output)))

        return result_obj

    def verify_ib_ports_state(self, dut_engine, expected_port_state):
        output_dict = OutputParsingTool.parse_json_str_to_dictionary(Port.show_interface(dut_engine, '--applied')).returned_value
        err_msg = ""
        for key, value in output_dict.items():
            if value[IbInterfaceConsts.TYPE] == IbInterfaceConsts.IB_PORT_TYPE and expected_port_state not in value[IbInterfaceConsts.LINK][IbInterfaceConsts.DHCP_STATE].keys():
                err_msg += "{} state is {}".format(key, value[IbInterfaceConsts.LINK][IbInterfaceConsts.DHCP_STATE].keys())

        return ResultObj(False, err_msg) if err_msg else ResultObj(True, "", "")

    def verify_dockers(self, dut_engine, dockers_list=""):
        result_obj = ResultObj(True, "")
        cmd_output = dut_engine.run_cmd('docker ps --format \"table {{.Names}}\"')
        list_of_dockers = dockers_list if dockers_list else self.available_dockers
        for docker in list_of_dockers:
            if docker not in cmd_output:
                result_obj.result = False
                result_obj.info += "{} docker is not active.\n".format(docker)

        return result_obj

    def verify_services(self, dut_engine):
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

    def _verify_value_in_table(self, dut_engine, db_name, table_name_prefix, field_name, expected_value):
        """
        :param db_name: Database name
        :param table_name_prefix: table name
        :param dut_engine: the dut engine
        :param field_name: the field name in the table
        :param expected_value: an expected value for the field
        :return: result_obj
        """
        result_obj = ResultObj(True, "")
        output = self.get_all_table_names_in_database(dut_engine, db_name, table_name_prefix).returned_value
        for table_name in output:
            obj = self.read_from_database(db_name, dut_engine, table_name, field_name)
            if obj.verify_result() != expected_value:
                result_obj.result = False
                logger.error("{field_name} value in {table_name} DB {database_name} is {obj_value} not {expected_value}"
                             " as expected \n".format(field_name=field_name, table_name=table_name,
                                                      database_name=db_name, obj_value=obj.returned_value,
                                                      expected_value=expected_value))
        if not result_obj.result:
            result_obj.info = "one or more fields are not as expected"
        return result_obj

    def read_from_database(self, database_name, engine, table_name, field_name=None):
        """
        Read the value of required field in specified database
        :param engine: dut engine
        :param database_name: the name of the database
        :param table_name: the table name in the given database
        :param field_name: the field name in table
        :return: ResultObj
        """
        result_obj = ResultObj(True, "")
        if database_name not in self.available_databases.keys():
            result_obj.result = False
            result_obj.info += "{database_name} can't be found in Redis".format(database_name=database_name)
            return result_obj

        output = Tools.DatabaseTool.sonic_db_cli_hgetall(engine=engine, asic="", b_name=database_name,
                                                         table_name=table_name)
        # cmd = "redis-cli -n {database_name} hgetall {table_name}".format(
        #    table_name='"' + table_name + '"', database_name=self.get_database_id(database_name))
        # output = engine.run_cmd(cmd)

        output_list = re.findall('"(.*)"\n', output + '\n')
        database_dic = {output_list[i]: output_list[i + 1] for i in range(0, len(output_list), 2)}
        result_obj.returned_value = database_dic[field_name] if field_name else database_dic
        return result_obj

    def get_all_table_names_in_database(self, engine, database_name, table_name_substring='.', database_docker=None):
        """
        :param engine: dut engine
        :param database_name: database name
        :param table_name_substring: full or partial table name
        :return: any database table that includes the substring, if table_name_substring is none we will return all the tables
        """
        result_obj = ResultObj(True, "")
        # docker_exec_cmd = 'docker exec -it {database_docker} '.format(database_docker=database_docker) if database_docker else ''
        output = Tools.DatabaseTool.sonic_db_run_get_keys_in_docker(
            docker_name=database_docker if database_docker else '', engine=engine, asic="",
            db_name=DatabaseConst.REDIS_DB_NUM_TO_NAME[self.get_database_id(database_name)],
            grep_str=table_name_substring)

        # cmd = docker_exec_cmd + "redis-cli -n {database_name} keys * | grep {prefix}".format(
        #    database_name=self.get_database_id(database_name), prefix=table_name_substring)
        # output = engine.run_cmd(cmd)
        result_obj.returned_value = output.splitlines()
        return result_obj


# -------------------------- Base Appliance ----------------------------
class BaseAppliance(BaseDevice):
    def __init__(self):
        BaseDevice.__init__(self)

    @abstractmethod
    def eth_ports_num(self):
        pass


# -------------------------- Base Switch ----------------------------
class BaseSwitch(BaseDevice, ABC):
    __metaclass__ = ABCMeta

    def __init__(self):
        BaseDevice.__init__(self)

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
                    {"ALIAS_PORT_MAP": self.ib_ports_num()},
                DatabaseConst.ASIC_DB_ID:
                    {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() + 1,
                     "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 1,
                     "LANES": 1,
                     "VIDCOUNTER": 1,
                     "RIDTOVID": 1,
                     "HIDDEN": 1,
                     "COLDVIDS": 1},
                DatabaseConst.COUNTERS_DB_ID:
                    {"COUNTERS_PORT_NAME_MAP": 1,
                     "COUNTERS:oid": self.ib_ports_num()},
                DatabaseConst.CONFIG_DB_ID:
                    {"IB_PORT": self.ib_ports_num(),
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
            'rsyslog-config.service', 'procdockerstatsd.service', 'swss-ibv0.service',
            'syncd-ibv0.service', 'pmon.service'))

    def _init_dependent_services(self):
        BaseDevice._init_dependent_services(self)

    def _init_dockers(self):
        BaseDevice._init_dockers(self)
        self.available_dockers.extend(('pmon', 'syncd-ibv0', 'swss-ibv0', 'database', 'ib-utils', 'gnmi-server'))

    def _init_dependent_dockers(self):
        BaseDevice._init_dependent_dockers(self)
        # TODO maybe in the future we will need it again, but for now they removed this dependency
        # self.dependent_dockers.extend([['swss-ibv0', 'syncd-ibv0']])

    def _init_constants(self):
        BaseDevice._init_constants(self)
        Constants = namedtuple('Constants', ['system', 'dump_files', 'sdk_dump_files', 'firmware'])
        system_dic = {
            'system': [SystemConsts.BUILD, SystemConsts.HOSTNAME, SystemConsts.PLATFORM, SystemConsts.PRODUCT_NAME,
                       SystemConsts.PRODUCT_RELEASE, SystemConsts.SWAP_MEMORY, SystemConsts.SYSTEM_MEMORY,
                       SystemConsts.UPTIME, SystemConsts.TIMEZONE, SystemConsts.HEALTH_STATUS, SystemConsts.DATE_TIME, SystemConsts.STATUS],
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
        firmware = [PlatformConsts.FW_BIOS, PlatformConsts.FW_ONIE, PlatformConsts.FW_SSD, PlatformConsts.FW_CPLD + '1', PlatformConsts.FW_CPLD + '2', PlatformConsts.FW_CPLD + '3']
        self.constants = Constants(system_dic, dump_files, sdk_dump_files, firmware)
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

    def _init_ib_speeds(self):
        self.supported_ib_speeds = {'hdr': '200G', 'edr': '100G', 'fdr': '56G', 'qdr': '40G', 'sdr': '10G'}
        self.invalid_ib_speeds = {}

    def _init_fan_list(self):
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1", "FAN2/2", "FAN3/1", "FAN3/2", "FAN4/1", "FAN4/2",
                         "FAN5/1", "FAN5/2", "FAN6/1", "FAN6/2"]
        self.fan_led_list = ['FAN1', 'FAN2', 'FAN3', 'FAN4', 'FAN5', 'FAN6', "PSU_STATUS", "STATUS", "UID"]

    def _init_sensors_dict(self):
        self.sensors_dict = {}

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.psu_fan_list = ["PSU1/FAN", "PSU2/FAN"]
        self.platform_env_psu_prop = ["capacity", "current", "power", "state", "voltage"]

    def _init_temperature(self):
        self.temperature_list = ["ASIC", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp",
                                 "CPU-Core-1-Temp", "CPU-Pack-Temp", "PSU-1-Temp"]

    def _init_health_components(self):
        self.health_components = self.fan_list + self.psu_list + self.psu_fan_list + \
            ["ASIC Temperature", "Containers", "CPU utilization", "Disk check", "Disk space", "Disk space log"]

    def _init_platform_lists(self):
        self.platform_hw_list = ["asic-count", "cpu", "cpu-load-averages", "disk-size", "hw-revision", "manufacturer",
                                 "memory", "model", "onie-version", "part-number", "product-name", "serial-number",
                                 "system-mac", "system-uuid"]
        self.platform_list = ["fan", "led", "psu", "temperature", "component", "hardware", "environment"]
        self.platform_environment_list = ["fan", "led", "psu", "temperature"]
        self.fan_prop = ["max-speed", "min-speed", "current-speed", "state"]
        self.hw_comp_list = self.fan_list + self.psu_list + ["SWITCH"]
        self.hw_comp_prop = ["hardware-version", "model", "serial", "state", "type"]

    def _init_system_lists(self):
        self.system_list = []
        self.user_fields = ['admin', 'monitor']

    @abstractmethod
    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        raise Exception(f"Not implemented for this switch {self.__class__.__name__}")

    @abstractmethod
    def reload_device(self, engine, cmd_list, validate=False):
        raise Exception(f"Not implemented for this switch {self.__class__.__name__}")


# -------------------------- Jaguar Switch ----------------------------
class JaguarSwitch(BaseSwitch):
    JAGUAR_IB_PORT_NUM = 40
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    def __init__(self):
        BaseSwitch.__init__(self)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format(
            "x86_64-mlnx_mqm8700-r0")

    def ib_ports_num(self):
        return self.JAGUAR_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'ndr': '400G'})

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["Ambient COMEX Temp", ]


# -------------------------- Multi ASIC Switch ----------------------------
class MultiAsicSwitch(BaseSwitch):
    CURRENT_BIOS_VERSION_NAME = "0ACQF_06.01.003"
    CURRENT_BIOS_VERSION_PATH = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x03/Release/0ACQF.cab"
    PREVIOUS_BIOS_VERSION_NAME = "0ACQF_06.01.002"
    PREVIOUS_BIOS_VERSION_PATH = "/auto/sw_system_release/sx_mlnx_bios/CoffeeLake/0ACQF_06.01.x02/Release/0ACQF.cab"

    def __init__(self, asic_amount):
        self.asic_amount = asic_amount
        self.DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + str(index) for index in range(1, asic_amount + 1)]
        self.DEVICE_LIST.append(IbConsts.DEVICE_SYSTEM)
        BaseSwitch.__init__(self)

    def _init_available_databases(self):
        BaseSwitch._init_available_databases(self)
        self.available_tables = {'database': self.available_tables}
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update(
            {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2,
             "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
             "LANES": 0,
             "VIDCOUNTER": 0,
             "RIDTOVID": 0,
             "HIDDEN": 0,
             "COLDVIDS": 0})

    def _init_services(self):
        BaseSwitch._init_services(self)
        for deamon in NvosConst.DOCKER_PER_ASIC_LIST:
            for asic_num in range(0, self.asic_amount):
                self.available_services.append('{deamon}@{asic_num}.service'.format(deamon=deamon, asic_num=asic_num))
        self.available_services.extend(('configmgrd.service', 'countermgrd.service',
                                        'portsyncmgrd.service'))
        self.available_services.remove('syncd-ibv0.service')
        self.available_services.remove('swss-ibv0.service')
        self.available_services.remove('pmon.service')

    def _init_dependent_services(self):
        BaseDevice._init_dependent_services(self)
        self.dependent_services.append(NvosConst.SYM_MGR_SERVICES)

    def _init_dockers(self):
        BaseSwitch._init_dockers(self)
        for deamon in NvosConst.DOCKER_PER_ASIC_LIST:
            for asic_num in range(0, self.asic_amount):
                self.available_dockers.append("{deamon}{asic_num}".format(deamon=deamon, asic_num=asic_num))
        self.available_dockers.remove('syncd-ibv0')
        self.available_dockers.remove('swss-ibv0')
        self.available_dockers.remove('pmon')

    def _init_dependent_dockers(self):
        BaseDevice._init_dependent_dockers(self)
        # TODO maybe in the future we will need it again, but for now they removed this dependency
        # ibv0_dependent_services = []
        # for asic_num in range(self.asic_amount):
        #     ibv0_dependent_services.extend(['swss-ibv0{}'.format(asic_num), 'syncd-ibv0{}'.format(asic_num)])
        # self.dependent_dockers.append(ibv0_dependent_services)

    def _init_constants(self):
        BaseSwitch._init_constants(self)
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
                    output = self.get_all_table_names_in_database(dut_engine, db_name, table_name, database_docker=database_docker).returned_value
                    if len(output) < expected_entries:
                        result_obj.result = False
                        result_obj.info += "Database docker: {database_docker} DB: {db_name}, Table: {table_name}. Table count mismatch, Expected: {expected} != Actual {actual}\n" \
                            .format(database_docker=database_docker, db_name=db_name, table_name=table_name, expected=str(expected_entries),
                                    actual=str(len(output)))

        return result_obj

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        return DutUtilsTool.wait_for_nvos_to_become_functional(engine)

    def reload_device(self, engine, cmd_list, validate=False):
        engine.send_config_set(cmd_list, exit_config_mode=False, cmd_verify=False)

# -------------------------- Marlin Switch ----------------------------


class MarlinSwitch(MultiAsicSwitch):
    ASIC_AMOUNT = 2
    MARLIN_IB_PORT_NUM = 128
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum2'
    PRIMARY_ASIC = "ASIC2"
    PRIMARY_SWID = 'SWID1'
    PRIMARY_IPOIB_INTERFACE = "ib1"
    SECONDARY_IPOIB_INTERFACE = "ib0"
    MULTI_ASIC_SYSTEM = True
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT
    }
    VOLTAGE_SENSORS = ["FAN1/1", "FAN2/1", "PSU1/FAN", "PSU2/FAN"]
    TEMPERATURE_SENSORS = ["ASIC", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp", "CPU-Core-1-Temp", "CPU-Core-2-Temp",
                           "CPU-Core-3-Temp", "CPU-Pack-Temp", "SODIMM-1-Temp"]

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num() / 2},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic,
                                      'database1': available_tables_per_asic})

    def ib_ports_num(self):
        return self.MARLIN_IB_PORT_NUM

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.VOLTAGE_SENSORS,
                             "TEMPERATURE": self.TEMPERATURE_SENSORS}

# -------------------------- Cumulus Switch ----------------------------


class AnacondaSwitch(BaseSwitch):
    SWITCH_CORE_COUNT = 8
    ASIC_TYPE = 'GEN2'

    def __init__(self):
        BaseSwitch.__init__(self)

    def ib_ports_num(self):
        return 0

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list = ["Fan1", "Fan2", "Fan3", "Fan4", "Fan5", "Fan6", "Fan7", "Fan8", "Fan9", "Fan10", "Fan11",
                         "Fan12"]
        self.psu_fan_list = ["PSU1Fan1", "PSU2Fan1"]
        self.fan_led_list = ["Fan Tray 1", "Fan Tray 2", "Fan Tray 3", "Fan Tray 4", "Fan Tray 5", "Fan Tray 6",
                             "Psu", "System"]
        self.fan_prop = ["max-speed", "min-speed", "speed", "state"]

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]
        self.platform_environment_list = self.fan_list + self.fan_led_list + ["PSU1", "PSU2"] \
            + self.psu_fan_list

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

    def _init_constants(self):
        BaseSwitch._init_constants(self)
        self.pre_login_message = "None\n"     # "Debian GNU/Linux 10\n"
        self.post_login_message = "\nWelcome to NVIDIA Cumulus (R) Linux (R)\n\nFor support and online technical documentation, visit\nhttps://www.nvidia.com/en-us/support\n\nThe registered trademark Linux (R) is used pursuant to a sublicense from LMI,\nthe exclusive licensee of Linus Torvalds, owner of the mark on a world-wide\nbasis.\n"

    def wait_for_os_to_become_functional(self, engine, find_prompt_tries=60, find_prompt_delay=10):
        return DutUtilsTool.wait_for_cumulus_to_become_functional(engine)

    def reload_device(self, engine, cmd_set, validate=False):
        engine.run_cmd_set(cmd_set, validate=False)


# -------------------------- Gorilla Switch ----------------------------
class GorillaSwitch(MultiAsicSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum2'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    ASIC_AMOUNT = 1
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_AGGREGATED_PORT = 'sw32p1'
    DEFAULT_LOOPBACK_PORTS = ['sw31p1', 'sw31p2']
    LOOP_BACK_TO_PORTS = {
        'sw31p1': 'sw32p1pl1',
        'sw31p2': 'sw32p1pl2'
    }
    AGGREGATED_PORT_LIST = ['sw1p1', 'sw2p1', 'sw32p1']  # total 3 ports
    FNM_PORT_LIST = 'fnm1'
    AGGREGATED_SPLIT_PORT_LIST = ['sw10p1']
    FNM_INTERNAL_PORT_LIST = ['fnma1p236']
    FNM_EXTERNAL_PORT_LIST = ['fnm1']
    FNM_EXTERNAL_CHILD_PORT = 'fnm1s1'
    SPLIT_AGGREGATED_PORT = ['sw10p1']
    CHILD_AGGREGATED_PORT = 'sw10p1s1'
    AGGREGATED_PORT_PLANARIZED_PORTS = 4
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'disabled', 'disabled', '1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['sw10p1', 'sw10p2', 'sw11p1', 'sw11p2', 'sw12p1', 'sw12p2', 'sw13p1', 'sw13p2',
                                'sw14p1', 'sw14p2', 'sw15p1', 'sw15p2', 'sw16p1', 'sw16p2', 'sw17p1', 'sw17p2',
                                'sw18p1', 'sw18p2', 'sw19p1', 'sw19p2', 'sw20p1', 'sw20p2', 'sw21p1', 'sw21p2',
                                'sw22p1', 'sw22p2', 'sw23p1', 'sw23p2', 'sw24p1', 'sw24p2', 'sw25p1', 'sw25p2',
                                'sw26p1', 'sw26p2', 'sw27p1', 'sw27p2', 'sw28p1', 'sw28p2', 'sw29p1', 'sw29p2',
                                'sw30p1', 'sw3p1', 'sw3p2', 'sw4p1', 'sw4p2', 'sw5p1', 'sw5p2', 'sw6p1', 'sw6p2',
                                'sw7p1', 'sw7p2', 'sw8p1', 'sw8p2', 'sw9p1', 'sw9p2']  # total 55 ports
    ALL_PLANE_PORT_LIST = ['sw1p1pl1', 'sw1p1pl2', 'sw2p1pl1', 'sw2p1pl2', 'sw32p1pl1', 'sw32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + AGGREGATED_PORT_LIST + FNM_EXTERNAL_PORT_LIST + \
        FNM_EXTERNAL_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    NVL5_PORTS_LIST = ['access1p1', 'access1p10', 'access1p11', 'access1p12', 'access1p13', 'access1p14', 'access1p15',
                       'access1p16', 'access1p17', 'access1p18', 'access1p19', 'access1p2', 'access1p20', 'access1p21',
                       'access1p22', 'access1p23', 'access1p24', 'access1p25', 'access1p26', 'access1p27', 'access1p28',
                       'access1p29', 'access1p3', 'access1p30', 'access1p31', 'access1p32', 'access1p33', 'access1p34',
                       'access1p35', 'access1p36', 'access1p37', 'access1p38', 'access1p39', 'access1p4', 'access1p40',
                       'access1p41', 'access1p42', 'access1p43', 'access1p44', 'access1p45', 'access1p46', 'access1p47',
                       'access1p48', 'access1p49', 'access1p5', 'access1p50', 'access1p51', 'access1p52', 'access1p53',
                       'access1p54', 'access1p55', 'access1p56', 'access1p57', 'access1p58', 'access1p59', 'access1p6',
                       'access1p60', 'access1p61', 'access1p62', 'access1p63', 'access1p7', 'access1p8', 'access1p9']
    ALL_NVL5_PORTS_LIST = [NVL5_PORTS_LIST + NON_IB_PORT_LIST]
    NVL5_FNM_PORT = ['fnm1pl1']
    ALL_FAE_NVL5_PORTS_LIST = [NVL5_PORTS_LIST + NON_IB_PORT_LIST + NVL5_FNM_PORT]
    NVL5_PORT = ['access1p48']
    NVL5_PORT_SPEED = '400G'
    NVL5_PORT_TYPE = 'nvl'
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
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
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['hdr', 'ndr']  # ['sdr', 'fdr', 'edr', 'hdr', 'ndr']
    VOLTAGE_SENSORS = ["3.3V-OSFP-P01-P08-Out-1", "3.3V-OSFP-P09-P16-Out-2", "3.3V-OSFP-P17-P24-Out-1",
                       "3.3V-OSFP-P25-P32-Out-2", "12V-ASIC-HVDD-DVDD-In-1", "12V-ASIC-VCORE-In-1",
                       "12V-PORTS-EAST-In-1", "12V-PORTS-WEST-In-1", "13V5-COMEX-VDD-In-1", "ASIC-DVDD-EAST-Out-2",
                       "ASIC-DVDD-WEST-Out-2", "ASIC-HVDD-EAST-Out-1", "ASIC-HVDD-WEST-Out-1", "ASIC-VCORE-Out-1",
                       "COMEX-VCCSA-Out-2", "COMEX-VCORE-Out-1", "PSU-1-12V-Out", "PSU-2-12V-Out"]
    TEMPERATURE_SENSORS = ["ASIC", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp",
                           "CPU-Core-1-Temp", "CPU-Core-2-Temp", "CPU-Core-3-Temp", "CPU-Pack-Temp", "PCH-Temp",
                           "PSU-1-Temp", "PSU-2-Temp", "SODIMM-1-Temp"]

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format("x86_64-mlnx_mqm9700-r0")

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'qdr': '40G'})
        self.supported_ib_speeds.pop('qdr')
        self.supported_ib_speeds.update({'ndr': '400G'})

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list.append("FAN7/1")
        self.fan_list.append("FAN7/2")
        self.fan_led_list.append('FAN7')

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num(),
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic})

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.VOLTAGE_SENSORS,
                             "TEMPERATURE": self.TEMPERATURE_SENSORS}


# -------------------------- BlackMamba Switch ----------------------------
class BlackMambaSwitch(MultiAsicSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum3'
    ASIC_AMOUNT = 4
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'enabled', 'disabled', '1']
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_AGGREGATED_PORT = 'sw32p1'
    DEFAULT_LOOPBACK_PORTS = ['sw31p1', 'sw31p2']
    LOOP_BACK_TO_PORTS = {
        'sw31p1': 'sw32p1pl1',
        'sw31p2': 'sw32p1pl2'
    }
    AGGREGATED_PORT_LIST = ['sw1p1', 'sw2p1', 'sw32p1']  # total 3 ports
    SPLIT_AGGREGATED_PORT = ['sw10p1']
    FNM_PORT_LIST = ['fnm1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['sw10p1', 'sw10p2', 'sw11p1', 'sw11p2', 'sw12p1', 'sw12p2', 'sw13p1', 'sw13p2',
                                'sw14p1', 'sw14p2', 'sw15p1', 'sw15p2', 'sw16p1', 'sw16p2', 'sw17p1', 'sw17p2',
                                'sw18p1', 'sw18p2', 'sw19p1', 'sw19p2', 'sw20p1', 'sw20p2', 'sw21p1', 'sw21p2',
                                'sw22p1', 'sw22p2', 'sw23p1', 'sw23p2', 'sw24p1', 'sw24p2', 'sw25p1', 'sw25p2',
                                'sw26p1', 'sw26p2', 'sw27p1', 'sw27p2', 'sw28p1', 'sw28p2', 'sw29p1', 'sw29p2',
                                'sw30p1', 'sw30p2', 'sw3p1', 'sw3p2', 'sw4p1', 'sw4p2', 'sw5p1', 'sw5p2', 'sw6p1',
                                'sw6p2', 'sw7p1', 'sw7p2', 'sw8p1', 'sw8p2', 'sw9p1', 'sw9p2']  # total 56 ports
    ALL_PLANE_PORT_LIST = ['sw1p1pl1', 'sw1p1pl2', 'sw2p1pl1', 'sw2p1pl2', 'sw32p1pl1', 'sw32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + AGGREGATED_PORT_LIST + FNM_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
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
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['sdr', 'fdr', 'edr', 'hdr', 'ndr']

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.\
            format("x86_64-mlnx_qm8790-r0")

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'qdr': '40G'})
        self.supported_ib_speeds.pop('qdr')
        self.supported_ib_speeds.update({'ndr': '400G'})

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list += ["FAN7/1", "FAN7/2", "FAN8/1", "FAN8/2", "FAN9/1", "FAN9/2", "FAN10/1", "FAN10/2"]
        self.fan_led_list += ['FAN7', 'FAN8', 'FAN9', 'FAN10']

    def _init_psu_list(self):
        BaseSwitch._init_psu_list(self)
        self.psu_list += ["PSU3", "PSU4", "PSU5", "PSU6", "PSU7", "PSU8"]
        self.psu_fan_list += ["PSU3/FAN", "PSU4/FAN", "PSU5/FAN", "PSU6/FAN", "PSU7/FAN", "PSU8/FAN"]

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["ASIC2", "ASIC3", "ASIC4", "CPU-Core-2-Temp", "CPU-Core-3-Temp", "PSU-7-Temp",
                                  "SODIMM-1-Temp", "SODIMM-2-Temp"]
        self.temperature_list.remove("PSU-1-Temp")

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT":
                                                                            self.ib_ports_num(),
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic})

    VOLTAGE_SENSORS = ["PMIC-1+12V_VDD_ASIC1+Vol+In+1", "PMIC-1+ASIC1_VDD+Vol+Out+1",
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
    TEMPERATURE_SENSORS = ["ASIC", "ASIC2", "ASIC3", "ASIC4", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp",
                           "CPU-Core-0-Temp", "CPU-Core-1-Temp", "CPU-Core-2-Temp", "CPU-Core-3-Temp", "CPU-Pack-Temp",
                           "PSU-7-Temp", "SODIMM-1-Temp", "SODIMM-2-Temp"]

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.VOLTAGE_SENSORS,
                             "TEMPERATURE": self.TEMPERATURE_SENSORS}


# -------------------------- Crocodile Switch ----------------------------
class CrocodileSwitch(MultiAsicSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum3'
    ASIC_AMOUNT = 2
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'enabled', 'disabled', '1']
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_AGGREGATED_PORT = 'sw32p1'
    DEFAULT_LOOPBACK_PORTS = ['sw31p1', 'sw31p2']
    LOOP_BACK_TO_PORTS = {
        'sw31p1': 'sw32p1pl1',
        'sw31p2': 'sw32p1pl2'
    }
    AGGREGATED_PORT_LIST = ['sw1p1', 'sw2p1', 'sw32p1']  # total 3 ports
    SPLIT_AGGREGATED_PORT = ['sw10p1']
    FNM_PORT_LIST = ['fnm1']
    FNM_INTERNAL_PORT_LIST = ['fnma1p236']
    FNM_EXTERNAL_PORT_LIST = ['fnm1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['sw10p1', 'sw10p2', 'sw11p1', 'sw11p2', 'sw12p1', 'sw12p2', 'sw13p1', 'sw13p2',
                                'sw14p1', 'sw14p2', 'sw15p1', 'sw15p2', 'sw16p1', 'sw16p2', 'sw17p1', 'sw17p2',
                                'sw18p1', 'sw18p2', 'sw19p1', 'sw19p2', 'sw20p1', 'sw20p2', 'sw21p1', 'sw21p2',
                                'sw22p1', 'sw22p2', 'sw23p1', 'sw23p2', 'sw24p1', 'sw24p2', 'sw25p1', 'sw25p2',
                                'sw26p1', 'sw26p2', 'sw27p1', 'sw27p2', 'sw28p1', 'sw28p2', 'sw29p1', 'sw29p2',
                                'sw30p1', 'sw30p2', 'sw3p1', 'sw3p2', 'sw4p1', 'sw4p2', 'sw5p1', 'sw5p2', 'sw6p1',
                                'sw6p2', 'sw7p1', 'sw7p2', 'sw8p1', 'sw8p2', 'sw9p1', 'sw9p2']  # total 56 ports
    ALL_PLANE_PORT_LIST = ['sw1p1pl1', 'sw1p1pl2', 'sw2p1pl1', 'sw2p1pl2', 'sw32p1pl1', 'sw32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + AGGREGATED_PORT_LIST + FNM_EXTERNAL_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
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
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['sdr', 'fdr', 'edr', 'hdr', 'ndr']

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.\
            format("x86_64-nvidia_qm3400-r0")

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'qdr': '40G'})
        self.supported_ib_speeds.pop('qdr')
        self.supported_ib_speeds.update({'ndr': '400G'})

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list.remove("FAN6/1")
        self.fan_list.remove("FAN6/2")
        self.fan_led_list.remove('FAN6')

    def _init_psu_list(self):
        BaseSwitch._init_psu_list(self)
        self.psu_list += ["PSU3", "PSU4"]
        self.psu_fan_list += ["PSU3/FAN", "PSU4/FAN"]

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PSU-2-Temp", "PSU-3-Temp", "PSU-4-Temp"]
        self.temperature_list.remove("ASIC")

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num(),
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic})

    VOLTAGE_SENSORS = ["PMIC-1+12V_VDD_ASIC1+Vol+In+1", "PMIC-1+ASIC1_VDD+Vol+Out+1",
                       "PMIC-2+12V_HVDD_DVDD_ASIC1+Vol+In+1", "PMIC-2+ASIC1_DVDD_PL0+Vol+Out+2",
                       "PMIC-2+ASIC1_HVDD_PL0+Vol+Out+1", "PMIC-3+12V_HVDD_DVDD_ASIC1+Vol+In+1",
                       "PMIC-3+ASIC1_DVDD_PL1+Vol+Out+2", "PMIC-3+ASIC1_HVDD_PL1+Vol+Out+1",
                       "PMIC-4+12V_VDD_ASIC2+Vol+In+1", "PMIC-4+ASIC2_VDD+Vol+Out+1",
                       "PMIC-5+12V_HVDD_DVDD_ASIC2+Vol+In+1", "PMIC-5+ASIC2_DVDD_PL0+Vol+Out+2",
                       "PMIC-5+ASIC2_HVDD_PL0+Vol+Out+1", "PMIC-6+12V_HVDD_DVDD_ASIC2+Vol+In+1",
                       "PMIC-6+ASIC2_DVDD_PL1+Vol+Out+2", "PMIC-6+ASIC2_HVDD_PL1+Vol+Out+1",
                       "PMIC-7+12V_MAIN+Vol+In+1", "PMIC-7+CEX_VDD+Vol+Out+1", "PSU-1+12V+Vol+Out", "PSU-2+12V+Vol+Out",
                       "PSU-3+12V+Vol+Out", "PSU-4+12V+Vol+Out"]
    TEMPERATURE_SENSORS = ["Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp", "CPU-Core-1-Temp",
                           "CPU-Core-2-Temp", "CPU-Core-3-Temp", "CPU-Pack-Temp", "PSU-1-Temp", "PSU-2-Temp",
                           "PSU-3-Temp", "PSU-4-Temp", "SODIMM-1-Temp"]

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.VOLTAGE_SENSORS,
                             "TEMPERATURE": self.TEMPERATURE_SENSORS}


# -------------------------- Juliet Switch ----------------------------
class JulietSwitch(MultiAsicSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum3'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    ASIC_AMOUNT = 1
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'enabled', 'disabled', '1']
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_LOOPBACK_PORTS = ['access31p1', 'access31p2']
    LOOP_BACK_TO_PORTS = {
        'access31p1': 'access32p1pl1',
        'access31p2': 'access32p1pl2'
    }
    AGGREGATED_PORT_LIST = ['access1p1', 'access2p1', 'access32p1']  # total 3 ports
    FNM_PORT_LIST = ['fnm1']
    FNM_EXTERNAL_PORT_LIST = ['fnm1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['access10p1', 'access10p2', 'access11p1', 'access11p2', 'access12p1', 'access12p2',
                                'access13p1', 'access13p2', 'access14p1', 'access14p2', 'access15p1', 'access15p2',
                                'access16p1', 'access16p2', 'access17p1', 'access17p2', 'access18p1', 'access18p2',
                                'access19p1', 'access19p2', 'access20p1', 'access20p2', 'access21p1', 'access21p2',
                                'access22p1', 'access22p2', 'access23p1', 'access23p2', 'access24p1', 'access24p2',
                                'access25p1', 'access25p2', 'access26p1', 'access26p2', 'access27p1', 'access27p2',
                                'access28p1', 'access28p2', 'access29p1', 'access29p2', 'access30p1', 'access30p2',
                                'access3p1', 'access3p2', 'access4p1', 'access4p2', 'access5p1', 'access5p2',
                                'access6p1', 'access6p2', 'access7p1', 'access7p2', 'access8p1', 'access8p2',
                                'access9p1', 'access9p2']  # total 56 ports
    ALL_PLANE_PORT_LIST = ['access1p1pl1', 'access1p1pl2', 'access2p1pl1', 'access2p1pl2',
                           'access32p1pl1', 'access32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + FNM_EXTERNAL_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
        'access1p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access2p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access32p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        }
    }
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['sdr', 'fdr', 'edr', 'hdr', 'ndr']

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format("x86_64-mlnx_mqm9700-r0")

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'qdr': '40G'})
        self.supported_ib_speeds.pop('qdr')
        self.supported_ib_speeds.update({'ndr': '400G'})

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list.append("FAN7/1")
        self.fan_list.append("FAN7/2")
        self.fan_led_list.append('FAN7')

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num(),
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic})


# -------------------------- JulietScaleout Switch ----------------------------
class JulietScaleoutSwitch(JulietSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum3'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    ASIC_AMOUNT = 1
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'enabled', 'disabled', '1']
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_LOOPBACK_PORTS = ['access31p1', 'access31p2']
    LOOP_BACK_TO_PORTS = {
        'access31p1': 'access32p1pl1',
        'access31p2': 'access32p1pl2'
    }
    FNM_PORT_LIST = ['fnm1']
    FNM_EXTERNAL_PORT_LIST = ['fnm1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['access10p1', 'access10p2', 'access11p1', 'access11p2', 'access12p1', 'access12p2',
                                'access13p1', 'access13p2', 'access14p1', 'access14p2', 'access15p1', 'access15p2',
                                'access16p1', 'access16p2', 'access17p1', 'access17p2', 'access18p1', 'access18p2',
                                'access19p1', 'access19p2', 'access20p1', 'access20p2', 'access21p1', 'access21p2',
                                'access22p1', 'access22p2', 'access23p1', 'access23p2', 'access24p1', 'access24p2',
                                'access25p1', 'access25p2', 'access26p1', 'access26p2', 'access27p1', 'access27p2',
                                'access28p1', 'access28p2', 'access29p1', 'access29p2', 'access30p1', 'access30p2',
                                'access3p1', 'access3p2', 'access4p1', 'access4p2', 'access5p1', 'access5p2',
                                'access6p1', 'access6p2', 'access7p1', 'access7p2', 'access8p1', 'access8p2',
                                'access9p1', 'access9p2']  # total 56 ports
    ALL_PLANE_PORT_LIST = ['access1p1pl1', 'access1p1pl2', 'access2p1pl1',
                           'access2p1pl2', 'access32p1pl1', 'access32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + FNM_EXTERNAL_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
        'access1p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access2p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access32p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        }
    }
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['sdr', 'fdr', 'edr', 'hdr', 'ndr']


# -------------------------- Caiman Switch ----------------------------
class CaimanSwitch(MultiAsicSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum3'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    ASIC_AMOUNT = 1
    PRIMARY_ASIC = "ASIC1"
    PRIMARY_SWID = 'SWID0'
    PRIMARY_IPOIB_INTERFACE = "ib0"
    SYSTEM_PROFILE_DEFAULT_VALUES = ['enabled', '2048', 'enabled', 'disabled', '1']
    MULTI_ASIC_SYSTEM = False
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface', 'voltage']
    CATEGORY_DISK_INTERVAL_DEFAULT = '30'  # [min]
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.STATE_DEFAULT
    }
    CATEGORY_DISK_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: CATEGORY_DISK_INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DISABLED_DICT
    }
    CATEGORY_LIST_DEFAULT_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[2]: CATEGORY_DISK_DEFAULT_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DICT,
        CATEGORY_LIST[6]: CATEGORY_DEFAULT_DICT
    }

    PLANE_PORT_LIST = ['pl1', 'pl2']
    DEFAULT_LOOPBACK_PORTS = ['access31p1', 'access31p2']
    LOOP_BACK_TO_PORTS = {
        'access31p1': 'access32p1pl1',
        'access31p2': 'access32p1pl2'
    }
    FNM_PORT_LIST = ['fnm1']
    FNM_EXTERNAL_PORT_LIST = ['fnm1']
    FNM_PLANE_PORT_LIST = ['fnm1pl1', 'fnm1pl2']  # total 2 ports
    NON_IB_PORT_LIST = ['eth0', 'ib0', 'lo']  # total 3 ports
    NON_AGGREGATED_PORT_LIST = ['access10p1', 'access10p2', 'access11p1', 'access11p2', 'access12p1', 'access12p2',
                                'access13p1', 'access13p2', 'access14p1', 'access14p2', 'access15p1', 'access15p2',
                                'access16p1', 'access16p2', 'access17p1', 'access17p2', 'access18p1', 'access18p2',
                                'access19p1', 'access19p2', 'access20p1', 'access20p2', 'access21p1', 'access21p2',
                                'access22p1', 'access22p2', 'access23p1', 'access23p2', 'access24p1', 'access24p2',
                                'access25p1', 'access25p2', 'access26p1', 'access26p2', 'access27p1', 'access27p2',
                                'access28p1', 'access28p2', 'access29p1', 'access29p2', 'access30p1', 'access30p2',
                                'access3p1', 'access3p2', 'access4p1', 'access4p2', 'access5p1', 'access5p2',
                                'access6p1', 'access6p2', 'access7p1', 'access7p2', 'access8p1', 'access8p2',
                                'access9p1', 'access9p2']  # total 56 ports
    ALL_PLANE_PORT_LIST = ['access1p1pl1', 'access1p1pl2', 'access2p1pl1', 'access2p1pl2',
                           'access32p1pl1', 'access32p1pl2']  # total 6 ports
    ALL_PORT_LIST = NON_AGGREGATED_PORT_LIST + FNM_EXTERNAL_PORT_LIST + NON_IB_PORT_LIST  # total 63 ports
    ALL_FAE_PORT_LIST = ALL_PORT_LIST + ALL_PLANE_PORT_LIST + FNM_PLANE_PORT_LIST  # total 71 ports
    ASIC0 = 'asic0'
    ASIC1 = 'asic1'
    COUNTERS_DB_NAME = 'COUNTERS_DB'
    OBJECT_NUMBERS = {  # TBD - update values
        'access1p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access2p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        },
        'access32p1': {
            'plane1': 'COUNTERS:oid:0x100000000001f',
            'plane2': 'COUNTERS:oid:0x100000000001f'
        }
    }
    FNM_LINK_SPEED = '400G'
    SUPPORTED_IB_SPEED = ['sdr', 'fdr', 'edr', 'hdr', 'ndr']

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)
        self.health_monitor_config_file_path = HealthConsts.HEALTH_MONITOR_CONFIG_FILE_PATH.format("x86_64-mlnx_mqm9700-r0")

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM

    def _init_ib_speeds(self):
        BaseSwitch._init_ib_speeds(self)
        self.invalid_ib_speeds.update({'qdr': '40G'})
        self.supported_ib_speeds.pop('qdr')
        self.supported_ib_speeds.update({'ndr': '400G'})

    def _init_fan_list(self):
        BaseSwitch._init_fan_list(self)
        self.fan_list.append("FAN7/1")
        self.fan_list.append("FAN7/2")
        self.fan_led_list.append('FAN7')

    def _init_temperature(self):
        BaseSwitch._init_temperature(self)
        self.temperature_list += ["CPU-Core-2-Temp", "CPU-Core-3-Temp", "PCH-Temp", "PSU-2-Temp"]

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num(),
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"ALIAS_PORT_MAP": self.ib_ports_num()},
            DatabaseConst.ASIC_DB_ID:
                {"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2 + 1,
                 "LANES": 1,
                 "VIDCOUNTER": 1,
                 "RIDTOVID": 1,
                 "HIDDEN": 1,
                 "COLDVIDS": 1},
            DatabaseConst.COUNTERS_DB_ID:
                {"COUNTERS_PORT_NAME_MAP": 1,
                 "COUNTERS:oid": self.ib_ports_num() / 2},
            DatabaseConst.CONFIG_DB_ID:
                {"IB_PORT": self.ib_ports_num() / 2,
                 "FEATURE": 6,
                 "CONFIG_DB_INITIALIZED": 1,
                 "DEVICE_METADATA": 1,
                 "VERSIONS": 0,
                 "KDUMP": 0}
        }
        self.available_tables.update({'database0': available_tables_per_asic})


# -------------------------- Gorilla Switch ----------------------------
class GorillaSwitchBF3(GorillaSwitch):
    SWITCH_CORE_COUNT = 16
    VOLTAGE_SENSORS = ["3.3V-OSFP-P01-P08-Out-1", "3.3V-OSFP-P09-P16-Out-2", "3.3V-OSFP-P17-P24-Out-1",
                       "3.3V-OSFP-P25-P32-Out-2", "12V-ASIC-HVDD-DVDD-In-1", "12V-ASIC-VCORE-In-1",
                       "12V-PORTS-EAST-In-1", "12V-PORTS-WEST-In-1", "13V5-COMEX-VDD-In-1", "ASIC-DVDD-EAST-Out-2",
                       "ASIC-DVDD-WEST-Out-2", "ASIC-HVDD-EAST-Out-1", "ASIC-HVDD-WEST-Out-1", "ASIC-VCORE-Out-1",
                       "COMEX-VCCSA-Out-2", "COMEX-VCORE-Out-1", "PSU-1-12V-Out", "PSU-2-12V-Out"]
    TEMPERATURE_SENSORS = ["ASIC", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "CPU-Core-0-Temp",
                           "CPU-Core-1-Temp", "CPU-Core-2-Temp", "CPU-Core-3-Temp", "CPU-Pack-Temp", "PCH-Temp",
                           "PSU-1-Temp", "PSU-2-Temp", "SODIMM-1-Temp"]

    def _init_temperature(self):
        GorillaSwitch._init_temperature(self)
        self.temperature_list = ["ASIC", "Ambient-Fan-Side-Temp", "Ambient-Port-Side-Temp", "PSU-1-Temp", "PSU-2-Temp",
                                 "xSFP-module-26-Temp", "xSFP-module-29-Temp"]
        GorillaSwitch._init_constants(self)
        self.constants.firmware.remove(PlatformConsts.FW_BIOS)

    def _init_sensors_dict(self):
        self.sensors_dict = {"VOLTAGE": self.VOLTAGE_SENSORS,
                             "TEMPERATURE": self.TEMPERATURE_SENSORS}