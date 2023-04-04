import datetime
import random
import re
import os
import time
import allure
import pexpect
import logging
import pytest
import json
from ngts.tests_nvos.general.security.test_login_ssh_notification.constants import LoginSSHNotificationConsts
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.system.System import System
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.tests_nvos.general.security.conftest import ssh_to_device_and_retrieve_raw_login_ssh_notification, create_ssh_login_engine


logger = logging.getLogger(__name__)


def convert_linux_date_output_to_datetime_object(linux_date_string):
    '''
    @summary: this helper function will extract time and date and
    return tuple ( date , time )
    :param output: output to extract the time and date from
    :param date_regex: date regex to catch
    :param time_regex: time regex to catch
    '''
    date_format = "%a %b %d %H:%M:%S %Z %Y"
    date = datetime.datetime.strptime(linux_date_string, date_format)
    return date


def parse_ssh_login_notification(dut_ip, username, password):
    '''
    @summary: in this function we will parse the login ssh notification parameters
    when creating ssh connection to switch and extracting all the parameters
    this includes:
        1.	Last successful login date/time and location – (for all users)
        2.	Number of unsuccessful logins since last successful login – (per user)
        3.	Last unsuccessful date/time and location (terminal or IP) – (per user)
        4.	Changes to user's account since last login (password, role, group, etc) – (per user)
        5.	Number of total successful logins since a date/time – (user with admin capabilities)

    :return: will return a dictionary of each parameter, e.g.:
    {
        'last_successful_login_date' : datetime bject of cuurent date,
        'last_successful_login_ip' : '10.7.34.240',
        'last_unsuccessful_login_date' : datetime bject of cuurent date,
        'last_unsuccessful_login_ip' : '10.7.34.240',
        'number_of_unsuccessful_attempts_since_last_login', '4',
        'record_period' : '5',
        'number_of_successful_connections_in_the_last_record_period' : '100',
        'password_changed_message' : None, (None - means didn't appear in the notification)
        'role_changed_message' : None
    }
    '''
    result = {}

    notification_login_message = ssh_to_device_and_retrieve_raw_login_ssh_notification(dut_ip,
                                                                                       username,
                                                                                       password)
    for key, regex in LoginSSHNotificationConsts.LOGIN_SSH_NOTIFICATION_REGEX_DICT.items():
        match = re.findall(regex, notification_login_message)
        if regex == LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_DATE_REGEX:
            # there will be always output to catch it
            result[LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_DATE] = convert_linux_date_output_to_datetime_object(match[0])
        elif regex == LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_DATE_REGEX:
            # not always the message will appear
            if len(match) != 0:
                result[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_DATE] = convert_linux_date_output_to_datetime_object(match[0])
            else:
                result[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_DATE] = None
        else:
            result[key] = match[0] if match else None

    return result


def change_username_password(engines, username, curr_password, new_password):
    '''
    @summary: in this test case we want to validate password message appearance
    after changing it in the second ssh login notification
    :param username: username
    :param curr_password: current password for username
    :param new_password: new password to change to
    '''
    with allure.step("Changing password for user: {}".format(username)):
        logger.info("Changing password for user: {}\n"
                    "Current password: {}\n"
                    "New password proposed: {}".format(username, curr_password, new_password))

    # create system class
    system = System()
    system.aaa.user.set_username(username=username)
    system.aaa.user.set(DefaultConnectionValues.PASSWORD, new_password, apply=True, ask_for_confirmation=True)
    logger.info("Sleeping {} secs to allow password change".format(DefaultConnectionValues.PASSWORD_UPDATE_TIME))
    time.sleep(DefaultConnectionValues.PASSWORD_UPDATE_TIME)


