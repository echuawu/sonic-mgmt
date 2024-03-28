import os
import cx_Oracle as cx
import pandas as pd

dwhprod_user = os.getenv("DWHPROD_USER")
dwhprod_password = os.getenv("DWHPROD_PASSWORD")
dwhprod_database_name = os.getenv("DWHPROD_DATABASE_NAME")


class OracleDb:

    def __init__(self):
        if not all([dwhprod_user, dwhprod_password, dwhprod_database_name]):
            raise Exception("No Credentials found for the database 'dwhprod'")
        self.db = cx.connect(dwhprod_user, dwhprod_password, dwhprod_database_name)
        self.cursor = self.db.cursor()

    def __del__(self):
        self.db.close()
        self.cursor = None
        self.db = None

    def run_proc(self, proc_name, proc_param):
        self.cursor.callproc(proc_name, [proc_param])
        self.db.commit()

    def select_into_df(self, query):
        result = pd.read_sql(query, con=self.db)
        return result
