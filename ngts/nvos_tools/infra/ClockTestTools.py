import random
import allure
import logging
import yaml
import datetime as dt
from datetime import datetime, timedelta
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.tests_nvos.system.clock_and_timezone.ClockConsts import ClockConsts
import re
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool


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

    @staticmethod
    def get_invalid_date():
        """
        @summary:
            Select an invalid date
            * invalid date - 'YYYY-MM-DD' , while 'YYYY' is any year, and 'MM-DD' compose a date which doesn't appear
            in the calendar.
        @return: invalid date as a string
        """
        # keep randomizing until got an invalid date
        while True:
            yyyy = str(random.randint(1000, 9999))
            month = random.randint(0, 99)
            mm = str(month) if month > 9 else "0" + str(month)
            day = random.randint(0, 99)
            dd = str(day) if day > 9 else "0" + str(day)
            random_date = yyyy + "-" + mm + "-" + dd
            if not ClockTestTools.is_valid_date(random_date):
                return random_date

    @staticmethod
    def is_valid_date(s):
        """
        @summary:
            Check if a given string represents a valid date
            * valid date - in 'YYYY-MM-DD' format , and the represented date exists in the calendar
        @param s: the given string to be checked
        @return: [True/False] whether the given string is a valid date or not
        """
        try:
            dt.date.fromisoformat(s)  # parse s, validate its format, and verify its a real date
        except ValueError:
            return False

        return True

    @staticmethod
    def get_invalid_time():
        """
        @summary:
            Select an invalid time
            * invalid date - 'hh:mm:ss' which isn't a real time in a day.
        @return: invalid time as a string
        """
        # keep randomizing until got an invalid time
        while True:
            hours = random.randint(0, 99)
            hh = str(hours) if hours > 9 else "0" + str(hours)
            minutes = random.randint(0, 99)
            mm = str(minutes) if minutes > 9 else "0" + str(minutes)
            seconds = random.randint(0, 99)
            ss = str(seconds) if seconds > 9 else "0" + str(seconds)
            random_time = hh + ":" + mm + ":" + ss
            if not ClockTestTools.is_valid_time(random_time):
                return random_time

    @staticmethod
    def is_valid_time(s):
        """
        @summary:
            Check if a given string represents a valid time
            * valid time - in 'hh:mm:ss' format , and the represented time exists in a day
        @param s: the given string to be checked
        @return: [True/False] whether the given string is a valid time or not
        """
        try:
            dt.time.fromisoformat(s)  # parse s, validate its format, and verify its a real time
        except ValueError:
            return False

        return True

    @staticmethod
    def generate_invalid_datetime_inputs():
        """
        @summary:
            Generate a list of invalid date-time inputs.
            The invalid inputs include several combinations of good/bad date, with good/bad time,
            composed together as an input string
        @return: list of strings (invalid inputs)
        """
        date_bad_format = RandomizationTool.get_random_string(length=10)  # bad format date - just random str
        date_not_exist = ClockTestTools.get_invalid_date()  # good format but invalid (doesn't really exist in the calendar)
        date_before_range = RandomizationTool.select_random_date(min_date="1111-01-01",
                                                                 max_date=SystemConsts.MIN_SYSTEM_DATE,
                                                                 forbidden_dates=[SystemConsts.MIN_SYSTEM_DATE]) \
            .get_returned_value()  # good format and valid, but not in allowed range (before)
        date_after_range = RandomizationTool.select_random_date(min_date=SystemConsts.MAX_SYSTEM_DATE,
                                                                max_date="2222-12-31",
                                                                forbidden_dates=[SystemConsts.MAX_SYSTEM_DATE]) \
            .get_returned_value()  # good format and valid, but not in allowed range (after)
        date_good = RandomizationTool.select_random_date().get_returned_value()  # valid from all aspects

        time_bad_format = RandomizationTool.get_random_string(length=8)  # bad format time - just random str
        time_not_exist = ClockTestTools.get_invalid_time()  # good format but invalid (doesn't really exist in a day)
        time_good = RandomizationTool.select_random_time().get_returned_value()  # valid from all aspects

        date_inputs = [date_bad_format, date_not_exist, date_before_range, date_after_range, date_good]
        time_inputs = [time_bad_format, time_not_exist, time_good]

        # all bad combinations
        bad_inputs = [""] + date_inputs  # should also test with empty input, and with date only
        for date_input in date_inputs:
            for time_input in time_inputs:
                if date_input == date_good and time_input == time_good:
                    continue  # this case composes a good date-time input -> skip it
                bad_inputs.append(date_input + " " + time_input)

        return bad_inputs
