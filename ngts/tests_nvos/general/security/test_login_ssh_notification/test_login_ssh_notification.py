import datetime
import random
import re
import os
import time

import allure
import pexpect
import logging
import pytest
from ngts.tests_nvos.general.security.test_login_ssh_notification.constants import LoginSSHNotificationConsts
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool


logger = logging.getLogger(__name__)


def create_ssh_login_engine(dut_ip, username):
    '''
    @summary: in this function we want to create ssh connection to device,
    ssh connection means that only executing the command:
    'ssh {-o OPTIONS} -l {username} {dut_ip}'
    without entering password!
    :param dut_ip: device IP
    :param username: username intiaiting the ssh connection
    :return: pexpect python module with ssh connection command executed as the spwan command
    '''
    _ssh_command = 'ssh {} -l {} {}'.format(DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS,
                                            username,
                                            dut_ip)
    # connect to device
    child = pexpect.spawn(_ssh_command, env={'TERM': 'dumb'}, timeout=10)
    return child


def ssh_to_device_and_retrieve_raw_login_ssh_notification(dut_ip,
                                                          username=DefaultConnectionValues.ADMIN,
                                                          password=DefaultConnectionValues.DEFAULT_PASSWORD):
    '''
    @summary: in this function we create ssh connection
    and return the raw output after connecting to device
    '''
    notification_login_message = ''

    with allure.step("Connection to dut device with SSH"):
        logger.info("Connection to dut device with SSH")
        # connecting using pexpect
        try:
            child = create_ssh_login_engine(dut_ip, username)
            respond = child.expect([DefaultConnectionValues.PASSWORD_REGEX, '~'])
            if respond == 0:
                notification_login_message += child.before.decode('utf-8')
                child.sendline(password)
                child.expect(DefaultConnectionValues.DEFAULT_PROMPTS[0])

            # convert output to decode
            notification_login_message += child.before.decode('utf-8')
            # close connection
        finally:
            child.close()
        return notification_login_message


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
    @summary: in this function we will parse the login ssh notification parameteres
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


def validate_ssh_login_notifications_default_fields(engines, login_source_ip_address, username, password, capability):
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
    :param login_source_ip_address: ip address initiaing the ssh connection in the test
    :param username: username to connect with to switch
    :param password: the password for username
    :param capability: the username capability, could be one of [admin, monitor]
    '''
    with allure.step("Connect for the first time to switch and store details"):
        logger.info("Connect for the first time to switch and store details")
        first_login_notification_message = parse_ssh_login_notification(engines.dut.ip, username,
                                                                        password)

    random_number_of_connection_fails = random.randint(5, 15)
    with allure.step("Fail connecting to device {}".format(random_number_of_connection_fails)):
        logger.info("Fail connecting to device {}".format(random_number_of_connection_fails))
        logger.info("Attempting {} wrong password attempts".format(random_number_of_connection_fails))
        for index in range(random_number_of_connection_fails):
            try:
                connection = create_ssh_login_engine(engines.dut.ip, DefaultConnectionValues.ADMIN)
                connection.expect(DefaultConnectionValues.PASSWORD_REGEX)
                random_password = RandomizationTool.get_random_string(random.randint(LoginSSHNotificationConsts.PASSWORD_MIN_LEN,
                                                                                     LoginSSHNotificationConsts.PASSWORD_MAX_LEN))
                logger.info("Itertation {} - connecting using random password: {}".format(index, random_password))
                connection.sendline(random_password)
                connection.expect("[Pp]ermission denied")
            finally:
                connection.close()

    with allure.step("Connect for the second time to switch and store details"):
        logger.info("Connect for the second time to switch and store details")
        second_login_notification_message = parse_ssh_login_notification(engines.dut.ip, DefaultConnectionValues.ADMIN,
                                                                         DefaultConnectionValues.DEFAULT_PASSWORD)

    with allure.step("Validating capability"):
        logger.info("Validating capability")
        if capability == LoginSSHNotificationConsts.ADMIN_CAPABITILY:
            assert second_login_notification_message[LoginSSHNotificationConsts.NUMBER_OF_SUCCESSFUL_CONNECTIONS_IN_THE_LAST_RECORD_PERIOD] is not None,\
                "Admin capability was not able to see total successful login value in the last record period"
        elif capability == LoginSSHNotificationConsts.MONITOR_CAPABITILY:
            assert second_login_notification_message[LoginSSHNotificationConsts.NUMBER_OF_SUCCESSFUL_CONNECTIONS_IN_THE_LAST_RECORD_PERIOD] is None, \
                "Monitor capability was able to see total successful login value in the last record period"

    with allure.step("Validating {} failed attemps in the second connection".format(random_number_of_connection_fails)):
        logger.info("Validating {} failed attemps in the second connection".format(random_number_of_connection_fails))
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

    with allure.step("Valiadting same date"):
        logger.info("Valiadting same date")
        output = os.popen("date").read()
        current_date_string = re.findall(LoginSSHNotificationConsts.LINUX_DATE_REGEX, output)[0]
        logger.info("Linux date is {}".format(current_date_string))
        current_date = convert_linux_date_output_to_datetime_object(current_date_string)
        time_delta_seconds = (current_date - second_login_notification_message[LoginSSHNotificationConsts.LAST_SUCCESSFUL_LOGIN_DATE]).seconds
        assert time_delta_seconds < LoginSSHNotificationConsts.MAX_TIME_DELTA_BETWEEEN_CONNECTIONS, "Time Delta between current time and successful login ssh time is not under 120 secs, \n" \
                                                                                                    "The time difference is {}".format(time_delta_seconds)
        time_delta_seconds = (current_date - second_login_notification_message[LoginSSHNotificationConsts.LAST_UNSUCCESSFUL_LOGIN_DATE]).seconds
        assert time_delta_seconds < LoginSSHNotificationConsts.MAX_TIME_DELTA_BETWEEEN_CONNECTIONS, "Time Delta between current time and successful login ssh time is not under 120 secs, \n" \
                                                                                                    "The time difference is {}".format(time_delta_seconds)

    with allure.step("Validating no password or capability has changed"):
        logger.info("Validating no password or capability has changed")
        assert second_login_notification_message[LoginSSHNotificationConsts.PASSWORD_CHANGED_MESSAGE] is None, \
            "Password change message appeared when it should not"
        assert second_login_notification_message[LoginSSHNotificationConsts.ROLE_CHANGED_MESSAGE] is None, \
            "Capability change message appeared when it should not"

    logger.info("Test is Done")


@pytest.mark.simx
@pytest.mark.login_ssh_notification
@pytest.mark.checklist
def test_ssh_login_notifications_default_fields_admin(engines, login_source_ip_address):
    '''
    @summary: in this test case we want to validate admin username ssh login notification
    '''
    validate_ssh_login_notifications_default_fields(engines, login_source_ip_address,
                                                    username=DefaultConnectionValues.ADMIN,
                                                    password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                                    capability=LoginSSHNotificationConsts.ADMIN_CAPABITILY)