def validate_ssh_login_notifications_default_fields(engines, login_source_ip_address, username, password, capability,
                                                    check_password_change_msg=False,
                                                    check_role_change_msg=False,
                                                    expected_login_record_period=None,
                                                    last_successful_login=None):
    '''
    @summary: in this test case we want to validate the output of default fields
    of login ssh notification, where we want to check the following parameters:
        [
            'last_successful_login_date',
            'last_successful_login_time',
            'last_successful_login_ip',
            'last_unsuccessful_login_date',
            'last_unsuccessful_login_time',
            'last_unsuccessful_login_ip',
            'number_of_unsuccessful_attempts_since_last_login',
            'record_period',
            'number_of_successful_connections_in_the_last_record_period'
        ]
    :param engines: fixture containing all engines
    :param login_source_ip_address: ip address initiating the ssh connection in the test
    :param username: username to connect with to switch
    :param password: the password for username
    :param capability: the username capability, could be one of [admin, monitor]
    :param check_password_change_msg: if set true will check if password message appeared
    :param check_role_change_msg: if set true will check if role message appeared
    :param expected_login_record_period: if not None, will validate same value as the notification value
    :param last_successful_login: datetime object of the time since last successful login
    '''
    random_number_of_connection_fails = random.randint(5, 15)
    with allure.step("Fail connecting to device {}".format(random_number_of_connection_fails)):
        logger.info("Fail connecting to device {}".format(random_number_of_connection_fails))
        logger.info("Attempting {} wrong password attempts".format(random_number_of_connection_fails))
        for index in range(random_number_of_connection_fails):
            try:
                connection = create_ssh_login_engine(engines.dut.ip, username)
                connection.expect(DefaultConnectionValues.PASSWORD_REGEX)
                random_password = RandomizationTool.get_random_string(random.randint(LoginSSHNotificationConsts.PASSWORD_MIN_LEN,
                                                                                     LoginSSHNotificationConsts.PASSWORD_MAX_LEN))
                logger.info("Iteration {} - connecting using random password: {}".format(index, random_password))
                connection.sendline(random_password)
                connection.expect("[Pp]ermission denied")
            finally:
                connection.close()

    with allure.step("Connect for the second time to switch and store details"):
        logger.info("Connect for the second time to switch and store details")
        second_login_notification_message = parse_ssh_login_notification(engines.dut.ip, username,
                                                                         password)

    if last_successful_login:
        with allure.step("Validating same date"):
            logger.info("Validating same date")
            time_delta_seconds = (abs(second_login_notification_message[LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_DATE] - last_successful_login)).seconds
            assert time_delta_seconds < LoginSSHNotificationConsts.MAX_TIME_DELTA_BETWEEEN_CONNECTIONS, "Time Delta between current time and successful login ssh time is not under 120 secs, \n" \
                                                                                                        "The time difference is {}".format(time_delta_seconds)
            time_delta_seconds = (second_login_notification_message[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_DATE] - last_successful_login).seconds
            assert time_delta_seconds < LoginSSHNotificationConsts.MAX_TIME_DELTA_BETWEEEN_CONNECTIONS, "Time Delta between current time and successful login ssh time is not under 120 secs, \n" \
                                                                                                        "The time difference is {}".format(time_delta_seconds)

    with allure.step("Validating {} failed attempts in the second connection".format(random_number_of_connection_fails)):
        logger.info("Validating {} failed attempts in the second connection".format(random_number_of_connection_fails))
        assert int(second_login_notification_message[LoginSSHNotificationConsts.NUMBER_OF_UNSUCCESSFUL_ATTEMPTS_SINCE_LAST_LOGIN]) == random_number_of_connection_fails, \
            "Number of failed connections is not the same, \n" \
            "Expected : {} \n" \
            "Actually : {}".format(second_login_notification_message[LoginSSHNotificationConsts.NUMBER_OF_UNSUCCESSFUL_ATTEMPTS_SINCE_LAST_LOGIN],
                                   random_number_of_connection_fails)

    with allure.step("Validating IP address is same as this test IP address"):
        logger.info("Validating IP address is same as this test IP address")
        with allure.step("Validating successful IP address"):
            logger.info("Validating successful IP address")
            assert second_login_notification_message[LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_IP] == login_source_ip_address, \
                "Not same login IP Address, \n" \
                "Expected : {} \n" \
                "Actual : {}".format(second_login_notification_message[LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_IP],
                                     login_source_ip_address)
        with allure.step("Validating unsuccessful IP address"):
            logger.info("Validating unsuccessful IP address")
            assert second_login_notification_message[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_IP] == login_source_ip_address, \
                "Not same unsuccessful login IP Address\n" \
                "Expected : {} \n" \
                "Actual : {}".format(
                    second_login_notification_message[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_IP],
                    login_source_ip_address)

    with allure.step("Validating password or capability changes"):
        logger.info("Validating password or capability changes")
        if check_password_change_msg:
            assert second_login_notification_message[LoginSSHNotificationConsts.PASSWORD_CHANGED_MESSAGE] is not None, \
                "Password change message did not appear when it should"
        else:
            assert second_login_notification_message[LoginSSHNotificationConsts.PASSWORD_CHANGED_MESSAGE] is None, \
                "Password change message appeared when it should not"

        if check_role_change_msg:
            assert second_login_notification_message[LoginSSHNotificationConsts.ROLE_CHANGED_MESSAGE] is not None, \
                "Capability change message did not appear when it should"
        else:
            assert second_login_notification_message[LoginSSHNotificationConsts.ROLE_CHANGED_MESSAGE] is None, \
                "Capability change message appeared when it should not"

    # if expected_login_record_period:
    #     with allure.step("Validating login-record-period value"):
    #         logger.info("Validating login-record-period value")
    #         assert second_login_notification_message[LoginSSHNotificationConsts.RECORD_PERIOD] == str(expected_login_record_period), \
    #             "Not same login record period value, expected: {}, actual: {}".format(expected_login_record_period,
    #                                                                                   second_login_notification_message[LoginSSHNotificationConsts.RECORD_PERIOD])


