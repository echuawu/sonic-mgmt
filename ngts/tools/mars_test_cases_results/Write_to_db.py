from dataclasses import dataclass
from .mars_data import SonicMarsData
from .Connect_to_MSSQL import ConnectMSSQL
from datetime import datetime


class MarsConnectDB(ConnectMSSQL):
    def __init__(self, server='mtlsqlprd', database='sonic_mars', username='sonic_db_user', password='Pa$$word01'):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.cursor = None
        self.conn = None
        self.data = None
        self.session_id = 0
        self.is_connected = False

    def write_json_to_db(self, mars_data_list):
        if self.conn is None:
            self.connect_db()

        self.connect_db()
        for row in mars_data_list:
            self.data = row
            self.insert_session()
        self.disconnect_db()

    def insert_session(self):

        insert = r"INSERT INTO [dbo].[mars_respond]([session_id], [mars_key_id] ,[mars_name] ,[mars_result],[allure_url]) VALUES (" + \
                 str(self.data.session_id) + ", '" + self.data.mars_key_id + "', '" + self.data.name + "', '" + \
                 self.data.result + "', '" + self.data.allure_url + "')"
        self.query_insert(insert)

    def clear_db(self):
        if self.conn is None:
            self.connect_db()

        clear_cmd = 'truncate table [Sonic_Mars].[dbo].[mars_respond]'
        self.execute_db_cmd(clear_cmd)
        self.disconnect_db()
