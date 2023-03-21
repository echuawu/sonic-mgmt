import pytest
import datetime
import logging
import yaml
import allure
from ngts.nvos_constants.constants_nvos import OutputFormat, SystemConsts
from ngts.nvos_tools.infra.ClockTestTools import ClockTestTools
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.system.clock_and_timezone.ClockConsts import ClockConsts


@pytest.fixture(scope='session')
def valid_system_timezones():
    """
    @summary:
    Return valid system timezones, extracted from timezone.yaml file
    @return: list of valid system timezones (strings)
    """
    timezone_yaml_dic = ClockTestTools.parse_yaml_to_dic(ClockConsts.FILE_PATH_TIMEZONE_YAML).get_returned_value()
    valid_timezones = \
        timezone_yaml_dic['components']['schemas']['system-timezone-config']['properties']['timezone']['enum']

    return valid_timezones


@pytest.fixture(scope='session')
def system_obj(valid_system_timezones):
    """
    @summary:
    Return a System object
    """
    return System() if ClockConsts.DESIGN_FINISHED else MockSystem(valid_timezones=valid_system_timezones)


@pytest.fixture(scope='function')
def orig_timezone(system_obj):
    """
    @summary:
    Backup original timezone before a test, and restore it after
    @param system_obj: System object (from fixture)
    @yield: original timezone (before test)
    """
    with allure.step("Backup current timezone from 'nv show system'"):
        original_timezone = OutputParsingTool.parse_json_str_to_dictionary(system_obj.show()) \
            .get_returned_value()[SystemConsts.TIMEZONE]
        logging.info("Backup current timezone from 'nv show system'\torig timezone: {orig}".format(orig=original_timezone))

    yield original_timezone

    with allure.step("Restore timezone to original (after test)"):
        logging.info("Restore timezone to original (after test)\torig timezone: {orig}".format(orig=original_timezone))
        system_obj.timezone.set(original_timezone, apply=True).verify_result()


@pytest.fixture(scope='function')
def datetime_backup_restore(system_obj, valid_system_timezones, orig_timezone):
    """
    @summary:
        Fixture for fixing date-time value after a test.
        this fixture mainly uses orig_timezone fixture.
        the current fixture changes to another different timezone,
        then the test does whatever it needs to, and eventually the
        orig_timezone fixture will restore the timezone, which will fix
        the date-time value too.
    """
    with allure.step("Backup date-time: saving orig_datetime"):
        logging.info("Backup date-time: saving orig_datetime")
        orig_datetime = ClockTestTools.get_datetime_from_show_system_output(system_obj.show())
        logging.info("Backup date-time: saving orig_datetime - {dt}".format(dt=orig_datetime))

    with allure.step("Backup date-time: changing to another timezone"):
        logging.info("Backup date-time: changing to another timezone")
        different_timezone = RandomizationTool.select_random_value(valid_system_timezones,
                                                                   forbidden_values=[orig_timezone])\
            .get_returned_value()
        logging.info("Backup date-time: changing to another timezone\t{tz}".format(tz=different_timezone))
        system_obj.timezone.set(different_timezone, apply=True)

    yield orig_datetime

    with allure.step("Restore date-time: orig_timezone restores the timezone -> fixes the date-time too"):
        logging.info("Restore date-time: orig_timezone restores the timezone -> fixes the date-time too")
        system_obj.datetime_val = None  # <-- mock


class MockSystem(System):
    """
    dummy class replacement for System
    used for testing until design team finish feature implementation.
    """

    def __init__(self, valid_timezones):
        System.__init__(self)
        self.timezone_val = None
        self.datetime_val = None
        self.valid_timezones = valid_timezones

    def show(self, op_param="", output_format=OutputFormat.json):
        """
        return output of the show system output + timezone & date-time fields (taken from timedatectl)
        """
        logging.info("MOCK SYSTEM.SHOW: Run 'nv show system' and append to the output timezone & date-time fields")

        logging.info("MOCK SYSTEM.SHOW: Run 'nv show system'")
        # take 'nv show system' original output
        show_system_output = OutputParsingTool \
            .parse_json_str_to_dictionary(output_json=System.show(self)).get_returned_value()
        logging.info("MOCK SYSTEM.SHOW: 'nv show system' output: \n{output}".format(output=show_system_output))

        logging.info("MOCK SYSTEM.SHOW: Run 'timedatectl'")
        # take 'timedatectl' output
        timedatectl_raw_output = TestToolkit.engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD)
        logging.info("MOCK SYSTEM.SHOW: 'timedatectl' output: \n{output}"
                     .format(output=OutputParsingTool.parse_timedatectl_cmd_output_to_dic(timedatectl_raw_output)
                             .get_returned_value()))

        # extract timezone and date-time values from timedatectl
        timezone = self.timezone_val if self.timezone_val \
            else ClockTestTools.get_timezone_from_timedatectl_output(timedatectl_raw_output)    # <-- mock
        date_time = self.datetime_val if self.datetime_val \
            else ClockTestTools.get_datetime_from_timedatectl_output(timedatectl_raw_output)  # <-- mock
        logging.info("MOCK SYSTEM.SHOW: 'timedatectl' : timezone: {tz}\tdate-time: {dt}"
                     .format(tz=timezone, dt=date_time))

        # add timezone & date-time from timedatectl to the dummy nv show system output
        show_system_output[SystemConsts.TIMEZONE] = timezone
        show_system_output[SystemConsts.DATE_TIME] = date_time
        logging.info("MOCK SYSTEM.SHOW: final mock show output: {output}".format(output=show_system_output))

        return show_system_output
