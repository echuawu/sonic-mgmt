import pytest
import allure
import logging

from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts
from ngts.tests_nvos.general.security.password_hardening.PwhTools import PwhTools


@pytest.fixture(scope='session')
def system():
    """
    Fixture that returns a System object
    """
    return System()


@pytest.fixture(scope='function')
def init_pwh(system):
    """
    Fixture that initializes pwh conf to default before test, and restores it to default after test.
    """
    with allure.step("Fixture: init_pwh - before test - Initializing pwh configuration to defaults"):
        logging.info("Fixture: init_pwh - before test - Initializing pwh configuration to defaults")
        system.security.password_hardening.unset(apply=True).verify_result()

    yield

    with allure.step("Fixture: init_pwh - after test - Restoring pwh configuration to defaults"):
        logging.info("Fixture: init_pwh - after test - Restoring pwh configuration to defaults")
        system.security.password_hardening.unset(apply=True).verify_result()


@pytest.fixture(scope='function')
def testing_users(engines, system):
    """
    Fixture that sets new users especially for test (and cleans them afterwards).
    There are 2 test users: 'test_admin' and 'test_monitor'.
    @return: (yield) Dictionary of
        {
            <usrname (str)>:    {
                                    'user_object': <User obj>, 'password': <pw (str)>
                                }
        }
    """
    with allure.step("Fixture: testing_users - before test - setting new users & pws"):
        logging.info("Fixture: testing_users - before test - setting new users & pws")

        with allure.step("Get pwh configuration"):
            pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(system.security.password_hardening.show())\
                .get_returned_value()
            logging.info("Get pwh configuration:\n{}".format(pwh_conf))

        with allure.step("Generate testing usrnames"):
            usrname_admin, usrname_monitor = PwhConsts.ADMIN_TEST_USR, PwhConsts.MONITOR_TEST_USR
            logging.info("Generate testing usrnames: {} , {}".format(usrname_admin, usrname_monitor))

        with allure.step("Generate testing pw"):
            pw_admin = PwhTools.generate_strong_pw(pwh_conf, usrname_admin)
            pw_monitor = PwhTools.generate_strong_pw(pwh_conf, usrname_monitor)
            logging.info("Generate pws for test users:\n{} - {}\n{} - {}"
                         .format(usrname_admin, pw_admin, usrname_monitor, pw_monitor))

        users = {usrname_admin: pw_admin, usrname_monitor: pw_monitor}

        for usrname, pw in users.items():
            role = PwhConsts.ADMIN if usrname == usrname_admin else PwhConsts.MONITOR
            with allure.step('Set test usr "{}" and pw "{}" with role {}'.format(usrname, pw, role)):
                logging.info('Set test usr "{}" and pw "{}" with role {}'.format(usrname, pw, role))

                logging.info('set the usr + pw')
                system.create_new_user(engines.dut, usrname, pw, role)
                user_obj = System(username=usrname).aaa.user

                users[usrname] = {PwhConsts.USER_OBJ: user_obj, PwhConsts.PW: pw}

    yield users

    with allure.step("Fixture: testing_users - after test - cleaning test users"):
        logging.info("Fixture: testing_users - after test - cleaning test users")
        for usrname, usr_dict in users.items():
            with allure.step('Unset test usr "{}"'.format(usrname)):
                logging.info('Unset test usr "{}"'.format(usrname))
                usr_dict[PwhConsts.USER_OBJ].unset(apply=True).verify_result()


@pytest.fixture(scope='function')
def admin_test_user_obj(testing_users):
    return testing_users[PwhConsts.ADMIN_TEST_USR][PwhConsts.USER_OBJ]


@pytest.fixture(scope='function')
def monitor_test_user_obj(testing_users):
    return testing_users[PwhConsts.MONITOR_TEST_USR][PwhConsts.USER_OBJ]
