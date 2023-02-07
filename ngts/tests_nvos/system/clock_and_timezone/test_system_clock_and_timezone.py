import logging
import datetime
import pytest
import allure
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ClockConsts import ClockConsts
from ngts.tests_nvos.system.clock_and_timezone.conftest import ClockTestTools
import random


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_show_system_contains_timezone_and_datetime(engines, system_obj):
    """
    @summary:
    Check that show system command's output contains timezone and date-time fields
        1. run show system
        2. verify timezone & date-time fields exist in output
        3. validate fields' values
    """
    logging.info("Starting test : test_show_system_contains_timezone_and_datetime")

    with allure.step('Run show system and timedatectl commands'):
        logging.info('Run show system and timedatectl commands')
        # run commands
        show_system_output_str = system_obj.show()
        timedatectl_output_str = engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD)
        # parse outputs to dicts
        show_system_output = OutputParsingTool \
            .parse_json_str_to_dictionary(show_system_output_str).get_returned_value()
        timedatectl_output = OutputParsingTool \
            .parse_timedatectl_cmd_output_to_dic(timedatectl_output_str).get_returned_value()

    with allure.step('Verify timezone & date-time fields exist in output'):
        logging.info('Verify timezone & date-time fields exist in output')
        tested_fields = [SystemConsts.TIMEZONE, SystemConsts.DATE_TIME]
        Tools.ValidationTool\
            .verify_field_exist_in_json_output(json_output=show_system_output, keys_to_search_for=tested_fields)\
            .verify_result()

    with allure.step("Validate timezone value"):
        logging.info("Validate timezone value")
        # verify that timezones are the same
        Tools.ValidationTool.compare_values(value1=show_system_output[SystemConsts.TIMEZONE],
                                            value2=ClockTestTools
                                            .get_timezone_from_timedatectl_output(timedatectl_output_str),
                                            should_equal=True).verify_result()

    with allure.step("Validate date-time value"):
        logging.info("Validate date-time value")
        # extract date-time value from outputs
        show_system_datetime = ClockTestTools.get_datetime_from_show_system_output(show_system_output_str)
        timedatectl_datetime = ClockTestTools.get_datetime_from_timedatectl_output(timedatectl_output_str)
        # verify both date-time values are the same
        verify_same_datetimes(show_system_datetime, timedatectl_datetime)


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_set_unset_system_timezone_ntp_off(engines, system_obj, valid_system_timezones, orig_timezone):
    # todo: what would disable ntp?
    """
    @summary:
    Check that system timezone set & unset commands work correctly with valid inputs
        1. Set new timezone to random timezone from timezone.yaml
        2. Verify new timezone is set in 'nv show system' and 'timedatectl'
        3. Unset timezone
        4. verify timezone returned to default in 'nv show system' and 'timedatectl'
    """

    with allure.step("Pick a random new timezone to set (from timezone.yaml)"):
        logging.info("Pick a random new timezone to set (from timezone.yaml)")
        new_timezone = RandomizationTool.select_random_value(list_of_values=valid_system_timezones,
                                                             forbidden_values=[orig_timezone],
                                                             work_with_copies=True).get_returned_value()

    with allure.step("Set the new timezone with 'nv set system timezone'"):
        logging.info("Set the new timezone with 'nv set system timezone'")
        system_obj.timezone.set(new_timezone, apply=True).verify_result()

    with allure.step("Verify new timezone in 'nv show system' and in 'timedatectl'"):
        logging.info("Verify new timezone in 'nv show system' and in 'timedatectl'")
        verify_timezone(engines, system_obj, expected_timezone=new_timezone, verify_with_linux=ClockConsts.DESIGN_FINISHED)

    with allure.step("Unet the timezone with 'nv unset system timezone'"):
        logging.info("Unet the timezone with 'nv unset system timezone'")
        system_obj.timezone.unset(apply=True).verify_result()

    with allure.step("Verify default timezone in 'nv show system' and in 'timedatectl'"):
        logging.info("Verify default timezone in 'nv show system' and in 'timedatectl'")
        verify_timezone(engines, system_obj, expected_timezone=ClockConsts.DEFAULT_TIMEZONE, verify_with_linux=ClockConsts.DESIGN_FINISHED)


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_action_change_date_time_ntp_off(engines, system_obj, datetime_backup_restore):  # todo: what would disable ntp?
    """
    @summary:
    Check that system date-time change action command work correctly with valid input of date and time
        1. Pick a random date and time
        2. Set new date and time with the action change command
        3. Verify new date-time in 'nv show system' and 'timedatectl'
    """

    with allure.step("Pick random new date-time to set"):
        logging.info("Pick random new date-time to set")
        new_datetime = RandomizationTool.select_random_datetime().get_returned_value()

    with allure.step("Set the new date-time with 'nv action change system date-time'"):
        logging.info("Set the new date-time with 'nv action change system date-time'")
        system_obj.datetime.action_change_datetime(params=new_datetime).verify_result()  # todo: implement System.DateTime.action_change_datetime()

    with allure.step("Run 'nv show system' and 'timedatectl' immediately to verify date-time changed"):
        logging.info("Run 'nv show system' and 'timedatectl' immediately to verify date-time changed")
        show_system_output_str = system_obj.show()
        timedatectl_output_str = engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD)

    with allure.step("Verify date-time"):
        logging.info("Verify date-time")
        show_system_datetime = ClockTestTools.get_datetime_from_show_system_output(show_system_output_str)
        verify_same_datetimes(new_datetime, show_system_datetime)
        if ClockConsts.DESIGN_FINISHED:
            timedatectl_datetime = ClockTestTools.get_datetime_from_timedatectl_output(timedatectl_output_str)
            verify_same_datetimes(new_datetime, timedatectl_datetime)


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_action_change_time_only_ntp_off(engines, system_obj, datetime_backup_restore):  # todo: what would disable ntp?
    """
    @summary:
        Check that system date-time change action command work correctly with valid input of time only
        example: 'nv action change system date-time' should allow parameter 'hh:mm:ss' only

        Test steps:
        1. Pick a random time
        2. Set new time with the action change command
        3. Verify new time in 'nv show system' and 'timedatectl'
    """

    with allure.step("Pick random new time to set"):
        logging.info("Pick random new time to set")
        new_time = RandomizationTool.select_random_time().get_returned_value()
        new_datetime = datetime_backup_restore.split(' ')[0] + ' ' + new_time

    with allure.step("Set the new time with 'nv action change system date-time'"):
        logging.info("Set the new time with 'nv action change system date-time'")
        system_obj.datetime.action_change_datetime(params=new_time).verify_result()  # todo: implement System.DateTime.action_change_datetime()

    with allure.step("Run 'nv show system' and 'timedatectl' immediately to verify date-time changed"):
        logging.info("Run 'nv show system' and 'timedatectl' immediately to verify date-time changed")
        show_system_output_str = system_obj.show()
        timedatectl_output_str = engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD)

    with allure.step("Verify date-time"):
        logging.info("Verify date-time")
        show_system_datetime = ClockTestTools.get_datetime_from_show_system_output(show_system_output_str)
        verify_same_datetimes(new_datetime, show_system_datetime)
        if ClockConsts.DESIGN_FINISHED:
            timedatectl_datetime = ClockTestTools.get_datetime_from_timedatectl_output(timedatectl_output_str)
            verify_same_datetimes(new_datetime, timedatectl_datetime)


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_set_system_invalid_timezone_ntp_off_error_flow(engines, system_obj, valid_system_timezones, orig_timezone):
    # todo: what would disable ntp?
    """
    @summary:
        Check that system timezone set command works correctly with invalid inputs
        * invalid - not exist in timezone.yaml file

        Main Steps:
            1. Set new timezone to random invalid timezone
            2. Verify error
            3. verify timezone hasn't changed (still the original one) in 'nv show system' and 'timedatectl'
    """
    # try to set random strings of varying length (also len 0 -> "")
    with allure.step("Pick random strings of different lengths as bad timezone"):
        logging.info("Pick random strings of different lengths as bad timezone")
    for n in range(0, 10, 3):
        with allure.step("Pick a random string of length {n} as bad timezone".format(n=n)):
            logging.info("Pick a random string of length {n} as bad timezone".format(n=n))
            bad_timezone = RandomizationTool.get_random_string(length=n)

        set_invalid_timezone_and_verify(bad_timezone, system_obj, engines, orig_timezone)

    # try to change random existing timezones from timezone.yaml and set them
    with allure.step("Pick 3 random timezone from timezone.yaml and change them to test case sensitivity"):
        logging.info("Pick 3 random timezone from timezone.yaml and change them to test case sensitivity")
        random_timezones = RandomizationTool.select_random_values(list_of_values=valid_system_timezones,
                                                                  number_of_values_to_select=3).get_returned_value()
        bad_timezones = list(map(lambda s: ClockTestTools.alternate_capital_lower(s), random_timezones))

    for bad_timezone in bad_timezones:
        set_invalid_timezone_and_verify(bad_timezone, system_obj, engines, orig_timezone)


