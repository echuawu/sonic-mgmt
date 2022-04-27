import logging
from .ResultObj import ResultObj
from .NvosTestToolkit import TestToolkit
from ngts.constants.constants_nvos import NvosConst, DatabaseConst
import re
logger = logging.getLogger()
EMPTY_ARRAY = '(empty array)'


class DatabaseReaderTool:
    @staticmethod
    def read_from_database(database_name, engine=None, table_name=None, field_name=None):
        """
        Read the value of required field in specified database
        :param engine: dut engine
        :param database_name: the name of the database
        :param table_name: the table name in the given database
        :param field_name: the field name in table
        :return: ResultObj
        """
        if not engine:
            engine = TestToolkit.engines.dut
        result_obj = ResultObj(True, "")
        if not DatabaseReaderTool._database_exists_in_redis(database_name):
            result_obj.result = False
            result_obj.info += "{database_name} can't be found in Redis".format(database_name=database_name)
            return result_obj
        if not DatabaseReaderTool._table_exists_in_database(engine, database_name, table_name):
            result_obj.result = False
            result_obj.info += \
                "{table_name} can't be found in database " \
                "{database_name}".format(table_name=table_name, database_name=database_name)
            return result_obj

        output = DatabaseReaderTool._get_table_content(engine, database_name, table_name)
        output = DatabaseReaderTool.redis_cmd_output_parser(output)
        result_obj.returned_value = output[field_name] if field_name else output

        return result_obj

    @staticmethod
    def _table_exists_in_database(engine, database_name, table_name):
        """
        Return True if the table name exists in specified database, False - otherwise
        :param engine: player engine
        :param database_name: the name of the database
        :param table_name: the name of the table
        :return: Boolean value
        """
        if not table_name:
            return False
        output = DatabaseReaderTool.get_all_table_names_in_database(engine, database_name).returned_value

        return table_name in output

    @staticmethod
    def _database_exists_in_redis(database_name):
        """
        Return True if database with provided name is exists in Redis, False - otherwise
        :param database_name: the name of the database
        :return: Boolean value
        """

        all_data_bases = DatabaseReaderTool.DATABASE_DICTIONARY.keys()
        return database_name in all_data_bases

    @staticmethod
    def _get_table_content(engine, database_name, table_name):
        """
        :param engine: dut engine
        :param database_name: database name
        :param table_name: a spastic table in the given database
        :return: all the content of the given table
        """
        cmd = "redis-cli -n {database_name} hgetall {table_name}".format(
            table_name='"' + table_name + '"', database_name=DatabaseReaderTool.get_database_id(database_name))

        output = engine.run_cmd(cmd)
        return output

    @staticmethod
    def get_all_table_names_in_database(engine, database_name, table_name_substring='.'):
        """
        :param engine: dut engine
        :param database_name: database name
        :param table_name_substring: full or partial table name
        :return: any database table that includes the substring, if table_name_substring is none we will return all the tables
        """
        result_obj = ResultObj(True, "")
        cmd = "redis-cli -n {database_name} keys * | grep {prefix}".format(
            database_name=DatabaseReaderTool.get_database_id(database_name), prefix=table_name_substring)
        output = engine.run_cmd(cmd)
        result_obj.returned_value = output.splitlines()
        return result_obj

    @staticmethod
    def get_database_id(database_name):
        """
        :param database_name: database name
        :return: database id in redis
        """
        return DatabaseReaderTool.DATABASE_DICTIONARY[database_name]

    @staticmethod
    def redis_cmd_output_parser(database_table):
        """
        Return the Dictionary format of the given table
        all the tables content displayed as follows
        input:
            1) "admin_status"
            2) "up"
            3) "alias"
            4) "swp2"
        in this function we are parsing the content to a dictionary
        output:
            {
            'admin_status': 'up',
            'alias"': 'swp2"
            }
        :param database_table: database table content
        :return: dictionary format of the given table
        """
        output_list = re.findall('"(.*)"\n', database_table + '\n')
        database_dic = {output_list[i]: output_list[i + 1] for i in range(0, len(output_list), 2)}
        return database_dic

    DATABASE_DICTIONARY = {DatabaseConst.APPL_DB_NAME: DatabaseConst.APPL_DB_ID,
                           DatabaseConst.ASIC_DB_NAME: DatabaseConst.ASIC_DB_ID,
                           DatabaseConst.COUNTERS_DB_NAME: DatabaseConst.COUNTERS_DB_ID,
                           DatabaseConst.CONFIG_DB_NAME: DatabaseConst.CONFIG_DB_ID,
                           DatabaseConst.STATE_DB_NAME: DatabaseConst.STATE_DB_ID
                           }
