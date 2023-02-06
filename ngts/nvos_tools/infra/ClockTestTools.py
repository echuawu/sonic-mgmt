import allure
import logging
import yaml
from datetime import datetime, timedelta
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.tests_nvos.system.clock_and_timezone.ClockConsts import ClockConsts
import re


class ClockTestTools:

    @staticmethod
    def parse_yaml_to_dic(yaml_file_path):
        """
        @summary:
            Parse a given .yaml file into a dictionary
        @param yaml_file_path: path of the given .yaml file
        @return: ResultObj containing: True with parsed yaml as a dictionary, or False if parsing failed
        """
        with allure.step("Parsing .yaml file to dictionary"):
            logging.info("Parsing .yaml file to dictionary")
            with open(yaml_file_path, 'r') as file:
                logging.info("Reading provided .yaml file")
                dic = yaml.safe_load(file)
                res_obj = ResultObj(True, info="yaml parsing success", returned_value=dic)

                if not dic or len(dic.keys()) == 0:
                    logging.info('Failed to read .yaml file')
                    res_obj = ResultObj(False, info="yaml parsing fail")

            return res_obj

    @staticmethod
    def get_timezone_from_timedatectl_output(timedatectl_output):
        """
        @summary:
            Extract timezone value from 'timedatectl' raw output
        @return: timezone as a string
        """
        return OutputParsingTool.parse_timedatectl_cmd_output_to_dic(timedatectl_output)\
            .get_returned_value()[ClockConsts.TIMEDATECTL_TIMEZONE_FIELD_NAME].split(' ')[0]

    @staticmethod
    def get_datetime_from_timedatectl_output(timedatectl_output):
        """
        @summary:
            Extract date-time value from 'timedatectl' raw output
        @return: date-time as a string of the format 'YYYY-MM-DD hh:mm:ss'
        """
        return " ".join(OutputParsingTool.parse_timedatectl_cmd_output_to_dic(timedatectl_output)
                        .get_returned_value()[ClockConsts.TIMEDATECTL_DATE_TIME_FIELD_NAME].split(' ')[1:3])

    @staticmethod
    def get_datetime_from_show_system_output(show_system_output):
        """
        @summary:
            Extract date-time value from 'nv show system' output
        @return: date-time as a string of the format 'YYYY-MM-DD hh:mm:ss'
        """
        return OutputParsingTool.parse_json_str_to_dictionary(show_system_output) \
            .get_returned_value()[SystemConsts.DATE_TIME]

    @staticmethod
    def datetime_difference_in_seconds(dt1, dt2):
        """
        @summary:
            Calc difference (in seconds) between two given date-time values.
            both given date-time values are strings in the format 'YYYY-MM-DD hh:mm:ss'
        @param dt1: first date-time
        @param dt2: second date-time
        @return: date-times difference (in whole seconds)
        """
        # create datetime objects out of the date-time strings
        datetime_obj1 = datetime.fromisoformat(dt1)
        datetime_obj2 = datetime.fromisoformat(dt2)
        # subtracting datetime objects result a datetime.timedelta object that holds the diff, and return the diff in seconds
        return int(abs(datetime_obj1 - datetime_obj2).total_seconds())

    @staticmethod
    def is_time_format(s):
        """
        @summary:
            check if a given string is in the time format- "hh:mm:ss",
            and represents a valid time.
        @param s: the given string
        @return: [True/False]
        """
        time_regex = re.compile(r'\b(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])\b')
        return bool(time_regex.match(s))

    @staticmethod
    def is_datetime_format(s):
        """
        @summary:
            check if a given string is in the time format- "YYYY:MM:DD hh:mm:ss",
            and represents a valid time.
        @param s: the given string
        @return: [True/False]
        """
        time_regex = re.compile(r'\b((\d{4}-\d{2}-\d{2}) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9]))\b')
        return bool(time_regex.match(s))

    @staticmethod
    def alternate_capital_lower(s):
        """
        @summary:
            Convert a given string to capital-lower alternating form.
            example: "Hello world!" --> "HeLlO WoRlD!"
        @param s: given string
        @return: the converted string
        """
        result = []
        for i, c in enumerate(s):
            if not c.isalpha():
                result.append(c)
            elif i % 2 == 0:
                result.append(c.upper())
            else:
                result.append(c.lower())
        return "".join(result)
