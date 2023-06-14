import random
import re
import string
import itertools
import allure
import logging
import pytest
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.system.System import *
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts
from ngts.tests_nvos.general.security.password_hardening.PwhTools import PwhTools


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_weak_and_strong_passwords(engines, system):
    """
    @summary:
        Verify that setting a strong password succeeds, an setting a weak password fails
        * strong/weak - according to a password hardening configuration
        * verify - check that the set password command succeeds/fails and also check login succeeds/fails accordingly

        Steps:
        1. Set a password hardening configuration
        2. Pick a strong and a weak password
        3. Set the strong password
        4. Verify set succeeds
        5. Verify login with the strong password succeeds
        6. Try to set the weak password
        7. Verify set fails
        8. Verify that login with weak password fails
    """
    with allure.step('Get password hardening configuration'):
        logging.info('Get password hardening configuration')
        conf = OutputParsingTool.parse_json_str_to_dictionary(system.security.password_hardening.show())\
            .get_returned_value()

    with allure.step('Pick a strong and a weak password'):
        logging.info('Pick a strong and a weak password')
        username = PwhConsts.ADMIN_TEST_USR
        user_obj = System(username=username).aaa.user
        strong_pw = PwhTools.generate_strong_pw(conf, username, [])
        weak_pw = PwhTools.generate_weak_pw(conf, username, [strong_pw])
        logging.info(
            'Test username: "{}"\nstrong password: "{}"\nweak password: "{}"'.format(username, strong_pw, weak_pw))

    with allure.step('Set the strong password'):
        logging.info('Set the strong password')
        res_obj = user_obj.set(PwhConsts.PW, '"' + strong_pw + '"', apply=True)

    with allure.step('Verify set succeeds'):
        logging.info('Verify set succeeds')
        res_obj.verify_result(should_succeed=True)

    with allure.step('Verify login with the strong password succeeds'):
        logging.info('Verify login with the strong password succeeds')
        PwhTools.verify_user(system, username)
        PwhTools.verify_login(engines.dut, username, strong_pw, login_should_succeed=True)

    with allure.step('Try to set the weak password and expect errors'):
        logging.info('Try to set the weak password')
        expected_errors = PwhTools.get_expected_errors(conf, username, weak_pw, [strong_pw])
        PwhTools.set_pw_expect_pwh_error(user_obj, weak_pw, expected_errors)

    with allure.step('Verify that login with weak password fails'):
        logging.info('Verify that login with weak password fails')
        PwhTools.verify_login(engines.dut, username, weak_pw, login_should_succeed=False)
        PwhTools.verify_login(engines.dut, username, strong_pw, login_should_succeed=True)


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_show_system_security(engines, system):
    """
    Check pwh configuration appears correctly in show output,
    and verify initial pwh configuration contains default values to all pwh settings.

    Steps:
        1. run show command
        2. verify all info exist in output
        3. verify all values are set to default initially
    """

    with allure.step("Run 'nv show system security password-hardening'"):
        logging.info("Run 'nv show system security password-hardening'")
        output = OutputParsingTool.parse_json_str_to_dictionary(system.security.password_hardening.show()) \
            .get_returned_value()

    with allure.step("Verify all fields exist in output"):
        logging.info("Verify all fields exist in output")
        ValidationTool.verify_all_fields_value_exist_in_output_dictionary(output, PwhConsts.FIELDS).verify_result()

    with allure.step("Verify all initial values are set to default"):
        logging.info("Verify all initial values are set to default")
        ValidationTool.validate_fields_values_in_output(expected_fields=PwhConsts.FIELDS,
                                                        expected_values=PwhConsts.DEFAULTS.values(),
                                                        output_dict=output).verify_result()


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_enable_disable(engines, system, testing_users):
    """
    Check pwh configuration values (in show) when feature is enabled/disabled.
    Also, check pwh functionality when feature is enabled/disabled.
    * functionality: pwh rules are enforced on new pws when feature is enabled,
        and not enforced when feature is disabled.

    Steps:
    1. Disable feature
    2. Verify pwh configuration in show
    3. Set weak pw which violates pwh conf rules
    4. Verify pw changed (no rule enforcing on new pws)
    5. Enable feature
    6. Verify pwh configuration in show matches to original pwh conf
    7. Set weak pw which violates (some) pwh conf rules
    8. Verify pw didn't change (rules enforced)
    9. Set strong pw
    10. Verify pw changed
    """
    pwh = system.security.password_hardening
    usrname = PwhConsts.ADMIN_TEST_USR
    orig_pw = testing_users[usrname][PwhConsts.PW]
    user_obj = testing_users[usrname][PwhConsts.USER_OBJ]
    pw_history = [orig_pw]

    with allure.step("Take original pwh configuration"):
        logging.info("Take original pwh configuration")
        orig_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()

    with allure.step("Disable feature"):
        logging.info("Disable feature")
        pwh.set(PwhConsts.STATE, PwhConsts.DISABLED, apply=True).verify_result()

    with allure.step("Verify pwh configuration in show"):
        logging.info("Verify pwh configuration in show")
        cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()
        ValidationTool.compare_dictionaries(cur_pwh_conf, PwhConsts.DISABLED_CONF, True).verify_result()

    with allure.step("Generate weak pw which violates orig pwh conf rules"):
        logging.info("Generate weak pw which violates orig pwh conf rules")
        weak_pw = PwhTools.generate_weak_pw(orig_pwh_conf, usrname, orig_pw)

    with allure.step('Set weak pw "{}" and apply'.format(weak_pw)):
        logging.info('Set weak pw "{}" and apply'.format(weak_pw))
        user_obj.set(PwhConsts.PW, '"' + weak_pw + '"', apply=True).verify_result()
        pw_history.append(weak_pw)  # save successful new pws in this list for 'history record' for the test

    with allure.step("Enable feature"):
        logging.info("Enable feature")
        pwh.set(PwhConsts.STATE, PwhConsts.ENABLED, apply=True).verify_result()

    with allure.step("Verify pwh configuration in show matches to original pwh conf"):
        logging.info("Verify pwh configuration in show matches to original pwh conf")
        cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()
        ValidationTool.compare_dictionaries(cur_pwh_conf, orig_pwh_conf, True).verify_result()

    with allure.step('Try to set the weak password and expect errors'):
        logging.info('Try to set the weak password and expect errors')
        weak_pw2 = PwhTools.generate_weak_pw(cur_pwh_conf, usrname, weak_pw)
        expected_errors = PwhTools.get_expected_errors(cur_pwh_conf, usrname, weak_pw2, pw_history)
        PwhTools.set_pw_expect_pwh_error(user_obj, weak_pw2, expected_errors)

    with allure.step("Set strong pw"):
        logging.info("Set strong pw")
        strong_pw = PwhTools.generate_strong_pw(cur_pwh_conf, usrname, pw_history)
        user_obj.set(PwhConsts.PW, '"' + strong_pw + '"', apply=True).verify_result()


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_set_unset(engines, system):
    """
    Verify set/unset to each pwh setting, with valid inputs.
    The verification is done in show only (without functionality check - tested later)

    Steps:
        1. Set pwh setting with valid value
        2. Verify new setting in show
        3. Unset pwh setting
        4. Verify setting is set to default value in show
        * do the above to each pwh setting separately
    """
    pwh_obj = system.security.password_hardening

    with allure.step('Get current password hardening configuration'):
        logging.info('Get current password hardening configuration')
        orig_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
        logging.info('Current (orig) password hardening configuration:\n{}'.format(orig_pwh_conf))

    for setting in PwhConsts.FIELDS:
        with allure.step('Select random valid value for setting "{}" (except value "{}")'
                         .format(setting, orig_pwh_conf[setting])):
            logging.info('Select random valid value for setting "{}" (except value "{}")'
                         .format(setting, orig_pwh_conf[setting]))
            value = RandomizationTool.select_random_value(PwhConsts.VALID_VALUES[setting],
                                                          [orig_pwh_conf[setting]]).get_returned_value()

            if setting == PwhConsts.EXPIRATION or setting == PwhConsts.EXPIRATION_WARNING:
                smaller = int(value if setting == PwhConsts.EXPIRATION_WARNING else orig_pwh_conf[PwhConsts.EXPIRATION_WARNING])
                larger = int(value if setting == PwhConsts.EXPIRATION else orig_pwh_conf[PwhConsts.EXPIRATION])
                while smaller > larger:
                    value = RandomizationTool.select_random_value(PwhConsts.VALID_VALUES[setting],
                                                                  [orig_pwh_conf[setting]]).get_returned_value()
                    smaller = int(value if setting == PwhConsts.EXPIRATION_WARNING else orig_pwh_conf[PwhConsts.EXPIRATION_WARNING])
                    larger = int(value if setting == PwhConsts.EXPIRATION else orig_pwh_conf[PwhConsts.EXPIRATION])

            logging.info('Selected value for setting "{}" - "{}")'.format(setting, value))

            assert value in PwhConsts.VALID_VALUES[setting], \
                'Error: Something went wrong with randomizing new value for setting "{}".\n' \
                'Problem: value "{}" is not in valid values.'.format(setting, value)

            assert value != orig_pwh_conf[setting], \
                'Error: Something went wrong with randomizing new value for setting "{}".\n' \
                'Problem: selected value "{}" == orig value "{}"'.format(setting, value, orig_pwh_conf[setting])

        with allure.step('Set password hardening setting "{}" to "{}"'.format(setting, value)):
            logging.info('Set password hardening setting "{}" to "{}"'.format(setting, value))
            pwh_obj.set(setting, value, apply=True).verify_result()

        with allure.step('Verify new setting ("{}" = "{}") in show output'.format(setting, value)):
            logging.info('Verify new setting ("{}" = "{}") in show output'.format(setting, value))
            PwhTools.verify_pwh_setting_value_in_show(pwh_obj, setting, value)

        with allure.step('Unset password hardening setting "{}"'.format(setting)):
            logging.info('Unset password hardening setting "{}"'.format(setting))
            pwh_obj.unset(setting, apply=True).verify_result()

        with allure.step('Verify setting "{}" is set to default ("{}") in show output'
                         .format(setting, PwhConsts.DEFAULTS[setting])):
            logging.info('Verify setting "{}" is set to default ("{}") in show output'
                         .format(setting, PwhConsts.DEFAULTS[setting]))
            PwhTools.verify_pwh_setting_value_in_show(pwh_obj, setting, PwhConsts.DEFAULTS[setting])


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_set_invalid_input(engines, system):
    """
    Verify that running set command with invalid input values cause error and doesn't change pwh configuration.

    Steps:
        1. Set pwh setting with invalid value
        2. Verify error
        3. Verify setting is still set to original value
        * do the above to each pwh setting separately
    """
    pwh_obj = system.security.password_hardening

    with allure.step('Get current password hardening configuration'):
        logging.info('Get current password hardening configuration')
        orig_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
        logging.info('Current (orig) password hardening configuration:\n{}'.format(orig_pwh_conf))

    for setting in PwhConsts.FIELDS:
        with allure.step('Select invalid values for setting "{}"'.format(setting)):
            logging.info('Select invalid values for setting "{}"'.format(setting))

            # invalid values: 1.empty value; 2.just a random string; 3.another value which is not in valid values list
            invalid_values_to_test = PwhTools.generate_invalid_field_inputs(setting)

            for invalid_value in invalid_values_to_test:
                logging.info('Invalid value for setting "{}" - "{}")'.format(setting, invalid_value))

                with allure.step('Try to set password hardening setting "{}" to "{}"'.format(setting, invalid_value)):
                    logging.info('Try to set password hardening setting "{}" to "{}"'.format(setting, invalid_value))
                    res_obj = pwh_obj.set(setting, invalid_value, apply=False)

                with allure.step('Verify error'):
                    logging.info('Verify error')
                    if invalid_value == '':
                        expected_err = PwhConsts.ERR_INCOMPLETE_SET_CMD
                    elif PwhConsts.VALID_VALUES[setting] == [PwhConsts.ENABLED, PwhConsts.DISABLED]:
                        expected_err = PwhConsts.ERR_INVALID_SET_ENABLE_DISABLED
                    elif setting in PwhConsts.MIN.keys() and re.match(PwhConsts.REGEX_NUMERIC, str(invalid_value)):
                        expected_err = PwhConsts.ERR_RANGE
                    else:
                        expected_err = PwhConsts.ERR_INVALID_SET_CMD
                    PwhTools.verify_error(res_obj=res_obj, error_should_contain=expected_err)

                with allure.step('Verify setting "{}" is still "{}" in show output'
                                 .format(setting, orig_pwh_conf[setting])):
                    logging.info('Verify setting "{}" is still "{}" in show output'
                                 .format(setting, orig_pwh_conf[setting]))
                    PwhTools.verify_pwh_setting_value_in_show(pwh_obj, setting, orig_pwh_conf[setting])

    with allure.step('Verify the constraint expiration-warning must be less or equal to expiration'):
        logging.info('Verify the constraint expiration-warning must be less or equal to expiration')

        pwh_obj.unset(apply=True)
        conf = {PwhConsts.EXPIRATION: '-1', PwhConsts.EXPIRATION_WARNING: '-1'}
        PwhTools.set_pwh_conf(conf, pwh_obj, engines)

        with allure.step('Try to set expiration-warning which is larger than expiration'):
            logging.info('Try to set expiration-warning which is larger than expiration')
            exp = random.randint(0, PwhConsts.MAX[PwhConsts.EXPIRATION_WARNING] - 1)
            bad_exp_warn = random.randint(exp + 1, PwhConsts.MAX[PwhConsts.EXPIRATION_WARNING])
            logging.info('Set expiration to {} - should succeed'.format(exp))
            pwh_obj.set(PwhConsts.EXPIRATION, exp, apply=True).verify_result()
            logging.info('Try to set expiration-warning to {} (larger) - should fail'.format(bad_exp_warn))
            res_obj = pwh_obj.set(PwhConsts.EXPIRATION_WARNING, bad_exp_warn, apply=True)
            logging.info('Verify error')
            PwhTools.verify_error(res_obj=res_obj, error_should_contain=PwhConsts.ERR_EXP_WARN_LEQ_EXP)

        pwh_obj.unset(apply=True)
        conf = {PwhConsts.EXPIRATION: '-1', PwhConsts.EXPIRATION_WARNING: '-1'}
        PwhTools.set_pwh_conf(conf, pwh_obj, engines)

        with allure.step('Try to set expiration which is smaller than expiration-warning'):
            logging.info('Try to set expiration which is smaller than expiration-warning')
            exp_warn = random.randint(1, PwhConsts.MAX[PwhConsts.EXPIRATION_WARNING])
            bad_exp = random.randint(0, exp_warn - 1)
            logging.info('Set expiration-warning to {} - should succeed'.format(exp_warn))
            pwh_obj.set(PwhConsts.EXPIRATION_WARNING, exp_warn, apply=True).verify_result()
            logging.info('Try to set expiration to {} (smaller) - should fail'.format(bad_exp))
            res_obj = pwh_obj.set(PwhConsts.EXPIRATION, bad_exp, apply=True)
            logging.info('Verify error')
            PwhTools.verify_error(res_obj=res_obj, error_should_contain=PwhConsts.ERR_EXP_WARN_LEQ_EXP)


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
@pytest.mark.checklist
def test_password_hardening_functionality(engines, system, testing_users, tst_all_pwh_confs):
    """
    @summary:
        Check functionality with several password hardening configurations.
            * configuration functionality - password rule enforcing according to the configuration
            * feature enable/disable already checked in previous test
            * all checked configurations will have {state enabled, expiration&warning disabled, history disabled},
            *   these fields are checked in other tests

        Steps:
            1. Set password hardening configuration
            2. Verify configuration in show
            3. Try to set rule violating password (weak pw)
            4. Verify error
            5. Verify password didn't change
            6. Set rule complying new password (strong pw)
            7. Verify success and that password changed
    """
    pwh_obj = system.security.password_hardening
    test_username = PwhConsts.ADMIN_TEST_USR
    orig_pw = testing_users[PwhConsts.ADMIN_TEST_USR][PwhConsts.PW]
    test_user_obj = testing_users[PwhConsts.ADMIN_TEST_USR][PwhConsts.USER_OBJ]

    all_confs = PwhTools.generate_configurations()
    test_confs = all_confs if tst_all_pwh_confs else random.sample(all_confs, PwhConsts.NUM_SAMPLES)
    logging.info('The test will check with {} password hardening configurations'.format(len(test_confs)))

    old_pw = orig_pw
    pw_history = [orig_pw]

    with allure.step('Test functionality for each password hardening configuration'):
        logging.info('Test functionality for each password hardening configuration')
        prev_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
        for i, conf in enumerate(test_confs):
            logging.info('Testing with conf #{} :\n{}'.format(i, conf))  # for debugging

            with allure.step('Verify conf is a valid password hardening configuration'):
                logging.info('Verify conf is a valid password hardening configuration')
                PwhTools.assert_is_pwh_conf(conf)

            with allure.step('Set password hardening configuration'):
                logging.info('Set password hardening configuration:\n{}'.format(conf))
                PwhTools.set_pwh_conf(conf, pwh_obj, engines, prev_conf)

            lowers = False if conf[PwhConsts.LOWER_CLASS] == PwhConsts.ENABLED else True
            uppers = False if conf[PwhConsts.UPPER_CLASS] == PwhConsts.ENABLED else True
            digits = False if conf[PwhConsts.DIGITS_CLASS] == PwhConsts.ENABLED else True
            specials = False if conf[PwhConsts.SPECIAL_CLASS] == PwhConsts.ENABLED else True

            # when all are False (the relevant fields enabled) -> cant generate 'weak' password without any character
            if not (lowers or uppers or digits or specials):
                with allure.step('Generate weak password that breaks enabled policies in current configuration'):
                    logging.info('Generate weak password that breaks enabled policies in current configuration')
                    weak_pw = PwhTools.generate_random_pw(lowers, uppers, digits, specials)
                    logging.info('Generated weak password: "{}"'.format(weak_pw))

                with allure.step('Test with the weak password "{}"'.format(weak_pw)):
                    logging.info('Test with the weak password "{}"'.format(weak_pw))
                    PwhTools.verify_conf_with_password(engines.dut, conf, test_user_obj, weak_pw, old_pw, pw_history)

            if conf[PwhConsts.REJECT_USER_PASSW_MATCH] == PwhConsts.ENABLED:
                with allure.step('Test with the username as a password "{}"'.format(test_username)):
                    logging.info('Test with the username as a password "{}"'.format(test_username))
                    PwhTools.verify_conf_with_password(engines.dut, conf, test_user_obj, test_username, old_pw,
                                                       pw_history)

            with allure.step('Generate strong password that applies policies of current configuration'):
                logging.info('Generate strong password that applies policies of current configuration')
                strong_pw = PwhTools.generate_strong_pw(conf, test_username, pw_history)
                logging.info('Generated strong password: "{}"'.format(strong_pw))

            with allure.step('Test with the strong password "{}"'.format(strong_pw)):
                logging.info('Test with the strong password "{}"'.format(strong_pw))
                PwhTools.verify_conf_with_password(engines.dut, conf, test_user_obj, strong_pw, old_pw, pw_history)
                pw_history.append(strong_pw)
                old_pw = strong_pw

            prev_conf = conf  # step


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_history_functionality(engines, system, testing_users):
    """
    Test the functionality of history-cnt password hardening setting.

    Steps:
        1. Set history-cnt to N
        2. Set N new passwords
        3. Verify success (for each of them)
        4. Try to set these N passwords again
        5. Verify failure and error (for each of them)
        6. Set the original password
        7. Verify success (it is N+1 passwords ago)
    """
    # random.randint(PwhConsts.MIN[PwhConsts.HISTORY_CNT], PwhConsts.MAX[PwhConsts.HISTORY_CNT]) -> too long test
    hist_cnt = random.randint(PwhConsts.MIN[PwhConsts.HISTORY_CNT], PwhConsts.NUM_SAMPLES)
    logging.info('Chosen N = {}'.format(hist_cnt))

    pwh_obj = system.security.password_hardening

    test_username = PwhConsts.ADMIN_TEST_USR
    test_user_obj = testing_users[test_username][PwhConsts.USER_OBJ]
    orig_pw = testing_users[test_username][PwhConsts.PW]

    pw_history = [orig_pw]

    with allure.step('Set setting "{}" to N ( {} )'.format(PwhConsts.HISTORY_CNT, hist_cnt)):
        logging.info('Set setting "{}" to N ( {} )'.format(PwhConsts.HISTORY_CNT, hist_cnt))
        pwh_obj.set(PwhConsts.HISTORY_CNT, hist_cnt, apply=True).verify_result()
        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()

    with allure.step('Set N ( {} ) new passwords to user "{}" and verify success'.format(hist_cnt, test_username)):
        logging.info('Set N ( {} ) new passwords to user "{}" and verify success'.format(hist_cnt, test_username))
        pw_history = PwhTools.verify_set_passwords(hist_cnt, pwh_conf, test_username, test_user_obj, pw_history,
                                                   engines.dut,
                                                   should_succeed=True)

    with allure.step('Try to set some ( {} ) of these N ( {} ) passwords again, and verify errors'
                     .format(min(PwhConsts.NUM_SAMPLES, hist_cnt), hist_cnt)):
        logging.info('Try to set some ( {} ) of these N ( {} ) passwords again, and verify errors'
                     .format(min(PwhConsts.NUM_SAMPLES, hist_cnt), hist_cnt))
        # todo: currently user can reuse current pw to set as new pw (bug).
        #   after bug fix, change blow code to let the test pick also the current pass (pw_history[-1])
        cant_reuse_pws = pw_history[1:len(pw_history) - 1]  # can reuse orig and current pws, so don't pick them
        pws_to_try_again = random.sample(cant_reuse_pws, min(PwhConsts.NUM_SAMPLES, len(cant_reuse_pws)))
        pw_history = PwhTools.verify_set_passwords(pws_to_try_again, pwh_conf, test_username, test_user_obj, pw_history,
                                                   engines.dut, should_succeed=False)

    with allure.step('Set the original password ( "{}" ), and verify success'.format(orig_pw)):
        logging.info('Set the original password ( "{}" ), and verify success'.format(orig_pw))
        PwhTools.verify_set_passwords([orig_pw], pwh_conf, test_username, test_user_obj, pw_history, engines.dut,
                                      should_succeed=True)


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_expiration_functionality(engines, system, init_time, testing_users):
    """
    Test the functionality of password expiration setting.

    Steps:
        1. Set user1 with password pw1 ('old' password)
        2. Set expiration to N (should apply to old and new passwords)
        3. Set user2 with password pw2 ('new' password)
        4. Let N days to pass
            in each of these days, login with both users (expect success)
        5. After the N days pass (on day #N+1), login with both users
            expect password expiration prompt
    """
    pwh_obj = system.security.password_hardening
    user1 = PwhConsts.ADMIN_TEST_USR
    pw1 = testing_users[user1][PwhConsts.PW]
    user1_obj = testing_users[user1][PwhConsts.USER_OBJ]
    user2 = PwhConsts.MONITOR_TEST_USR
    pw2 = testing_users[user2][PwhConsts.PW]
    user2_obj = testing_users[user2][PwhConsts.USER_OBJ]

    exp = random.randint(0, PwhConsts.MAX[PwhConsts.EXPIRATION])  # can randomize between min_expiration to max_expiration but the test will be too long

    with allure.step('Set expiration setting to {}'.format(exp)):
        logging.info('Set expiration setting to {}'.format(exp))
        pwh_obj.set(PwhConsts.EXPIRATION_WARNING, -1, apply=True).verify_result()
        pwh_obj.set(PwhConsts.EXPIRATION, exp, apply=True).verify_result()

    with allure.step('Set user2 with new password'):
        logging.info('Set user2 with new password')
        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
        logging.info('Current password hardening configuration:\n{}'.format(pwh_conf))
        pw2 = PwhTools.generate_strong_pw(pwh_conf, user2, [pw2])
        logging.info('Setting new password for user2 ("{}") : "{}"'.format(user2, pw2))
        user2_obj.set(PwhConsts.PW, '"' + pw2 + '"', apply=True).verify_result()

    with allure.step('Let {} days pass, and on each day, login (with both users) and expect success'.format(exp)):
        logging.info('Let {} days pass, and on each day, login (with both users) and expect success'.format(exp))
        expired_day = exp + 1
        day_num = 0  # today
        while day_num <= expired_day:
            if day_num == expired_day:
                with allure.step('Day #{} - verify expired'.format(day_num)):
                    logging.info('Day #{} - verify expired'.format(day_num))
                    PwhTools.verify_expiration(engines.dut.ip, user1, pw1)
                    PwhTools.verify_expiration(engines.dut.ip, user2, pw2)
                break
            else:
                with allure.step('Day #{} - verify login success'.format(day_num)):
                    logging.info('Day #{} - verify login success'.format(day_num))
                    PwhTools.verify_login(engines.dut, user1, pw1, login_should_succeed=True)
                    PwhTools.verify_login(engines.dut, user2, pw2, login_should_succeed=True)

                step = random.randint(1, expired_day - day_num)
                with allure.step('Move {} days ahead'.format(step)):
                    logging.info('Move {} days ahead'.format(step))
                    PwhTools.move_k_days(num_of_days=step, system=system)
                    day_num += step


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_expiration_warning_functionality(engines, system, init_time, testing_users):
    """
    Test the functionality of password expiration-warning setting.

    Steps:
        1. Set user1 with password pw1 ('old' password)
        2. Set expiration to N, and expiration-warning to M < N (should apply to old and new passwords)
        3. Set user2 with password pw2 ('new' password)
        4. Let K (=N-M) days to pass
            in each of these days, login with both users (expect success)
        5. After the K days pass (on day #K+1), login with both users
            expect password expiration warning
    """
    pwh_obj = system.security.password_hardening
    user1 = PwhConsts.ADMIN_TEST_USR
    pw1 = testing_users[user1][PwhConsts.PW]
    user1_obj = testing_users[user1][PwhConsts.USER_OBJ]
    user2 = PwhConsts.MONITOR_TEST_USR
    pw2 = testing_users[user2][PwhConsts.PW]
    user2_obj = testing_users[user2][PwhConsts.USER_OBJ]

    exp = random.randint(1, PwhConsts.MAX[PwhConsts.EXPIRATION])
    exp_warn = random.randint(0, min(exp - 1, PwhConsts.MAX[PwhConsts.EXPIRATION_WARNING]))

    with allure.step('Set expiration-warning setting to {}'.format(exp_warn)):
        logging.info('Set expiration-warning setting to {}'.format(exp_warn))
        pwh_obj.set(PwhConsts.EXPIRATION_WARNING, exp_warn, apply=True).verify_result()

    with allure.step('Set expiration setting to {}'.format(exp)):
        logging.info('Set expiration setting to {}'.format(exp))
        pwh_obj.set(PwhConsts.EXPIRATION, exp, apply=True).verify_result()

    with allure.step('Set user2 with new password'):
        logging.info('Set user2 with new password')
        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
        logging.info('Current password hardening configuration:\n{}'.format(pwh_conf))
        pw2 = PwhTools.generate_strong_pw(pwh_conf, user2, [pw2])
        logging.info('Setting new password for user2 ("{}") : "{}"'.format(user2, pw2))
        user2_obj.set(PwhConsts.PW, '"' + pw2 + '"', apply=True).verify_result()

    with allure.step('Let {} days to pass'.format(exp)):
        logging.info('Let {} days to pass'.format(exp))
        warning_day = exp - exp_warn + 1
        day_num = 0  # today
        while day_num <= warning_day:
            if day_num == warning_day:
                with allure.step('Day #{} - Expect warning'.format(day_num)):
                    logging.info('Day #{} - Expect warning'.format(day_num))
                    PwhTools.verify_expiration(engines.dut.ip, user1, pw1, expiration_type=PwhConsts.EXPIRATION_WARNING)
                    PwhTools.verify_expiration(engines.dut.ip, user2, pw2, expiration_type=PwhConsts.EXPIRATION_WARNING)
                break
            else:
                with allure.step('Day #{} - verify login success'.format(day_num)):
                    logging.info('Day #{} - verify login success'.format(day_num))
                    PwhTools.verify_login(engines.dut, user1, pw1, login_should_succeed=True)
                    PwhTools.verify_login(engines.dut, user2, pw2, login_should_succeed=True)

                step = random.randint(1, warning_day - day_num)
                with allure.step('Move {} days ahead'.format(step)):
                    logging.info('Move {} days ahead'.format(step))
                    PwhTools.move_k_days(num_of_days=step, system=system)
                    day_num += step


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_apply_new_password_and_expiration_settings_together(engines, system, init_time):
    """
    Test several times in a row that running 'apply' on the expiration settings and new user password together
     apply the new settings also on the new user.

     1. Set user with password (no apply)
     2. Set expiration and expiration-warning settings
     3. Verify that new settings applied also on the new password
     * do the above several times in a row
    """
    pwh_obj = system.security.password_hardening
    orig_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()

    username = PwhConsts.ADMIN_TEST_USR
    user_obj = System(username=username).aaa.user

    for i in range(PwhConsts.NUM_SAMPLES):
        with allure.step('Round #{}'.format(i)):
            logging.info('Round #{}'.format(i))

            with allure.step('Randomizing new password, expiration and expiration-warning values'):
                logging.info('Randomizing new password, expiration and expiration-warning values')
                password = PwhTools.generate_strong_pw(orig_pwh_conf, username)
                expiration = random.randint(1, PwhConsts.NUM_SAMPLES)
                expiration_warning = random.randint(1, expiration)
                logging.info('New expiration: {}\t;\tNew expiration-warning: {}'.format(expiration, expiration_warning))

            with allure.step('Set user "{}" with password "{}" (no apply)'.format(username, password)):
                logging.info('Set user "{}" with password "{}" (no apply)'.format(username, password))
                user_obj.set(PwhConsts.PW, '"' + password + '"', apply=False).verify_result()

            with allure.step('Set expiration to {} (no apply)'.format(expiration)):
                logging.info('Set expiration to {} (no apply)'.format(expiration))
                pwh_obj.set(PwhConsts.EXPIRATION, expiration, apply=False).verify_result()

            with allure.step('Set expiration-warning to {} (no apply)'.format(expiration_warning)):
                logging.info('Set expiration-warning to {} (no apply)'.format(expiration_warning))
                pwh_obj.set(PwhConsts.EXPIRATION_WARNING, expiration_warning, apply=False).verify_result()

            with allure.step('Apply changes together'):
                logging.info('Apply changes together')
                SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)

            with allure.step('Verify new settings'):
                logging.info('Verify new settings')
                logging.info('Verify user "{}"'.format(username))
                PwhTools.verify_user(system, username, usr_should_exist=True)
                cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
                logging.info('Verify expiration in show\nExpected: {}\nActual: {}'
                             .format(int(expiration), int(cur_pwh_conf[PwhConsts.EXPIRATION])))
                ValidationTool.compare_values(int(expiration), int(cur_pwh_conf[PwhConsts.EXPIRATION])).verify_result()
                logging.info('Verify expiration-warning in show\nExpected: {}\nActual: {}'
                             .format(int(expiration_warning), int(cur_pwh_conf[PwhConsts.EXPIRATION_WARNING])))
                ValidationTool.compare_values(int(expiration_warning), int(cur_pwh_conf[PwhConsts.EXPIRATION_WARNING])) \
                    .verify_result()

            with allure.step('Verify new expiration settings applied also on new password'):
                logging.info('Verify new expiration settings applied also on new password')
                chage_output = PwhTools.run_chage(engines.dut, username)
                chage_dict = OutputParsingTool.parse_linux_cmd_output_to_dic(chage_output).get_returned_value()
                logging.info('Compare expiration:\nExpected: {}\nActual: {}'
                             .format(int(expiration), int(chage_dict[PwhConsts.CHAGE_EXPIRATION])))
                ValidationTool.compare_values(int(chage_dict[PwhConsts.CHAGE_EXPIRATION]), int(expiration)).verify_result()
                logging.info('Compare expiration-warning:\nExpected: {}\nActual: {}'
                             .format(expiration_warning, chage_dict[PwhConsts.CHAGE_EXPIRATION_WARNING]))
                ValidationTool.compare_values(int(chage_dict[PwhConsts.CHAGE_EXPIRATION_WARNING]),
                                              int(expiration_warning)).verify_result()

            with allure.step('Unset changes'):
                logging.info('Unset changes')
                pwh_obj.unset(apply=True).verify_result()
                user_obj.unset(apply=True).verify_result()

            with allure.step('Verify old settings'):
                logging.info('Verify old settings')
                logging.info('Verify user "{}" doesnt exist'.format(username))
                PwhTools.verify_user(system, username, usr_should_exist=False)
                cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh_obj.show()).get_returned_value()
                logging.info('Verify expiration in show\nExpected: {}\nActual: {}'
                             .format(int(orig_pwh_conf[PwhConsts.EXPIRATION]), int(cur_pwh_conf[PwhConsts.EXPIRATION])))
                ValidationTool.compare_values(int(orig_pwh_conf[PwhConsts.EXPIRATION]), int(cur_pwh_conf[PwhConsts.EXPIRATION])) \
                    .verify_result()
                logging.info('Verify expiration-warning in show\nExpected: {}\nActual: {}'
                             .format(int(orig_pwh_conf[PwhConsts.EXPIRATION_WARNING]), int(cur_pwh_conf[PwhConsts.EXPIRATION_WARNING])))
                ValidationTool.compare_values(int(orig_pwh_conf[PwhConsts.EXPIRATION_WARNING]),
                                              int(cur_pwh_conf[PwhConsts.EXPIRATION_WARNING])).verify_result()


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_history_multi_user(engines, system, testing_users):
    """
    @summary:
        Test that password history of one user doesn't affect another user

        1. Set history-count to N
        2. Set user1 with N new passwords (pw1, pw2, ... , pwN)
        3. Set user2 with the same N passwords
        4. Expect success (user1's history shouldn't affect user2)
        5. Set user2 with another password (pwN+1)
        6. Try to set user1 with password pw1
        7. Expect failure (pw1 is in the previous N passwords for user1)
        8. Set user2 with password pw1
        9. Expect success (pw1 is no longer in the previous N passwords for user2)
    """
    pwh = system.security.password_hardening

    user1 = PwhConsts.ADMIN_TEST_USR
    user1_obj = testing_users[user1][PwhConsts.USER_OBJ]
    pw1 = testing_users[user1][PwhConsts.PW]
    pw_hist1 = [pw1]

    user2 = PwhConsts.MONITOR_TEST_USR
    user2_obj = testing_users[user2][PwhConsts.USER_OBJ]
    pw2 = testing_users[user2][PwhConsts.PW]
    pw_hist2 = [pw2]

    hist_cnt = random.randint(PwhConsts.MIN[PwhConsts.HISTORY_CNT], PwhConsts.NUM_SAMPLES)
    logging.info('Chosen history-count for test_history_multi_user_password_hardening: {}'.format(hist_cnt))

    with allure.step('Set history-count to {}'.format(hist_cnt)):
        logging.info('Set history-count to {}'.format(hist_cnt))
        pwh.set(PwhConsts.HISTORY_CNT, hist_cnt, apply=True).verify_result()

    with allure.step('Set user1 "{}" with {} new passwords'.format(user1, hist_cnt)):
        logging.info('Set user1 "{}" with {} new passwords'.format(user1, hist_cnt))

        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()

        for i in range(hist_cnt):
            pw1 = PwhTools.generate_strong_pw(pwh_conf, user1, pw_hist1)
            logging.info('Round #{} - Set user1 "{}" with password "{}"'.format(i + 1, user1, pw1))
            user1_obj.set(PwhConsts.PW, '"' + pw1 + '"', apply=True).verify_result()
            pw_hist1.append(pw1)

    with allure.step('Set user2 "{}" with the same {} passwords, and expect success'.format(user2, hist_cnt)):
        logging.info('Set user2 "{}" with the same {} passwords, and expect success'.format(user2, hist_cnt))
        passwords_to_set = pw_hist1[1:]  # take the same N new passwords that were set to user1
        assert len(passwords_to_set) == hist_cnt, 'Error: Something is wrong.\nExpected len(passwords_to_set) : {}\n' \
                                                  'Actual len(passwords_to_set) : {}\n' \
                                                  'passwords_to_set : {}'\
            .format(hist_cnt, len(passwords_to_set), passwords_to_set)

        for i in range(hist_cnt):
            pw2 = passwords_to_set[i]
            logging.info('Round #{} - Set user2 "{}" with password "{}"'.format(i + 1, user2, pw2))
            user2_obj.set(PwhConsts.PW, '"' + pw2 + '"', apply=True).verify_result()
            pw_hist2.append(pw2)

    with allure.step('Set user2 "{}" with another password (pw_{}+1)'.format(user2, hist_cnt)):
        logging.info('Set user2 "{}" with another password (pw_{}+1)'.format(user2, hist_cnt))
        pw2 = PwhTools.generate_strong_pw(pwh_conf, user2, pw_hist2)
        logging.info('Set user2 "{}" with password "{}"'.format(user2, pw2))
        user2_obj.set(PwhConsts.PW, '"' + pw2 + '"', apply=True).verify_result()
        pw_hist2.append(pw2)

    with allure.step('Try to set user1 "{}" with password pw_1 "{}" and expect errors'.format(user1, pw_hist1[1])):
        logging.info('Try to set user1 "{}" with password pw_1 "{}" and expect errors'.format(user1, pw_hist1[1]))
        PwhTools.set_pw_expect_pwh_error(user1_obj, pw_hist1[1], [PwhConsts.WEAK_PW_ERRORS[PwhConsts.HISTORY_CNT]])
        if TestToolkit.tested_api == ApiType.NVUE:
            logging.info('Detaching the failed config')
            NvueGeneralCli.detach_config(engines.dut)

    with allure.step('Set user2 "{}" with password pw_1 "{}"'.format(user2, pw_hist2[1])):
        logging.info('Set user2 "{}" with password pw_1 "{}"'.format(user2, pw_hist2[1]))
        assert pw_hist1[1] == pw_hist2[1], 'Error: expected pw_hist1[1] == pw_hist2[1]\n' \
                                           'pw_hist1[1] = {}\n' \
                                           'pw_hist2[1] = {}'.format(pw_hist1[1], pw_hist2[1])
        res_obj = user2_obj.set(PwhConsts.PW, '"' + pw_hist2[1] + '"', apply=True)

    with allure.step('Expect success'):
        logging.info('Expect success')
        res_obj.verify_result()


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_history_increase(engines, system, testing_users):
    """
    @summary:
        Check if a record of password which is older than history-count is not dropped from the records.

        Steps:
        1. Set history-count to N
        2. Set 2N new passwords (pw1, .. , pwN , .. , pw_2N)
        3. Increase history-count to 2N
        4. Try to set again pw1, .. , pwN
        5. Expect failure
    """
    pwh = system.security.password_hardening
    username = PwhConsts.ADMIN_TEST_USR
    user_obj = testing_users[username][PwhConsts.USER_OBJ]
    orig_pw = testing_users[username][PwhConsts.PW]

    with allure.step('Set history-count'):
        logging.info('Set history-count')
        hist_cnt = random.randint(PwhConsts.MIN[PwhConsts.HISTORY_CNT], PwhConsts.NUM_SAMPLES)
        logging.info('Set history-count to {}'.format(hist_cnt))
        pwh.set(PwhConsts.HISTORY_CNT, hist_cnt, apply=True).verify_result()
        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()

    with allure.step('Set 2*{} ({}) new passwords'.format(hist_cnt, 2 * hist_cnt)):
        logging.info('Set 2*{} ({}) new passwords'.format(hist_cnt, 2 * hist_cnt))
        pw_history = [orig_pw]
        for i in range(1, (2 * hist_cnt) + 1):
            pw_i = PwhTools.generate_strong_pw(pwh_conf, username, pw_history)
            logging.info('Round #{} - Set user "{}" with password "{}"'.format(i, username, pw_i))
            user_obj.set(PwhConsts.PW, '"' + pw_i + '"', apply=True).verify_result()
            pw_history.append(pw_i)

    with allure.step('Increase history-count to 2*{} ({})'.format(hist_cnt, 2 * hist_cnt)):
        logging.info('Increase history-count to 2*{} ({})'.format(hist_cnt, 2 * hist_cnt))
        pwh.set(PwhConsts.HISTORY_CNT, 2 * hist_cnt, apply=True).verify_result()
        pwh_conf[PwhConsts.HISTORY_CNT] = 2 * hist_cnt

    with allure.step('Try to set again the first {} passwords. Expect failure'.format(hist_cnt)):
        logging.info('Try to set again the first {} passwords. Expect failure'.format(hist_cnt))
        for i in range(1, hist_cnt + 1):
            pw_i = pw_history[i]
            logging.info('Round #{} - Set user "{}" with password pw_{} - "{}"'.format(i, username, i, pw_i))
            PwhTools.set_pw_expect_pwh_error(user_obj, pw_i, [PwhConsts.WEAK_PW_ERRORS[PwhConsts.HISTORY_CNT]])


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_password_hardening_history_when_feature_disabled(engines, system, testing_users):
    """
    @summary:
        Check if passwords are recorded in password history when feature is disabled

        Steps:
        1. Set history-cnt to N
        2. Disable the feature
        3. Set N new passwords
        4. Enable the feature
        5. Try to set again the N passwords
        6. Expect failure
    """
    username = PwhConsts.ADMIN_TEST_USR
    user_obj = testing_users[username][PwhConsts.USER_OBJ]
    orig_pw = testing_users[username][PwhConsts.PW]
    pwh = system.security.password_hardening
    pw_history = [orig_pw]

    with allure.step('Set history-cnt'):
        logging.info('Set history-cnt')
        hist_cnt = random.randint(PwhConsts.MIN[PwhConsts.HISTORY_CNT], PwhConsts.NUM_SAMPLES)
        logging.info('Set history-cnt to {}'.format(hist_cnt))
        pwh.set(PwhConsts.HISTORY_CNT, hist_cnt, apply=True).verify_result()
        pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()

    with allure.step('Disable the feature'):
        logging.info('Disable the feature')
        pwh.set(PwhConsts.STATE, PwhConsts.DISABLED, apply=True).verify_result()

    with allure.step('Set {} new passwords'.format(hist_cnt)):
        logging.info('Set {} new passwords'.format(hist_cnt))
        for i in range(1, hist_cnt + 1):
            pw_i = PwhTools.generate_strong_pw(pwh_conf, username, pw_history)
            logging.info('Round #{} - Set user "{}" wit pw_{} - "{}"'.format(i, username, i, pw_i))
            user_obj.set(PwhConsts.PW, '"' + pw_i + '"', apply=True).verify_result()
            pw_history.append(pw_i)

    with allure.step('Enable the feature'):
        logging.info('Enable the feature')
        pwh.set(PwhConsts.STATE, PwhConsts.ENABLED, apply=True).verify_result()

    with allure.step('Try to set again the {} new passwords. Expect failure'.format(hist_cnt)):
        logging.info('Try to set again the {} new passwords. Expect failure'.format(hist_cnt))
        for i in range(1, hist_cnt):
            pw_i = pw_history[i]
            with allure.step('Set user "{}" with pw_{} - "{}" and expect errors'.format(username, i, pw_i)):
                logging.info('Round #{} - Set user "{}" with pw_{} - "{}" and expect errors'.format(i, username, i, pw_i))
                PwhTools.set_pw_expect_pwh_error(user_obj, pw_i, [PwhConsts.WEAK_PW_ERRORS[PwhConsts.HISTORY_CNT]])