@pytest.mark.system
@pytest.mark.simx
@pytest.mark.clock
def test_change_invalid_datetime_ntp_off_error_flow(engines, system_obj):
    # todo: what would disable ntp?
    """
    @summary:
        Check that system date-time change action command works correctly (error) with invalid inputs.
        * valid input can be any parameter in the format "YYYY-MM-DD hh:mm:ss" or just "hh:mm:ss",
            while both date ("YYYY-MM-DD") and time ("hh:mm:ss") define a valid date and time, which exists in the
            calendar year, and is in the 'allowed range'
        * the 'allowed range' is between SystemConsts.MIN_SYSTEM_DATETIME to SystemConsts.MAX_SYSTEM_DATETIME

        Main Steps:
            1. Try to change date-time with several invalid inputs
            2. verify error
            3. verify that date-time hasn't changed
    """
    with allure.step("Generate several invalid inputs for 'nv action change system date-time"):
        logging.info("Generate several invalid inputs for 'nv action change system date-time")
        bad_inputs = ClockTestTools.generate_invalid_datetime_inputs()
        logging.info("Generated invalid date-time inputs:\n{bi}".format(bi=bad_inputs))

    for bad_datetime in bad_inputs:
        set_invalid_datetime_and_verify(bad_datetime, system_obj, engines)