def get_current_time_in_secs():
    '''
    @summary: in this function we convert the current date to seconds
    :return:
    '''
    output = os.popen("date").read()
    current_date_string = re.findall(LoginSSHNotificationConsts.LINUX_DATE_REGEX, output)[0]
    logger.info("Linux date is {}".format(current_date_string))
    current_date = convert_linux_date_output_to_datetime_object(current_date_string)
    return current_date


@pytest.mark.simx
@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_ssh_login_notifications_default_fields_admin(engines, login_source_ip_address):
    '''
    @summary: in this test case we want to validate admin username ssh login notification
    '''
    with allure.step("Connecting to switch before validation to clear all failed messages"):
        logger.info("Connecting to switch before validation to clear all failed messages")
        successful_login_time = get_current_time_in_secs()
        ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip,
                                                              username=DefaultConnectionValues.ADMIN,
                                                              password=DefaultConnectionValues.DEFAULT_PASSWORD)
    validate_ssh_login_notifications_default_fields(engines, login_source_ip_address,
                                                    username=DefaultConnectionValues.ADMIN,
                                                    password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                                    capability=LoginSSHNotificationConsts.ADMIN_CAPABITILY,
                                                    last_successful_login=successful_login_time)


@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_ssh_login_notification_password_change_admin(engines, login_source_ip_address, disable_password_hardening_rules):
    '''
    @summary: in this test case we want to validate admin username ssh login notification
    '''
    system = System()
    system.aaa.user.set_username(DefaultConnectionValues.ADMIN)

    with allure.step("Connecting to switch before validation to clear all failed messages"):
        logger.info("Connecting to switch before validation to clear all failed messages")
        successful_login_time = get_current_time_in_secs()
        ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip,
                                                              username=DefaultConnectionValues.ADMIN,
                                                              password=DefaultConnectionValues.DEFAULT_PASSWORD)
    try:
        change_username_password(engines, username=DefaultConnectionValues.ADMIN,
                                 curr_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                 new_password=DefaultConnectionValues.SIMPLE_PASSWORD)
        validate_ssh_login_notifications_default_fields(engines, login_source_ip_address,
                                                        username=DefaultConnectionValues.ADMIN,
                                                        password=DefaultConnectionValues.SIMPLE_PASSWORD,
                                                        capability=LoginSSHNotificationConsts.ADMIN_CAPABITILY,
                                                        check_password_change_msg=True,
                                                        last_successful_login=successful_login_time)
    finally:
        with allure.step('Restoring original password'):
            logger.info('Restoring original password')
        system.aaa.user.set(DefaultConnectionValues.PASSWORD, DefaultConnectionValues.DEFAULT_PASSWORD, apply=True, ask_for_confirmation=True)
        with allure.step("Sleeping {} secs to allow password change".format(DefaultConnectionValues.PASSWORD_UPDATE_TIME)):
            logger.info("Sleeping {} secs to allow password change".format(DefaultConnectionValues.PASSWORD_UPDATE_TIME))
        time.sleep(DefaultConnectionValues.PASSWORD_UPDATE_TIME)


@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_ssh_login_notification_role_new_user(engines, login_source_ip_address):
    '''
    @summary: in this test case we want to validate new user role change on ssh login notification,
    where we expect role message to appear
    '''
    try:
        system = System(None)
        with allure.step("Creating a new username"):
            logger.info("Creating a new username")
        user_name, password = system.create_new_user(engine=engines.dut)
        system.aaa.user.set_username(user_name)
        system.aaa.user.set(SystemConsts.USER_ROLE, SystemConsts.ROLE_CONFIGURATOR, apply=True, ask_for_confirmation=True)
        logging.info("User created: \nuser_name: {} \npassword: {}\ncapability: {}".format(user_name, password, SystemConsts.ROLE_CONFIGURATOR))

        with allure.step("Connecting to switch with the new user for first time"):
            logger.info("Connecting to switch with the new user for first time")
            successful_login_time = get_current_time_in_secs()
            ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip, username=user_name, password=password)

        with allure.step("Change role for new user: {} to {} role".format(user_name, SystemConsts.ROLE_VIEWER)):
            logger.info("Change role for new user: {} to {} role".format(user_name, SystemConsts.ROLE_VIEWER))
            system.aaa.user.set(SystemConsts.USER_ROLE, SystemConsts.ROLE_VIEWER, apply=True, ask_for_confirmation=True)

        validate_ssh_login_notifications_default_fields(engines, login_source_ip_address,
                                                        username=user_name,
                                                        password=password,
                                                        capability=SystemConsts.ROLE_VIEWER,
                                                        check_password_change_msg=False,
                                                        check_role_change_msg=True,
                                                        last_successful_login=successful_login_time)
    finally:
        with allure.step('Delete created user {}'.format(user_name)):
            logger.info('Delete created user {}'.format(user_name))
            if system and system.aaa and system.aaa.user:
                system.aaa.user.unset(apply=True, ask_for_confirmation=True)


