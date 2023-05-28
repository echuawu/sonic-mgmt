import re
import logging
from collections import namedtuple
from abc import abstractmethod, ABCMeta, ABC
from ngts.nvos_constants.constants_nvos import NvosConst, DatabaseConst, IbConsts, StatsConsts
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_constants.constants_nvos import SystemConsts, HealthConsts
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
        time.sleep(10)
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
        result_obj = self._verify_value_in_table(dut_engine, DatabaseConst.CONFIG_DB_NAME,
                                                 NvosConst.PORT_CONFIG_DB_TABLES_PREFIX,
                                                 NvosConst.PORT_STATUS_LABEL, expected_port_state)
        return result_obj

    def verify_dockers(self, dut_engine):
        result_obj = ResultObj(True, "")
        cmd_output = dut_engine.run_cmd('docker ps --format \"table {{.Names}}\"')
        for docker in self.available_dockers:
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

        cmd = "redis-cli -n {database_name} hgetall {table_name}".format(
            table_name='"' + table_name + '"', database_name=self.get_database_id(database_name))

        output = engine.run_cmd(cmd)
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
        docker_exec_cmd = 'docker exec -it {database_docker} '.format(database_docker=database_docker) if database_docker else ''
        cmd = docker_exec_cmd + "redis-cli -n {database_name} keys * | grep {prefix}".format(
            database_name=self.get_database_id(database_name), prefix=table_name_substring)
        output = engine.run_cmd(cmd)
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
                    {"IB_PORT_TABLE:Infiniband": self.ib_ports_num(),
                     "ALIAS_PORT_MAP": self.ib_ports_num(),
                     "IB_PORT_TABLE:Port": 2},
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
                     "BREAKOUT_CFG": self.ib_ports_num(),
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
        self.available_dockers.extend(('pmon', 'syncd-ibv0', 'swss-ibv0', 'database', 'ib-utils'))

    def _init_dependent_dockers(self):
        BaseDevice._init_dependent_dockers(self)
        # TODO maybe in the future we will need it again, but for now they removed this dependency
        # self.dependent_dockers.extend([['swss-ibv0', 'syncd-ibv0']])

    def _init_constants(self):
        BaseDevice._init_constants(self)
        Constants = namedtuple('Constants', ['system', 'dump_files'])
        system_dic = {
            'system': [SystemConsts.BUILD, SystemConsts.HOSTNAME, SystemConsts.PLATFORM, SystemConsts.PRODUCT_NAME,
                       SystemConsts.PRODUCT_RELEASE, SystemConsts.SWAP_MEMORY, SystemConsts.SYSTEM_MEMORY,
                       SystemConsts.UPTIME, SystemConsts.TIMEZONE, SystemConsts.HEALTH_STATUS, SystemConsts.DATE_TIME],
            'message': [SystemConsts.PRE_LOGIN_MESSAGE, SystemConsts.POST_LOGIN_MESSAGE],
            'reboot': [SystemConsts.REBOOT_REASON],
            'version': [SystemConsts.VERSION_BUILD_DATE, SystemConsts.VERSION_BUILT_BY, SystemConsts.VERSION_IMAGE,
                        SystemConsts.VERSION_KERNEL]
        }
        dump_files = ['APPL_DB.json', 'ASIC_DB.json', 'boot.conf', 'bridge.fdb', 'bridge.vlan', 'CONFIG_DB.json',
                      'COUNTERS_DB_1.json', 'COUNTERS_DB_2.json', 'COUNTERS_DB.json', 'date.counter_1',
                      'date.counter_2', 'df', 'dmesg', 'docker.pmon', 'docker.ps', 'docker.stats',
                      'docker.swss-ibv0.log', 'dpkg', 'fan', 'FLEX_COUNTER_DB.json', 'free', 'hdparm', 'ib-utils.dump',
                      'ifconfig.counters_1', 'ifconfig.counters_2', 'interface.status', 'interface.xcvrs.eeprom',
                      'interface.xcvrs.presence', 'ip.addr', 'ip.interface', 'ip.link', 'ip.link.stats', 'ip.neigh',
                      'ip.neigh.noarp', 'ip.route', 'ip.rule', 'lspci', 'lsusb', 'machine.conf', 'mount', 'nat.config',
                      'nat.conntrack', 'nat.conntrackall', 'nat.conntrackallcount', 'nat.conntrackcount',
                      'nat.iptables', 'netstat.counters_1', 'netstat.counters_2', 'platform.summary',
                      'ps.aux', 'ps.extended', 'psustatus', 'queue.counters_1', 'queue.counters_2', 'reboot.cause',
                      'saidump', 'sensors', 'services.summary', 'ssdhealth', 'STATE_DB.json', 'swapon', 'sysctl',
                      'syseeprom', 'systemd.analyze.blame', 'systemd.analyze.dump', 'systemd.analyze.plot.svg',
                      'temperature', 'top', 'version', 'vlan.summary', 'vmstat', 'vmstat.m', 'vmstat.s', 'who']
        self.constants = Constants(system_dic, dump_files)

    def _init_ib_speeds(self):
        self.supported_ib_speeds = {'hdr': '200G', 'edr': '100G', 'fdr': '56G', 'qdr': '40G', 'sdr': '10G'}
        self.invalid_ib_speeds = {}

    def _init_fan_list(self):
        self.fan_list = ["FAN1/1", "FAN1/2", "FAN2/1", "FAN2/2", "FAN3/1", "FAN3/2", "FAN4/1", "FAN4/2",
                         "FAN5/1", "FAN5/2", "FAN6/1", "FAN6/2"]
        self.fan_led_list = ['FAN1', 'FAN2', 'FAN3', 'FAN4', 'FAN5', 'FAN6', "PSU_STATUS", "STATUS", "UID"]

    def _init_psu_list(self):
        self.psu_list = ["PSU1", "PSU2"]
        self.psu_fan_list = ["PSU1/FAN", "PSU2/FAN"]
        self.platform_env_psu_prop = ["capacity", "current", "power", "state", "voltage"]

    def _init_temperature(self):
        self.temperature_list = ["ASIC", "Ambient Fan Side Temp", "Ambient Port Side Temp", "CPU Core 0 Temp",
                                 "CPU Core 1 Temp", "CPU Pack Temp", "PSU-1 Temp"]

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


