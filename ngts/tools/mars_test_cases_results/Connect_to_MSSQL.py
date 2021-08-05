import pyodbc


class ConnectMSSQL:
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.cursor = None
        self.conn = None
        self.is_connected = False

    def __del__(self):
        if self.is_connected is True:
            self.disconnect_db()

    def connect_db(self):
        self.conn = pyodbc.connect(
            # Linux driver
            'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password)
        # Windows Driver
        # 'DRIVER={SQL Server Native Client 11.0};SERVER=' + self.server + ';DATABASE=' + self.database + ';UID=' + self.username + ';PWD=' + self.password)
        self.cursor = self.conn.cursor()
        self.is_connected = True

    def disconnect_db(self):

        if self.cursor is not None and self.is_connected is True:
            self.cursor.close()
        if self.conn is not None and self.is_connected is True:
            self.conn.close()
        self.is_connected = False

    def execute_db_cmd(self, cmd):
        self.cursor.execute(cmd)

    def get_or_insert_dim_id(self, get_query, insert_query):
        result_id: int
        try:
            self.cursor.execute(get_query)
            result_id = self.cursor.fetchone()[0]
            return result_id
        except Exception as e:

            if "NoneType" in str(e):
                self.cursor.execute(insert_query)
                self.conn.commit()
                self.cursor.execute(get_query)
                result_id = self.cursor.fetchone()[0]
                return result_id

            else:
                raise Exception("SQL query: " + get_query + " failed. error: " + str(e))

    def query_insert(self, insert_query, get_query=None):
        try:
            self.cursor.execute(insert_query)
            self.conn.commit()

            if get_query is not None:
                self.cursor.execute(get_query)
                result_id = self.cursor.fetchone()[0]
                return result_id
            else:
                return None
        except Exception as e:
            raise Exception("SQL insert query: " + insert_query + " failed. error: " + str(e))

    def query_scalar(self, scalar_query):
        self.cursor.execute(scalar_query)
        result_id = self.cursor.fetchone()[0]
        return result_id

    @staticmethod
    def str_or_null(string):
        if len(string) <= 0:
            return 'null'
        else:
            return ("'" + string + "'")

    @staticmethod
    def object_or_null(object):
        if object is not None:
            return object
        else:
            return 'null'
