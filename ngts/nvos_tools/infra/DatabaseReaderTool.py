import logging
from .ResultObj import ResultObj

logger = logging.getLogger()


class DatabaseReaderTool:

    @staticmethod
    def read_from_database(database_name, field_name):
        """
        Read the value of required field in specified database
        :param database_name: the name of the database
        :param field_name: the field name in database
        :return: ResultObj
        """
        result_obj = ResultObj()
        result_obj.result = True
        result_obj.info = ""

        if not database_name:
            result_obj.result = False
            result_obj.info = "Invalid value of database name"
        if not field_name:
            result_obj.result = False
            result_obj.info += "- Invalid value of database name"
        if not DatabaseReaderTool.database_exists_in_redis(database_name):
            result_obj.result = False
            result_obj.info += "{database_name} can't be found in Redis".format(database_name=database_name)
        if not DatabaseReaderTool.database_exists_in_redis(database_name):
            result_obj.result = False
            result_obj.info += "{field_name} can't be found in database {database_name}".format(field_name=field_name,
                                                                                                database_name=database_name)
        # TODO: TO IMPLEMENT
        result_obj.returned_value = ""
        return result_obj

    @staticmethod
    def field_exists_in_database(database_name, field_name):
        """
        Return True if the field name exists in specified database, False - otherwise
        :param database_name: the name of the database
        :param field_name: the name of the field
        :return: Boolean value
        """
        # TODO: TO IMPLEMENT
        return True

    @staticmethod
    def database_exists_in_redis(database_name):
        """
        Return True if database with provided name is exists in Redis, False - otherwise
        :param database_name: the name of the database
        :return: Boolean value
        """
        # TODO: TO IMPLEMENT
        return True