def verify_timezone(engines, system_obj, expected_timezone, verify_with_linux=True):
    """
    @summary:
    Verify that timezone is as expected in 'nv show system' cmd

    @param engines: the engines object (from fixture)
    @param system_obj: System object (from fixture)
    @param expected_timezone: the expected timezone
    @param verify_with_linux:
        [True/False] verify also in 'timedatectl' cmd. this method should be called with False until design team
        finish feature implementation, because until then, there is a mock feature implementation,
        which doesn't touch the linux clock.
    """
    show_system_timezone = OutputParsingTool.parse_json_str_to_dictionary(system_obj.show()) \
        .get_returned_value()[SystemConsts.TIMEZONE]
    logging.info("Verify nv show: expected timezone: {expected}\t'nv show system' timezone: {timezone}"
                 .format(expected=expected_timezone, timezone=show_system_timezone))
    Tools.ValidationTool.compare_values(show_system_timezone, expected_timezone).verify_result()

    if verify_with_linux:
        timedatectl_timezone = OutputParsingTool \
            .parse_timedatectl_cmd_output_to_dic(engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD)) \
            .get_returned_value()[ClockConsts.TIMEDATECTL_TIMEZONE_FIELD_NAME]
        logging.info("Verify timedatectl: expected timezone: {expected}\t'nv show system' timezone: {timezone}"
                     .format(expected=expected_timezone, timezone=timedatectl_timezone))
        Tools.ValidationTool.compare_values(timedatectl_timezone, expected_timezone).verify_result()


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
    with allure.step("Calculate diff (in seconds) between dt1: {dt1} and dt2 {dt2}".format(dt1=dt1, dt2=dt2)):
        logging.info("Calculate diff (in seconds) between dt1: {dt1} and dt2 {dt2}".format(dt1=dt1, dt2=dt2))
        diff = ClockTestTools.datetime_difference_in_seconds(dt1, dt2)

    with allure.step("Assert diff: {diff} < const {const}".format(diff=diff, const=ClockConsts.DATETIME_MARGIN)):
        logging.info("Assert diff: {diff} < const {const}".format(diff=diff, const=ClockConsts.DATETIME_MARGIN))
        assert diff < ClockConsts.DATETIME_MARGIN, \
            ("Difference (delta) between times in 'nv show system' and 'timedatectl' is too high! \n"
             "Expected delta: less than '{expected}' seconds, Actual delta: '{actual}' seconds"
             .format(expected=allowed_margin, actual=diff))


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
        logging.info("Set the bad timezone ( {btz} )".format(btz=bad_timezone))
        res_obj = system_obj.timezone.set(bad_timezone, apply=True)

    with allure.step("Verify error occurred"):
        logging.info("Verify error occurred for the bad timezone ( {btz} )".format(btz=bad_timezone))
        res_obj.verify_result(should_succeed=False)

    with allure.step("Verify error message"):
        logging.info("Verify error message for the bad timezone ( {btz} )".format(btz=bad_timezone))
        test_error_msg = "Failure: set system timezone failed but error message is not right.\n" \
                         "expected error message should contain: '{em}' ,\n" \
                         "actual error message: {aem}".format(em=ClockConsts.ERR_MSG_INVALID_TIMEZONE,
                                                              aem=res_obj.info)
        ValidationTool.verify_substring_in_output(output=res_obj.info,
                                                  substring=ClockConsts.ERR_MSG_INVALID_TIMEZONE,
                                                  err_message_in_case_of_failure=test_error_msg,
                                                  should_be_found=True)

    with allure.step("Verify timezone hasn't changed"):
        logging.info("Verify timezone hasn't changed")
        verify_timezone(engines, system_obj, expected_timezone=orig_timezone,
                        verify_with_linux=ClockConsts.DESIGN_FINISHED)


