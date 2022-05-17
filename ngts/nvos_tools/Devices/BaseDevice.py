from abc import abstractmethod, ABCMeta, ABC
import logging
from ngts.constants.constants_nvos import NvosConst, DatabaseConst
from ngts.nvos_tools.infra.DatabaseReaderTool import DatabaseReaderTool
from ngts.nvos_tools.infra.ResultObj import ResultObj

logger = logging.getLogger()


class BaseDevice:

    def __init__(self):
        self.available_databases = {}
        self.available_tables = {}
        self.available_services = []
        self.available_dockers = []

        self._init_available_databases()
        self._init_services()
        self._init_dockers()

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
    def _init_dockers(self):
        pass

    def verify_databases(self, dut_engine):
        """
        validate the redis includes all expected tables
        :param dut_engine: ssh dut engine
        Return result_obj with True result if all tables exists, False and a relevant info if one or more tables are missing
        """
        result_obj = ResultObj(True, "")
        for db_name, db_id in self.available_databases.items():
            table_info = self.available_tables[db_id]
            for table_name, expected_entries in table_info.items():
                output = DatabaseReaderTool.get_all_table_names_in_database(dut_engine, db_name,
                                                                            table_name).returned_value
                if len(output) != expected_entries:
                    result_obj.result = False
                    result_obj.info += "DB: {db_name}, Table: {table_name}. Table count mismatch, Expected: {expected} != Actual {actual}\n" \
                        .format(db_name=db_name, table_name=table_name, expected=str(expected_entries),
                                actual=str(len(output)))
        return result_obj

    def _verify_value_in_table(self, dut_engine, db_name, table_name, field_name, expected_value):
        """
        :param db_name: Database name
        :param table_name: table name
        :param dut_engine: the dut engine
        :param field_name: the field name in the table
        :param expected_value: an expected value for the field
        :return: result_obj
        """
        result_obj = ResultObj(True, "")
        obj = DatabaseReaderTool.read_from_database(db_name, dut_engine, table_name, field_name)
        if obj.verify_result() != expected_value:
            result_obj.result = False
            logger.error("{field_name} value in {table_name} DB {database_name} is {obj_value} not {expected_value}"
                         " as expected \n".format(field_name=field_name, table_name=table_name,
                                                  database_name=db_name, obj_value=obj.returned_value,
                                                  expected_value=expected_value))
        if not result_obj.result:
            result_obj.info = "Value Mismatch"
        return result_obj

    def verify_ib_ports_state(self, dut_engine, expected_port_state, ib_ports_to_check=None):
        if ib_ports_to_check is None:
            ib_ports_to_check = range(self.ib_ports_num())

        result_obj = ResultObj(True, "")
        for i in ib_ports_to_check:
            port_result = self._verify_value_in_table(dut_engine, DatabaseConst.CONFIG_DB_NAME, "IB_PORT",
                                                      NvosConst.PORT_STATUS_LABEL, expected_port_state)
            if not port_result.result:
                result_obj.result = False
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
             DatabaseConst.COUNTERS_DB_NAME: DatabaseConst.COUNTERS_DB_ID,
             DatabaseConst.CONFIG_DB_NAME: DatabaseConst.CONFIG_DB_ID,
             DatabaseConst.STATE_DB_NAME: DatabaseConst.STATE_DB_ID
             })

        self.available_tables.update(
            {
                DatabaseConst.APPL_DB_ID:
                    {"IB_PORT_TABLE:Infiniband": self.ib_ports_num(),
                     "ALIAS_PORT_MAP": 1},
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
                     "XCVRD_LOG": 1,
                     "VERSIONS": 1,
                     "KDUMP": 1}
            })

    def _init_services(self):
        BaseDevice._init_services(self)
        self.available_services.append(
            ('docker.service', 'database.service', 'hw-management.service', 'config-setup.service',
             'updategraph.service', 'ntp.service', 'hostname-config.service', 'ntp-config.service',
             'rsyslog-config.service', 'procdockerstatsd.service', 'swss-ibv0.service',
             'syncd-ibv0.service', 'pmon.service'))

    def _init_dockers(self):
        BaseDevice._init_services(self)
        self.available_dockers.append(('nvue', 'pmon', 'syncd-ibv0', 'swss-ibv0', 'database'))


# -------------------------- Gorilla Switch ----------------------------
class GorillaSwitch(BaseSwitch):
    GORILLA_IB_PORT_NUM = 64

    def __init__(self):
        BaseSwitch.__init__(self)

    def ib_ports_num(self):
        return self.GORILLA_IB_PORT_NUM


# -------------------------- Jaguar Switch ----------------------------
class JaguarSwitch(BaseSwitch):
    JAGUAR_IB_PORT_NUM = 40

    def __init__(self):
        BaseSwitch.__init__(self)

    def ib_ports_num(self):
        return self.JAGUAR_IB_PORT_NUM