# -------------------------- Gorilla Switch ----------------------------
class GorillaSwitch(BaseSwitch):
    GORILLA_IB_PORT_NUM = 64
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum2'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]
    CATEGORY_LIST = ['temperature', 'cpu', 'disk', 'power', 'fan', 'mgmt-interface']
    CATEGORY_DEFAULT_DISABLED_DICT = {
        StatsConsts.HISTORY_DURATION: StatsConsts.HISTORY_DURATION_DEFAULT,
        StatsConsts.INTERVAL: StatsConsts.INTERVAL_DEFAULT,
        StatsConsts.STATE: StatsConsts.State.DISABLED.value
    }
    CATEGORY_DISABLED_DICT = {
        CATEGORY_LIST[0]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[1]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[2]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[3]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[4]: CATEGORY_DEFAULT_DISABLED_DICT,
        CATEGORY_LIST[5]: CATEGORY_DEFAULT_DISABLED_DICT
    }

    def __init__(self):
        BaseSwitch.__init__(self)
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
        self.temperature_list += ["CPU Core 2 Temp", "CPU Core 3 Temp", "PCH Temp", "PSU-2 Temp"]


# -------------------------- Jaguar Switch ----------------------------
class JaguarSwitch(BaseSwitch):
    JAGUAR_IB_PORT_NUM = 40
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum'
    DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + '1', IbConsts.DEVICE_SYSTEM]

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

    def __init__(self, asic_amount):
        self.asic_amount = asic_amount
        self.DEVICE_LIST = [IbConsts.DEVICE_ASIC_PREFIX + str(index) for index in range(1, asic_amount + 1)]
        self.DEVICE_LIST.append(IbConsts.DEVICE_SYSTEM)
        BaseSwitch.__init__(self)

    def _init_available_databases(self):
        BaseSwitch._init_available_databases(self)
        self.available_tables = {'database': self.available_tables}

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


# -------------------------- Marlin Switch ----------------------------
class MarlinSwitch(MultiAsicSwitch):
    ASIC_AMOUNT = 2
    MARLIN_IB_PORT_NUM = 128
    SWITCH_CORE_COUNT = 4
    ASIC_TYPE = 'Quantum2'

    def __init__(self):
        MultiAsicSwitch.__init__(self, self.ASIC_AMOUNT)

    def _init_available_databases(self):
        MultiAsicSwitch._init_available_databases(self)
        self.available_tables['database'][DatabaseConst.ASIC_DB_ID].update({"ASIC_STATE:SAI_OBJECT_TYPE_PORT": self.ib_ports_num() / 2,
                                                                            "ASIC_STATE:SAI_OBJECT_TYPE_SWITCH": 0,
                                                                            "LANES": 0,
                                                                            "VIDCOUNTER": 0,
                                                                            "RIDTOVID": 0,
                                                                            "HIDDEN": 0,
                                                                            "COLDVIDS": 0})

        available_tables_per_asic = {
            DatabaseConst.APPL_DB_ID:
                {"IB_PORT_TABLE:Infiniband": self.ib_ports_num() / 2,
                 "ALIAS_PORT_MAP": self.ib_ports_num() / 2,
                 "IB_PORT_TABLE:Port": 2},
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
                 "BREAKOUT_CFG": self.ib_ports_num() / 2,
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


# -------------------------- Cumulus Switch ----------------------------
class AnacondaSwitch(BaseSwitch):
    SWITCH_CORE_COUNT = 4
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
        self.temperature_list += ["CPU Core 2 Temp", "CPU Core 3 Temp", "PCH Temp", "PSU-2 Temp"]
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
