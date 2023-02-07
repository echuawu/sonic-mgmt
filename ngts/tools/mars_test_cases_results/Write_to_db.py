from dataclasses import dataclass
from .mars_data import SonicMarsData
from .Connect_to_MSSQL import ConnectMSSQL
from datetime import datetime
import logging
logger = logging.getLogger()


class MarsConnectDB(ConnectMSSQL):
    def __init__(self, server, database, username, password):
        ConnectMSSQL.__init__(self, server, database, username, password)
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

        insert = r"INSERT INTO [dbo].[mars_respond]([session_id], [mars_key_id] ,[mars_name] ,[mars_result],[allure_url], [skip_reason], [dump_info]) VALUES (" + \
                 str(self.data.session_id) + ", '" + self.data.mars_key_id + "', '" + self.data.name + "', '" + \
                 self.data.result + "', '" + self.data.allure_url + "','" + self.data.skip_reason + "','" + str(self.data.dump_info) + "' )"
        logger.info('Inserting: {} to MARS SQL DB'.format(insert))
        try:
            self.query_insert(insert)
        except Exception as e:
            logger.error(e)

    def clear_db(self):
        if self.conn is None:
            self.connect_db()

        clear_cmd = 'truncate table [' + self.database + '].[dbo].[mars_respond]'
        self.execute_db_cmd(clear_cmd)
        self.disconnect_db()
