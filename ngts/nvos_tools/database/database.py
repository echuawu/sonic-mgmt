import logging

from ngts.nvos_tools.infra.DatabaseReaderTool import DatabaseReaderTool
from ngts.nvos_tools.infra.ResultObj import ResultObj

logger = logging.getLogger()


class Database:
    def __init__(self, name, id, tables):
        self.name = name
        self.id = id
        self.tables = tables

    def verify_num_of_tables_in_database(self, dut_engine):
        """
        validate the redis includes all expected tables
        :param dut_engine: ssh dut engine
        Return result_obj with True result if all tables exists, False and a relevant info if one or more tables are missing
        """
        result_obj = ResultObj(True, "")
        for table_name, num_of_tables in self.tables.items():
            output = DatabaseReaderTool.get_all_table_names_in_database(dut_engine, self.name, table_name).returned_value
            if len(output) not in num_of_tables:
                result_obj.result = False
                result_obj.info += "in {database_name} one or more tables are missing with prefix {table_name}\n" \
                    .format(database_name=self.name, table_name=table_name)
        return result_obj

    def verify_filed_value_in_all_tables(self, dut_engine, table_name_substring, field_name, expected_value):
        """

        :param dut_engine: the dut engine
        :param table_name_substring: substring of tables list we want to verify there values
        :param field_name: the field name in the table
        :param expected_value: an expected value for the field
        :return: result_obj
        """
        result_obj = ResultObj(True, "")
        output = DatabaseReaderTool.get_all_table_names_in_database(dut_engine, self.name,
                                                                    table_name_substring).returned_value
        for table_name in output:
            obj = DatabaseReaderTool.read_from_database(self.name, dut_engine, table_name, field_name)
            if obj.verify_result() != expected_value:
                result_obj.result = False
                logger.error("{field_name} value in {table_name} DB {database_name} is {obj_value} not {expected_value}"
                             " as expected \n".format(field_name=field_name, table_name=table_name,
                                                      database_name=self.name, obj_value=obj.returned_value,
                                                      expected_value=expected_value))
        if not result_obj.result:
            result_obj.info = "one or more fields are not as expected"
        return result_obj
