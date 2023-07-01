import random
from ngts.tools.test_utils import allure_utils as allure
import logging
import yaml
import datetime as dt
from datetime import datetime, timedelta
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
import re
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.tests_nvos.system.clock.ClockConsts import ClockConsts
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType, NvosConst


class ClockTools:

    @staticmethod
    def parse_yaml_to_dic(yaml_file_path):
        """
        @summary:
            Parse a given .yaml file into a dictionary
        @param yaml_file_path: path of the given .yaml file
        @return: ResultObj containing: True with parsed yaml as a dictionary, or False if parsing failed
        """
        with allure.step("Parsing .yaml file to dictionary"):
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
        return OutputParsingTool.parse_linux_cmd_output_to_dic(timedatectl_output)\
            .get_returned_value()[ClockConsts.TIMEDATECTL_TIMEZONE_FIELD_NAME].split(' ')[0]

    @staticmethod
    def get_datetime_from_timedatectl_output(timedatectl_output):
        """
        @summary:
            Extract date-time value from 'timedatectl' raw output
        @return: date-time as a string of the format 'YYYY-MM-DD hh:mm:ss'
        """
        return " ".join(OutputParsingTool.parse_linux_cmd_output_to_dic(timedatectl_output)
                        .get_returned_value()[ClockConsts.TIMEDATECTL_DATETIME_FIELD_NAME].split(' ')[1:3])

    @staticmethod
    def get_datetime_from_show_system_output(show_system_output):
        """
        @summary:
            Extract date-time value from 'nv show system' raw output
        @return: date-time as a string of the format 'YYYY-MM-DD hh:mm:ss'
        """
        return OutputParsingTool.parse_json_str_to_dictionary(show_system_output) \
            .get_returned_value()[ClockConsts.DATETIME]

    @staticmethod
    def get_datetime_object_from_show_system_output(show_system_output):
        """
        @summary:
            Extract date-time value from 'nv show system' raw output
        @return: datetime object
        """
        orig_datetime = ClockTools.get_datetime_from_show_system_output(show_system_output)
        return datetime.strptime(orig_datetime, "%Y-%m-%d %H:%M:%S")

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
            if not ClockTools.is_valid_date(random_date):
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
    def is_valid_system_date(s, check_range=True):
        """
        @summary:
            Check if a given string represents a valid date,
                between ClockConsts.MIN_SYSTEM_DATE to ClockConsts.MAX_SYSTEM_DATE.
            * valid date - in 'YYYY-MM-DD' format , and the represented date exists in the calendar
        @param s: the given string to be checked
        @param check_range: whether to check if given s is a date in the valid system dates range
        @return: [True/False] whether the given string is a valid system date or not
        """
        try:
            s_date = dt.date.fromisoformat(s)  # parse s, validate its format, and verify its a real date
            if check_range:
                min_date = dt.date.fromisoformat(ClockConsts.MIN_SYSTEM_DATE)
                max_date = dt.date.fromisoformat(ClockConsts.MAX_SYSTEM_DATE)
                return min_date <= s_date <= max_date
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
            if not ClockTools.is_valid_time(random_time):
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
        date_not_exist = ClockTools.get_invalid_date()  # good format but invalid (doesn't really exist in the calendar)
        date_before_range = RandomizationTool.select_random_date(min_date="1111-01-01",
                                                                 max_date=ClockConsts.MIN_SYSTEM_DATE,
                                                                 forbidden_dates=[ClockConsts.MIN_SYSTEM_DATE]) \
            .get_returned_value()  # good format and valid, but not in allowed range (before)
        date_after_range = RandomizationTool.select_random_date(min_date=ClockConsts.MAX_SYSTEM_DATE,
                                                                max_date="2500-12-31",
                                                                forbidden_dates=[ClockConsts.MAX_SYSTEM_DATE]) \
            .get_returned_value()  # good format and valid, but not in allowed range (after)
        date_good = RandomizationTool.select_random_date().get_returned_value()  # valid from all aspects

        time_bad_format = RandomizationTool.get_random_string(length=8)  # bad format time - just random str
        time_not_exist = ClockTools.get_invalid_time()  # good format but invalid (doesn't really exist in a day)
        time_good = RandomizationTool.select_random_time().get_returned_value()  # valid from all aspects

        date_inputs = [date_bad_format, date_not_exist, date_before_range, date_after_range, date_good]
        time_inputs = [time_bad_format, time_not_exist, time_good]

        # all bad combinations
        bad_inputs = [""] + date_inputs + time_inputs  # should also test with empty input, and with date/time only
        for date_input in date_inputs:
            for time_input in time_inputs:
                if date_input == date_good and time_input == time_good:
                    continue  # this case composes a good date-time input -> skip it
                bad_inputs.append(date_input + " " + time_input)

        return bad_inputs

    @staticmethod
    def verify_timezone(engines, system_obj, expected_timezone, verify_with_linux=True):
        """
        @summary:
        Verify that timezone is as expected in 'nv show system' cmd

        @param engines: the engines object
        @param system_obj: System object
        @param expected_timezone: the expected timezone
        @param verify_with_linux:
            [True/False] verify also in 'timedatectl' cmd. this method should be called with False until design team
            finish feature implementation, because until then, there is a mock feature implementation,
            which doesn't touch the linux clock.
        """
        show_system_timezone = OutputParsingTool.parse_json_str_to_dictionary(system_obj.show()) \
            .get_returned_value()[ClockConsts.TIMEZONE]
        logging.info("Verify timezone in nv show:\nexpected timezone: {expected}\n'nv show system' timezone: {timezone}"
                     .format(expected=expected_timezone, timezone=show_system_timezone))
        ValidationTool.compare_values(show_system_timezone, expected_timezone).verify_result()

        if verify_with_linux:
            timedatectl_timezone = ClockTools \
                .get_timezone_from_timedatectl_output(engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD))
            logging.info("Verify timezone in timedatectl:\nexpected timezone: {expected}\n'timedatectl' timezone: {timezone}"
                         .format(expected=expected_timezone, timezone=timedatectl_timezone))
            ValidationTool.compare_values(timedatectl_timezone, expected_timezone).verify_result()

    @staticmethod
    def verify_same_datetimes(dt1, dt2, allowed_margin=ClockConsts.DATETIME_MARGIN):
        """
        @summary:
            Verify that two date-time values are the same (with small margin allowed).
            the allowed margin is up to a constant number of seconds, held in ClockConsts.DATETIME_MARGIN
            date-time values are given as strings in the format 'YYYY-MM-DD hh:mm:ss'
        @param dt1: 1st given date-time value
        @param dt2: 2nd given date-time value
        @param allowed_margin: the allowed margin (seconds)
        """
        if TestToolkit.tested_api == ApiType.OPENAPI:
            allowed_margin *= 2  # commands take a little longer with openapi infra, so allow larger margin

        with allure.step("Calculate diff (in seconds) between dt1: {dt1} and dt2 {dt2}".format(dt1=dt1, dt2=dt2)):
            diff = ClockTools.datetime_difference_in_seconds(dt1, dt2)

        with allure.step("Assert diff: {diff} < const {const}".format(diff=diff, const=allowed_margin)):
            assert diff < allowed_margin, \
                ("Difference (delta) between times in 'nv show system' and 'timedatectl' is too high! \n"
                 "Expected delta: less than '{expected}' seconds, Actual delta: '{actual}' seconds"
                 .format(expected=allowed_margin, actual=diff))

    @staticmethod
    def set_invalid_timezone_and_verify(bad_timezone, system_obj, engines, orig_timezone):
        """
        @summary:
            Sets a given invalid timezone, verifies error, and checks that timezone hasn't changed
        @param bad_timezone: the invalid timezone to be set
        @param system_obj: the System object
        @param engines: engines object
        @param orig_timezone: the original timezone (shouldn't be changed)
        """
        with allure.step("Set the bad timezone"):
            logging.info('Set the bad timezone "{btz}"'.format(btz=bad_timezone))
            res_obj = ClockTools.set_timezone(bad_timezone, system_obj, apply=True)

        with allure.step("Verify error occurred"):
            logging.info('Verify error occurred for the bad timezone "{btz}"'.format(btz=bad_timezone))
            res_obj.verify_result(should_succeed=False)

        with allure.step("Verify error message"):
            logging.info('Verify error message for the bad timezone "{btz}"'.format(btz=bad_timezone))
            expected_errors = \
                ClockConsts.ERR_INVALID_TIMEZONE if bad_timezone != '' or TestToolkit.tested_api == ApiType.OPENAPI \
                else ClockConsts.ERR_EMPTY_PARAM
            for msg in expected_errors:
                logging.info('Verify error msg for set timezone to "{}"\n'
                             'expect to contain: "{}"\n'
                             'actual error: "{}"'.format(bad_timezone, msg, res_obj.info))
                test_error_msg = "Failure: set system timezone failed but error message is not right.\n" \
                    "expected error message should contain: '{em}' ,\n" \
                    "actual error message: {aem}".format(em=msg,
                                                         aem=res_obj.info)
                ValidationTool.verify_substring_in_output(output=res_obj.info,
                                                          substring=msg,
                                                          err_message_in_case_of_failure=test_error_msg,
                                                          should_be_found=True)

        with allure.step("Verify timezone hasn't changed"):
            ClockTools.verify_timezone(engines, system_obj, expected_timezone=orig_timezone)

    @staticmethod
    def change_datetime_and_verify_error(bad_datetime, system_obj, engines, expected_err=None):
        """
        @summary:
            Sets a given invalid datetime, verifies error, and checks that datetime hasn't changed
        @param bad_datetime: the invalid datetime to be set
        @param system_obj: the System object
        @param engines: engines object
        @param expected_err: list of expected error messages (optional)
        """
        with allure.step("Save original date-time from show system"):
            orig_datetime = ClockTools.get_datetime_from_show_system_output(system_obj.show())
            logging.info("original date-time: '{odt}'".format(odt=orig_datetime))

        with allure.step("Try to set the datetime '{bdt}'".format(bdt=bad_datetime)):
            res_obj = system_obj.datetime.action_change(params=bad_datetime)

        with allure.step("Take date-time from show system and 'timedatectl (after the change command)"):
            show_datetime = ClockTools.get_datetime_from_show_system_output(system_obj.show())
            timedatectl_datetime = ClockTools.get_datetime_from_timedatectl_output(
                engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD))
            logging.info("show system date-time (after the change command): '{dt}'".format(dt=show_datetime))
            logging.info("timedatectl date-time (after the change command): '{dt}'".format(dt=timedatectl_datetime))

        with allure.step("Verify error occurred for datetime '{}'".format(bad_datetime)):
            logging.info("Verify error occurred for datetime '{}'\nresult object - result: {}\n"
                         "result object - info: {}".format(bad_datetime, res_obj.result, res_obj.info))
            res_obj.verify_result(should_succeed=False)

        with allure.step("Verify error message"):
            logging.info("Verify error message for '{bdt}'".format(bdt=bad_datetime))

            for msg in expected_err:
                logging.info('Verify error msg for change datetime to "{}"\n'
                             'expect to contain: "{}"\n'
                             'actual error: "{}"'.format(bad_datetime, msg, res_obj.info))
                test_error_msg = "Failure: set system datetime failed but error message is not right.\n" \
                    "expected error message should contain: '{em}' ,\n" \
                    "actual error message: {aem}".format(em=msg,
                                                         aem=res_obj.info)
                ValidationTool.verify_substring_in_output(output=res_obj.info,
                                                          substring=msg,
                                                          err_message_in_case_of_failure=test_error_msg,
                                                          should_be_found=True)

        with allure.step("Verify date-time hasn't changed"):
            ClockTools.verify_same_datetimes(orig_datetime, show_datetime)
            ClockTools.verify_same_datetimes(orig_datetime, timedatectl_datetime)

    @staticmethod
    def set_timezone(new_tz, system_obj, apply=True):
        """Set a given timezone

        :param new_tz: timezone to set (str)
        :param system_obj: System object
        :param apply: whether to apply the set or not, defaults to True
        :return: ResultObj from the set command
        """
        return system_obj.set(op_param_name=ClockConsts.TIMEZONE, op_param_value=new_tz, apply=apply)

    @staticmethod
    def unset_timezone(system_obj, apply=True):
        """Unset timezone

        :param system_obj: System object
        :param apply: whether to apply the unset or not, defaults to True
        :return: ResultObj from the unset command
        """
        return system_obj.unset(op_param=ClockConsts.TIMEZONE, apply=apply)

    @staticmethod
    def verify_show_and_log_times(system):
        """
        @summary:
            Verify that date-time in show system and timestamp of last system log line
            are the same time
        @param system: System object
        """
        with allure.step('Take date-time from show and from last log timestamp'):
            system.log.rotate_logs()
            show_output = system.show()
            logs = system.log.show_log(exit_cmd='q', expected_str=' ')

            last_log_datetime = ' '.join((re.findall(NvosConst.DATE_TIME_REGEX, logs)[-1]).split(' '))
            show_datetime = ClockTools.get_datetime_from_show_system_output(show_output)
            log_datetime = ClockTools.get_datetime_of_system_log_line(last_log_datetime)
            logging.info('show date-time: {}\nlogs date-time: {}'.format(show_datetime, log_datetime))

        with allure.step('Verify log timestamp similar to show date-time'):
            ClockTools.verify_same_datetimes(show_datetime, log_datetime)

    @staticmethod
    def get_datetime_of_system_log_line(log_line):
        """
        @summary:
            Return the timestamp from a log line in the format "YYYY-MM-DD hh:mm:ss"
        @param log_line: a line from system log
        @return: the timestamp (str)
        """
        with allure.step('Take timestamp from a single log line'):
            log_timestamp = log_line.split('.')[0].split(' ')  # remove .<microseconds>
            log_timestamp = ' '.join([substr for substr in log_timestamp if substr != ''])  # clean from double spaces
            logging.info('Take timestamp from a single log line: {}'.format(log_timestamp))

            current_year = datetime.now().year
            logging.info('Take current year: {}'.format(current_year))

            # convert date string to datetime object
            datetime_obj = datetime.strptime(log_timestamp, "%b %d %H:%M:%S")  # [.%f] if need .<microseconds> optional

            # replace year in datetime object
            new_datetime_obj = datetime_obj.replace(year=current_year)

            # format datetime object to string
            res = new_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
            logging.info('Result date-time: {}'.format(res))

            return res

    @staticmethod
    def add_hours_to_datetime(datetime_str, num_hours_to_add):
        """
        Given a datetime string, generate a new datetime string, which is + a given number of hours
        @param datetime_str: the given datetime (str)
        @param num_hours_to_add: number of hours (int)
        @return: new datetime string
        """
        with allure.step('Adding {} hours to the given datetime "{}"'.format(num_hours_to_add, datetime_str)):
            dt_obj = datetime.fromisoformat(datetime_str)
            dt_obj = dt_obj + timedelta(hours=num_hours_to_add)
            res = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            logging.info('Result new datetime: "{}"'.format(res))
            return res

    @staticmethod
    def dates_diff_in_days(date1, date2):
        """
        Given two datetime strings, calculate the diff between them (dt1 - dt2) in days
        @param date1: first datetime string
        @param date2: second datetime string
        @return: diff in days (int)
        """
        with allure.step('Calculate diff in days between "{}" and "{}"'.format(date1, date2)):
            date1_obj = datetime.fromisoformat(date1)
            date2_obj = datetime.fromisoformat(date2)
            return (date1_obj - date2_obj).days
