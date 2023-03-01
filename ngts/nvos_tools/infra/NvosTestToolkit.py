from ngts.nvos_constants.constants_nvos import ApiType, NvosConst
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.openapi.openapi_general_clis import OpenApiGeneralCli
import logging
import allure
import re
from datetime import datetime

logger = logging.getLogger()


class TestToolkit:
    tested_ports = None
    engines = None
    tested_api = ApiType.NVUE
    GeneralApi = {ApiType.NVUE: NvueGeneralCli, ApiType.OPENAPI: OpenApiGeneralCli}

    @staticmethod
    def update_tested_ports(tested_ports):
        with allure.step("Update tested ports in TestTookit"):
            logging.info("Testes port/s: " + str(tested_ports))
            TestToolkit.tested_ports = tested_ports

    @staticmethod
    def update_engines(engines):
        with allure.step("Update engines object in TestTookit"):
            TestToolkit.engines = engines

    @staticmethod
    def update_apis(api_type):
        with allure.step("Update api in TestTookit to " + api_type):
            TestToolkit.tested_api = api_type
            logging.info("API updated to: " + api_type)

    @staticmethod
    def update_port_output_dictionary(port_obj, engine=None):
        with allure.step("Run 'show' command and update output dictionary"):
            logging.info("Run 'show' command and update output dictionary")
            port_obj.update_output_dictionary(engine if engine else TestToolkit.engines.dut)

    @staticmethod
    def date_time_string_to_datetime_obj(date_time_str):
        """
        return datetime object from date time string
        example : date_time_string_to_datetime_obj(Feb 23 10:31:21)  => 2023-02-23 10:31:21
        """
        datetime_obj = datetime.strptime(date_time_str, "%b %d %H:%M:%S")
        current_year = datetime.now().year
        datetime_obj = datetime_obj.replace(year=current_year)
        return datetime_obj

    @staticmethod
    def get_date_and_time_from_line(line):
        date_time = re.findall(NvosConst.DATE_TIME_REGEX, line)
        assert len(date_time) > 0, "Didn\'t find date and time regex {} in line: {}".format(NvosConst.DATE_TIME_REGEX, line)
        return TestToolkit.date_time_string_to_datetime_obj(date_time[0].split(".")[0])

    @staticmethod
    def search_line_after_a_specific_date_time(line_to_search, text, since_date_time):
        """
        search line in the txt and return just the lines that find that happen after a specific time
        :param line_to_search: regex of line to search
        :param text: txt to search in
        :param since_date_time: datatime object
        :return: list of the relevant line appearance
        """
        lines = re.findall(line_to_search, text)
        res = []
        for line in lines:
            line_date_time = TestToolkit.get_date_and_time_from_line(line)
            if since_date_time < line_date_time:
                res.append(line)
        return res