def set_invalid_datetime_and_verify(bad_datetime, system_obj, engines):
    """
    @summary:
        Sets a given invalid datetime, verifies error, and checks that datetime hasn't changed
    @param bad_datetime: the invalid datetime to be set
    @param system_obj: the System object
    @param engines: engines object
    """
    with allure.step("Save original date-time from show system"):
        logging.info("Save original date-time from show system")
        orig_datetime = ClockTestTools.get_datetime_from_show_system_output(system_obj.show())
        logging.info("original date-time: {odt}".format(odt=orig_datetime))

    with allure.step("Set the bad datetime"):
        logging.info("Set the bad datetime ( {bdt} )".format(bdt=bad_datetime))
        res_obj = system_obj.datetime.action_change_datetime(params=bad_datetime)

    with allure.step("Take date-time from show system and 'timedatectl (after the change command)"):
        logging.info("Take date-time from show system and 'timedatectl (after the change command)")
        show_datetime = ClockTestTools.get_datetime_from_show_system_output(system_obj.show())
        timedatectl_datetime = ClockTestTools.get_datetime_from_timedatectl_output(
            engines.dut.run_cmd(ClockConsts.TIMEDATECTL_CMD))
        logging.info("show system date-time (after the change command): {dt}".format(dt=show_datetime))
        logging.info("timedatectl date-time (after the change command): {dt}".format(dt=timedatectl_datetime))

    with allure.step("Verify error occurred"):
        logging.info("Verify error occurred for the bad datetime ( {bdt} )".format(bdt=bad_datetime))
        res_obj.verify_result(should_succeed=False)

    with allure.step("Verify error message"):
        logging.info("Verify error message for the bad datetime ( {bdt} )".format(bdt=bad_datetime))
        test_error_msg = "Failure: set system datetime failed but error message is not right.\n" \
                         "expected error message should contain: '{em}' ,\n" \
                         "actual error message: {aem}".format(em=ClockConsts.ERR_MSG_INVALID_DATETIME,
                                                              aem=res_obj.info)
        ValidationTool.verify_substring_in_output(output=res_obj.info,
                                                  substring=ClockConsts.ERR_MSG_INVALID_DATETIME,
                                                  err_message_in_case_of_failure=test_error_msg,
                                                  should_be_found=True)

    with allure.step("Verify date-time hasn't changed"):
        logging.info("Verify date-time hasn't changed")
        verify_same_datetimes(orig_datetime, show_datetime)
        if ClockConsts.DESIGN_FINISHED:
            verify_same_datetimes(orig_datetime, timedatectl_datetime)
