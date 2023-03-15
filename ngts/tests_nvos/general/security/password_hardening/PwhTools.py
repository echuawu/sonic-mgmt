import random
import string
import allure

from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts
import logging
from netmiko.ssh_exception import NetmikoAuthenticationException


class PwhTools:

    @staticmethod
    def generate_strong_pw(pwh_conf, usrname='', pw_history=[]):
        """
        Generates a pw which applies the given pwh configuration rules
        @param pwh_conf: pwh configuration as a dict of { <pwh field (str)>: <value (str)> }
        @param usrname: username (str)
        @param pw_history: record of pw history as a list (from oldest to newest)
        @return: a random valid pw (str), according to the given pwh conf rules
        """
        with allure.step('First verify that parameter is valid pwh configuration'):
            logging.info('First verify that parameter is valid pwh configuration')
            PwhTools.assert_is_pwh_conf(pwh_conf)

        with allure.step('Generating strong password according to the password hardening configuration'):
            logging.info('PwhTools.generate_strong_pw(pwh_conf, usrname, pw_history)\n'
                         'pwh_conf = {} \nusrname = {}\npw_history = {}'.format(pwh_conf, usrname, pw_history))

            pw_len = random.randint(int(pwh_conf[PwhConsts.LEN_MIN]), int(pwh_conf[PwhConsts.LEN_MIN]) + 10)
            logging.info('Random len for pw: {}'.format(pw_len))

            pw = RandomizationTool.get_random_string(length=pw_len)
            logging.info('Random string of len {} : "{}"'.format(pw_len, pw))

            logging.info('Strenghtening the pw to follow given pwh conf rules')
            if pwh_conf[PwhConsts.LOWER_CLASS] == PwhConsts.ENABLED:
                logging.info('{} is enabled. adding a random lowercase char'.format(PwhConsts.LOWER_CLASS))
                pw += chr(random.randint(ord('a'), (ord('z'))))

            if pwh_conf[PwhConsts.UPPER_CLASS] == PwhConsts.ENABLED:
                logging.info('{} is enabled. adding a random uppercase char'.format(PwhConsts.UPPER_CLASS))
                pw += chr(random.randint(ord('A'), (ord('Z'))))

            if pwh_conf[PwhConsts.DIGITS_CLASS] == PwhConsts.ENABLED:
                logging.info('{} is enabled. adding a random digit char'.format(PwhConsts.DIGITS_CLASS))
                pw += chr(random.randint(ord('0'), (ord('9'))))

            if pwh_conf[PwhConsts.SPECIAL_CLASS] == PwhConsts.ENABLED:
                logging.info('{} is enabled. adding a random special char'.format(PwhConsts.SPECIAL_CLASS))
                pw += random.choice(PwhConsts.SPECIAL_CHARS)

            k = int(pwh_conf[PwhConsts.HISTORY_CNT])  # k = history-cnt
            n = len(pw_history)
            newest_k_pws = pw_history[n - k + 1:] if k <= n else pw_history

            while (pw in newest_k_pws) \
                    or (pwh_conf[PwhConsts.REJECT_USER_PASSW_MATCH] == PwhConsts.ENABLED and pw == usrname):
                pw += RandomizationTool.get_random_string(length=1)

        with allure.step('Finished generating strong pw: "{}"'.format(pw)):
            logging.info('Finished generating strong pw: "{}"'.format(pw))
            return pw

    @staticmethod
    def generate_weak_pw(pwh_conf, usrname='', pw_history=[], generate_short_pw=False):
        """
        Generates a pw which violates the given pwh configuration rules
        @param pwh_conf: pwh configuration as a dict of { <pwh field (str)>: <value (str)> }
        @param usrname: username (str)
        @param pw_history: record of pw history as a list (from oldest to newest)
        @param generate_short_pw: [True/False] to generate just a pw shorter than len-min or not
        @return: a random valid pw (str), according to the given pwh conf rules
        """
        with allure.step('First verify that parameter is valid pwh configuration'):
            logging.info('First verify that parameter is valid pwh configuration')
            PwhTools.assert_is_pwh_conf(pwh_conf)

        with allure.step('Generating weak password according to the password hardening configuration'):
            logging.info('PwhTools.generate_weak_pw(pwh_conf, usrname, pw_history, generate_short_pw)\n'
                         'pwh_conf = {} \nusrname = {}\npw_history = {}\ngenerate_short_pw = {}'
                         .format(pwh_conf, usrname, pw_history, generate_short_pw))

            if generate_short_pw:
                with allure.step('Generating password shorter than min-len'):
                    logging.info('Generating password shorter than min-len ({})'
                                 .format(int(pwh_conf[PwhConsts.LEN_MIN])))
                    pw_len = random.randint(0, int(pwh_conf[PwhConsts.LEN_MIN]) - 1) \
                        if int(pwh_conf[PwhConsts.LEN_MIN]) >= 0 else 0
                    logging.info('Random len for pw: {}'.format(pw_len))
                    pw = RandomizationTool.get_random_string(length=pw_len)
                    logging.info('Random string of len {} : "{}"'.format(pw_len, pw))
                    logging.info('Finished generating weak pw: "{}"'.format(pw))
                    return pw

            pw_len = random.randint(int(pwh_conf[PwhConsts.LEN_MIN]), int(pwh_conf[PwhConsts.LEN_MIN]) + 10)
            logging.info('Random len for pw: {}'.format(pw_len))

            with allure.step('Generating random weak password of length {}'.format(pw_len)):
                logging.info('Generating random weak password of length {}'.format(pw_len))

                pw = RandomizationTool.get_random_string(length=pw_len)
                logging.info('Random string of len {} : "{}"'.format(pw_len, pw))

                logging.info('Weakening the pw to violate given pwh conf rules')
                if pwh_conf[PwhConsts.LOWER_CLASS] == PwhConsts.ENABLED:
                    logging.info('{} is enabled. uppercase all characters is enough'.format(PwhConsts.LOWER_CLASS))
                    pw = pw.upper()
                elif pwh_conf[PwhConsts.UPPER_CLASS] == PwhConsts.ENABLED:
                    logging.info('{} is enabled. can finish'.format(PwhConsts.UPPER_CLASS))
                elif pwh_conf[PwhConsts.DIGITS_CLASS] == PwhConsts.ENABLED:
                    logging.info('{} is enabled. can finish'.format(PwhConsts.DIGITS_CLASS))
                elif pwh_conf[PwhConsts.SPECIAL_CLASS] == PwhConsts.ENABLED:
                    logging.info('{} is enabled. can finish'.format(PwhConsts.SPECIAL_CLASS))
                    pw += random.choice(PwhConsts.SPECIAL_CHARS)
                elif pwh_conf[PwhConsts.REJECT_USER_PASSW_MATCH] == PwhConsts.ENABLED:
                    logging.info('{} is enabled. set pw to be usrname: {}'.format(PwhConsts.REJECT_USER_PASSW_MATCH, usrname))
                    pw = usrname
                else:
                    k = int(pwh_conf[PwhConsts.HISTORY_CNT])  # k = history-cnt
                    n = len(pw_history)
                    newest_k_pws = pw_history[n - k + 1:] if k <= n else pw_history
                    pw = random.choice(newest_k_pws)
                    logging.info('everithing else disabled. chose random pw from history: {}'.format(pw))

        with allure.step('Finished generating weak pw: "{}"'.format(pw)):
            logging.info('Finished generating weak pw: "{}"'.format(pw))
            return pw

    @staticmethod
    def assert_is_pwh_conf(obj):
        """
        Verifies that a given object is a pwh configuration -> dict of { <pwh field (str)>: <value (str)> }
        @param obj: the given object
        """
        with allure.step("PwhTools.assert_is_pwh_conf(obj) :  obj = \n{o}".format(o=obj)):
            logging.info("PwhTools.assert_is_pwh_conf(obj) :  obj = \n{o}".format(o=obj))

        with allure.step("checking that obj is dict"):
            logging.info("checking that obj is dict")
            assert isinstance(obj, dict), 'Error: the given parameter is not a dict'

        with allure.step("checking that obj has all fields"):
            logging.info("checking that obj has all fields")
            assert sorted(obj.keys()) == sorted(PwhConsts.DEFAULTS.keys()), \
                "Error: the given parameter doesn't have all pwh configuration fields"

        with allure.step("checking that obj has valid values"):
            logging.info("checking that obj has valid values")
            invalid_values = {}
            for field, val in obj.items():
                if obj[field] not in PwhConsts.VALID_VALUES[field]:
                    invalid_values[field] = obj[field]

            assert not invalid_values, 'Error: the given param is not a valid pwh configuration. ' \
                                       'The invalid values:\n{ivs}'.format(ivs=invalid_values)

    @staticmethod
    def verify_user(system_obj, usrname='', usr_should_exist=True):
        """
        Verifies wether a user with a given username exists or not
        @param system_obj: System object
        @param usrname: the given username to check
        @param usr_should_exist: true - verify that the username exists; false - verify doesn't exist
        """
        with allure.step('Verify that user "{}" {}'.format(usrname, 'exist' if usr_should_exist else 'does not exist')):
            logging.info('Verify that user "{}" {}'.format(usrname, 'exist' if usr_should_exist else 'does not exist'))

            show_output = system_obj.aaa.show(PwhConsts.USER + ' ' + usrname)
            cond = show_output != PwhConsts.ERR_ITEM_NOT_EXIST
            logging.info('show cmd output: {}\ncond: {}\nusr_should_exist: {}'
                         .format(show_output, cond, usr_should_exist))

            assert cond == usr_should_exist, \
                'Error: PwhTools.verify_user() asserts that user "{}" should{} exist, but it does{}'\
                .format(usrname, '' if usr_should_exist else ' not', ' exist.' if cond else ' not exist.')

    @staticmethod
    def verify_login(dut_engine_obj, usrname='', pw='', login_should_succeed=True):
        """
        Verifies wether a user with a given username exists or not
        @param dut_engine_obj: dut engine object
        @param usrname: the given username
        @param pw: the given pw
        @param login_should_succeed: true - verify that the login should succeed; false - shouldn't succeed
        """
        with allure.step('Verify that login with user "{}" and pw "{}" {}'
                         .format(usrname, pw, 'succeeds' if login_should_succeed else 'does not succeed')):
            logging.info('Verify that login with user "{}" and pw "{}" {}'
                         .format(usrname, pw, 'succeeds' if login_should_succeed else 'does not succeed'))

        with allure.step('Check ssh connection with username "{}" and password "{}"'.format(usrname, pw)):
            logging.info('Check ssh connection with username "{}" and password "{}"'.format(usrname, pw))
            cond = PwhTools.check_ssh_connection(dut_engine_obj, usrname, pw)

        with allure.step('Assert cond ( {} ) == login_should_succeed ( {} )\nAssert result: {}'
                         .format(cond, login_should_succeed, cond == login_should_succeed)):
            logging.info('Assert cond ( {} ) == login_should_succeed ( {} )\nAssert result: {}'
                         .format(cond, login_should_succeed, cond == login_should_succeed))
            assert cond == login_should_succeed, 'Error: PwhTools.verify_login() asserts that login with user "{}" ' \
                                                 'and pw "{}" should{} succeed, but it did{}' \
                .format(usrname, pw, '' if login_should_succeed else ' not', '.' if cond else ' not.')

    @staticmethod
    def check_ssh_connection(dut_engine_obj, usr, pw):
        """
        Encapsulate ProxySshEngine.update_credentials() method to return True in success and False in failure
        @param dut_engine_obj: dut engine object
        @param usr: username
        @param pw: password
        @return: True - if update_credentials succeeds; False - otherwise
        """
        res_obj = ConnectionTool.create_ssh_conn(dut_engine_obj.ip, usr, pw)
        connection_success = res_obj.result
        if connection_success:
            res_obj.returned_value.disconnect()
        return connection_success

    @staticmethod
    def set_pw_and_apply(user_obj, pw):
        """
        Encapsulate System.AAA.User.set(), to set a new pw
        @param user_obj: User object
        @param pw: password to set
        @return: ResultObj returned from set()
        """
        return user_obj.set(PwhConsts.PW, '"' + pw + '"', apply=True)

    @staticmethod
    def verify_pwh_setting_value_in_show(pwh_obj, setting, expected_value):
        """
        Verify that a given password hardening setting is set to the given value
        in the current password hardening configuration
        @param pwh_obj: Password_hardening object
        @param setting: given pwh setting to check
        @param expected_value: given value to check
        """
        with allure.step('Get current password hardening configuration'):
            logging.info('Get current password hardening configuration')
            cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
            logging.info('Current (orig) password hardening configuration:\n{}'.format(cur_pwh_conf))

        with allure.step('Verify that current "{}" is set to "{} in show output'.format(setting, expected_value)):
            logging.info('Verify that current "{}" is set to "{} in show output'.format(setting, expected_value))
            ValidationTool.compare_values(cur_pwh_conf[setting], expected_value).verify_result()

    @staticmethod
    def verify_error(res_obj, error_should_contain=''):
        """
        Verify (through ResultObj) that a switch operation failed, and the error message contains a given string
        @param res_obj: the given result object of the switch operation run
        @param error_should_contain: the given string that should be contained in the error message
        """
        with allure.step('Verify that switch operation failed'):
            logging.info('Verify that switch operation failed')
            res_obj.verify_result(should_succeed=False)

        with allure.step('Switch operation failed as expected'):
            logging.info('Switch operation failed as expected')

        with allure.step('Verify that op error message "{}" contains the given string "{}"'
                         .format(res_obj.info, error_should_contain)):
            logging.info('Verify that op error message "{}" contains the given string "{}"'
                         .format(res_obj.info, error_should_contain))
            err_msg = 'Error: switch operation failed, but error message is not as expected.\n' \
                      '\tActual operation error message: "{}"\n' \
                      '\tExpected (missing) substring: "{}"'.format(res_obj.info, error_should_contain)
            ValidationTool.verify_substring_in_output(output=res_obj.info, substring=error_should_contain,
                                                      err_message_in_case_of_failure=err_msg, should_be_found=True)

        with allure.step('Switch operation failed with expected error message'):
            logging.info('Switch operation failed with expected error message')

    @staticmethod
    def generate_invalid_field_inputs(field):
        """
        Generate 3 invalid inputs of a given password hardening field:
            1. empty value
            2. just a random string
            3. another value which is not valid (mainly for field with number values).
        @param field: given field (str)
        @return: list of invalid inputs (strings) for the given field
        """
        with allure.step('Generating invalid input values for setting "{}"'.format(field)):
            logging.info('Generating invalid input values for setting "{}"'.format(field))
            # invalid values: 1.empty value; 2.just a random string; 3.another value which is not in valid values list
            invalid_values_to_test = ['']  # empty value

            another_value = RandomizationTool.get_random_string(random.randint(1, 10),
                                                                string.ascii_letters + string.digits)
            while another_value in PwhConsts.VALID_VALUES[field]:
                another_value = RandomizationTool.get_random_string(random.randint(1, 10),
                                                                    string.ascii_letters + string.digits)
            invalid_values_to_test.append(another_value)

            # random value outside the valid set of values
            if PwhConsts.VALID_VALUES[field] == [PwhConsts.ENABLED, PwhConsts.DISABLED]:
                another_value = RandomizationTool.get_random_string(random.randint(1, 10),
                                                                    string.ascii_letters + string.digits)
                while another_value in PwhConsts.VALID_VALUES[field]:
                    another_value = RandomizationTool.get_random_string(random.randint(1, 10),
                                                                        string.ascii_letters + string.digits)
            else:
                invalid_vals = list(range(-999, PwhConsts.MIN[field])) + list(range(PwhConsts.MAX[field] + 1, 999))
                another_value = random.choice(invalid_vals)
            invalid_values_to_test.append(another_value)

        with allure.step('Verify that generated values are indeed invalid'):
            logging.info('Verify that generated values are indeed invalid')
            for val in invalid_values_to_test:
                assert val not in PwhConsts.VALID_VALUES[field], \
                    'Error: Something went wrong with randomizing invalid value for field "{}".\n' \
                    'Problem: value "{}" is in valid values, although it should not.'.format(field, val)

        logging.info('Generated invalid values successfully')
        return invalid_values_to_test