@pytest.mark.simx
@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_ssh_login_notification_cli_commands_good_flow(engines, login_source_ip_address,
                                                       restore_original_record_period):
    '''
    @summary: in this test case we want to test the new cli commands for login ssh notification,
    this test case will contain the good flow,
    commands to be tested:
    1. nv set system ssh-server login-record-period
    2. nv show system ssh-server
    '''
    system = System(None)

    with allure.step("Connecting to switch before validation to clear all failed messages"):
        logger.info("Connecting to switch before validation to clear all failed messages")
        successful_login_time = get_current_time_in_secs()
        ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip,
                                                              username=DefaultConnectionValues.ADMIN,
                                                              password=DefaultConnectionValues.DEFAULT_PASSWORD)

    with allure.step("Validating ssh login record period set command"):
        logger.info("Validating ssh login record period set command")

    with allure.step("Setting new value for login record period"):
        logger.info("Setting new value for login record period")
        record_days = random.randint(LoginSSHNotificationConsts.MIN_RECORD_PERIOD_VAL, LoginSSHNotificationConsts.MAX_RECORD_PERIOD_VAL)
        system.ssh_server.set(LoginSSHNotificationConsts.RECORD_PERIOD, record_days, apply=True, ask_for_confirmation=True)
        validate_ssh_login_notifications_default_fields(engines, login_source_ip_address,
                                                        username=DefaultConnectionValues.ADMIN,
                                                        password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                                        capability=SystemConsts.ROLE_CONFIGURATOR,
                                                        check_password_change_msg=False,
                                                        check_role_change_msg=False,
                                                        expected_login_record_period=record_days,
                                                        last_successful_login=successful_login_time)

    with allure.step("Validating Validating show system ssh-server command"):
        logger.info("Validating Validating show system ssh-server command")
        output = json.loads(system.ssh_server.show())
        assert output[LoginSSHNotificationConsts.RECORD_PERIOD] == str(record_days), \
            "Could not match same login record period ib the show system ssh-server command\n" \
            "expected: {}, actual: {}".format(record_days, output[LoginSSHNotificationConsts.RECORD_PERIOD])


@pytest.mark.simx
@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_login_ssh_notification_performance(engines, login_source_ip_address, restore_original_record_period,
                                            delete_auth_logs):
    '''
    @summary: in this test case we want to validate the performance of the feature when there is a huge
    auth.log file
    '''
    system = System(None)

    with allure.step("Setting max value for login record period"):
        logger.info("Setting max value for login record period")
        system.ssh_server.set(LoginSSHNotificationConsts.RECORD_PERIOD,
                              LoginSSHNotificationConsts.MAX_RECORD_PERIOD_VAL,
                              apply=True, ask_for_confirmation=False)

    with allure.step("populating auth. logs by uploading from previously created files"):
        logger.info("populating auth. logs by uploading from previously created files")
        player_engine = engines['sonic_mgmt']
        player_engine.upload_file_using_scp(dest_username=DefaultConnectionValues.ADMIN,
                                            dest_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                            dest_folder=LoginSSHNotificationConsts.AUTH_LOG_SWITCH_PATH,
                                            dest_ip=engines.dut.ip,
                                            local_file_path=LoginSSHNotificationConsts.AUTH_LOGS_SHARED_LOCATION)

    with allure.step("Measuring login time"):
        logger.info("Measuring login time")
        start_time = datetime.datetime.now()
        ssh_to_device_and_retrieve_raw_login_ssh_notification(engines.dut.ip)
        end_time = datetime.datetime.now()
        login_time_sec = end_time.second - start_time.second
        logger.info("Login time is: {} secs".format(login_time_sec))
        assert login_time_sec <= LoginSSHNotificationConsts.MAX_LOGIN_TIME, \
            "Took too long to login to switch using ssh, max threshold: {}," \
            "actual: {}".format(LoginSSHNotificationConsts.MAX_LOGIN_TIME, login_time_sec)
