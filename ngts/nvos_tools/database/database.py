from ngts.nvos_tools.infra.DatabaseReaderTool import DatabaseReaderTool
from ngts.nvos_tools.infra.ResultObj import ResultObj


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
