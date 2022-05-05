from ngts.tools.mars_test_cases_results.mars_data import SonicMarsData
import json
import re


class JsonHandler:
    def __init__(self, json_file):
        self.data = SonicMarsData()
        self.json_file = json_file
        self.all_data = []
        self.read_json_row()

    def read_json_row(self):
        for row in self.json_file:
            self.read_to_structure(row)

    def read_to_structure(self, json_row):

        self.data.session_id = json_row['session_id']
        self.data.mars_key_id = json_row['mars_key_id']
        self.data.name = json_row['name']
        self.data.result = json_row['result']
        self.data.allure_url = json_row['allure_url']
        self.data.skip_reason = json_row['skip_reason']
        self.all_data.append(self.data)
        self.data = None
        self.data = SonicMarsData()

    @staticmethod
    def fix_to_num(item):
        if isinstance(item, str):
            if item.isnumeric():
                return item
            else:
                return 'null'
        else:
            return item
