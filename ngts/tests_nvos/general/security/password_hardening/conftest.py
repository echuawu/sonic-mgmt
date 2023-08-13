import re
import pytest

from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tests_nvos.general.security.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_utils import set_local_users
from ngts.tools.test_utils import allure_utils as allure
import logging

from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts
from ngts.tests_nvos.general.security.password_hardening.PwhTools import PwhTools
from ngts.tests_nvos.system.clock.ClockTools import ClockTools


@pytest.fixture(scope='session')
def system():
    """
    Fixture that returns a System object
    """
    return System()


@pytest.fixture(scope='function')
def testing_users(engines, system):
    """
    Fixture that sets new users especially for test (and cleans them afterwards).
    There are 2 test users: 'test_admin' and 'test_monitor'.
    @return: (yield) Dictionary of
        {
            <username (str)>:    {
                                    'user_object': <User obj>, 'password': <pw (str)>
                                }
        }
    """
    with allure.step("Before test: set local test users"):
        users_info = AaaConsts.LOCAL_ONLY_TEST_USERS
        set_local_users(engines, users_info, apply=True)

        users = {
            user[AaaConsts.USERNAME]: {
                PwhConsts.USER_OBJ: System(username=user[AaaConsts.USERNAME]).aaa.user,
                AaaConsts.PASSWORD: user[AaaConsts.PASSWORD]
            } for user in users_info
        }

    yield users

    for username in users.keys():
        with allure.step(f'Clear user {username}'):
            System().aaa.user.unset(username)

    with allure.step('Apply users unset'):
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)


@pytest.fixture(scope='function')
def init_time(engines, system):
    """
    Prepare test in perspective of time. including:
        - disable ntp before test, and re-enable it after
        - set time to an early enough hour of the day, such that a day won't pass during the test
            (and restore it after the test)
        - restores the date to original before test
    """

    with allure.step('Getting the original state of ntp'):
        orig_ntp_state = OutputParsingTool.parse_json_str_to_dictionary(system.ntp.show()) \
            .get_returned_value()[PwhConsts.STATE]
        logging.info('Original ntp state: "{}"'.format(orig_ntp_state))

    should_change_ntp = orig_ntp_state == PwhConsts.ENABLED

    if should_change_ntp:
        with allure.step('Changing ntp state from "{}" to "{}"'.format(PwhConsts.ENABLED, PwhConsts.DISABLED)):
            system.ntp.set(op_param_name=PwhConsts.STATE, op_param_value=PwhConsts.DISABLED, apply=True).verify_result()

    with allure.step('Save original datetime before test'):
        orig_datetime = ClockTools.get_datetime_from_show_system_output(system.show())

    with allure.step('Calc hour diff between now to 3AM'):
        morning_datetime = re.sub(PwhConsts.REGEX_TIME, '03:00:00', orig_datetime)
        hour_diff = int(ClockTools.datetime_difference_in_seconds(orig_datetime, morning_datetime) / 3600)
        logging.info('Hour diff between now ({}) to 3AM ({}) : {}'.format(hour_diff, orig_datetime, morning_datetime))

    if hour_diff != 0:
        with allure.step('Set time to 3AM ({})'.format(morning_datetime)):
            system.datetime.action_change(params=morning_datetime).verify_result()

    yield

    cur_ntp_state = OutputParsingTool.parse_json_str_to_dictionary(system.ntp.show()).get_returned_value()[PwhConsts.STATE]
    if hour_diff != 0 and cur_ntp_state == PwhConsts.DISABLED:
        with allure.step('Restore time'):
            cur_datetime = ClockTools.get_datetime_from_show_system_output(system.show())
            restored_datetime = ClockTools.add_hours_to_datetime(cur_datetime, hour_diff)
            logging.info('Set time to {}'.format(restored_datetime))
            system.datetime.action_change(params=restored_datetime).verify_result()

    with allure.step('Restore original date after test'):
        cur_date = ClockTools.get_datetime_from_show_system_output(system.show()).split(' ')[0]
        orig_date = orig_datetime.split(' ')[0]
        days_diff = ClockTools.dates_diff_in_days(cur_date, orig_date)
        if days_diff != 0 and cur_ntp_state == PwhConsts.DISABLED:
            PwhTools.move_k_days(num_of_days=-days_diff, system=system)

    if should_change_ntp:
        with allure.step('Changing back ntp state from "{}" to "{}"'.format(PwhConsts.DISABLED, PwhConsts.ENABLED)):
            system.ntp.set(op_param_name=PwhConsts.STATE, op_param_value=PwhConsts.ENABLED, apply=True).verify_result()
