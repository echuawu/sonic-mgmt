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

''' --------------------------- OLD TESTS ----------------------------------- '''


def output_verification(output_dictionary, exp_key, exp_val):
    output_dictionary = {key: str(value) for key, value in output_dictionary.items()}
    ValidationTool.verify_field_exist_in_json_output(output_dictionary, [exp_key]).verify_result()
    ValidationTool.verify_field_value_in_output(output_dictionary, exp_key, exp_val, should_be_equal=True).verify_result()


@pytest.mark.security
@pytest.mark.simx
def test_good_flow_password_hardening(engines):
    """
    Run show system reboot command and verify the reboot history and reason values
        Test flow:
            1. run set system security password-hardening <policy> <policy value>
            2. config apply
            3. show system security
            4. verify last show configuration
            5. show system security password-hardening
            6. verify last show configuration
    """

    passw_hardening_conf_dict = {
        'history-cnt': '11',
        'len-min': '11',
        'lower-class': 'disabled',
        'special-class': 'disabled',
        'upper-class': 'disabled',
        'digits-class': 'disabled',
        'reject-user-passw-match': 'disabled',
        'state': 'enabled'
    }

    if not is_redmine_issue_active([3313369]):
        passw_hardening_conf_dict['expiration'] = '111'
        passw_hardening_conf_dict['expiration-warning'] = '11'

    for passw_hardening_policy, passw_hardening_value in passw_hardening_conf_dict.items():
        with allure.step('Verify config & show system security password-hardening %s' % passw_hardening_policy):
            system = System(None)

            with allure.step("set {} = {}".format(passw_hardening_policy, passw_hardening_value)):
                system.security.password_hardening.set(passw_hardening_policy, passw_hardening_value).verify_result()
                NvueGeneralCli.apply_config(engines.dut, True)

                with allure.step("Verify output after set command - using show security/password_hardening output"):
                    password_hardening_output = OutputParsingTool.parse_json_str_to_dictionary(
                        system.security.password_hardening.show()).get_returned_value()
                    output_verification(password_hardening_output, passw_hardening_policy, passw_hardening_value)

                with allure.step("Verify output after set command - using show security output"):
                    security_output = OutputParsingTool.parse_json_str_to_dictionary(system.security.show()).get_returned_value()
                    output_verification(security_output["password-hardening"], passw_hardening_policy, passw_hardening_value)


@pytest.mark.security
@pytest.mark.simx
def test_bad_flow_password_hardening():
    """
    test bad flow of nv set/show of system security password-hardening
        Test flow:
            1. nv set security password-hardening <policy> <policy value> with value invalid.
            2. Expect set to failed, other, raise an error
    """
    passw_hardening_conf_dict = {
        'expiration': '611',
        'expiration-warning': '61',
        'history-cnt': '611',
        'len-min': '111',
        'lower-class': '1',
        'special-class': '1',
        'upper-class': '1',
        'digit-class': '1',
        'reject-user-passw-match': '1',
        'state': '1'
    }

    for passw_hardening_policy, passw_hardening_value in passw_hardening_conf_dict.items():
        with allure.step('Verify config & show system security password-hardening %s' % passw_hardening_policy):
            system = System(None)
            system.security.password_hardening.set(passw_hardening_policy,
                                                   passw_hardening_value).verify_result(False)


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_show_system_security(engines):
    """
    Run show system security command and verify the required fields
    """
    expected_fields = ["digits-class", "history-cnt", "len-min", "lower-class", "reject-user-passw-match",
                       "special-class", "state", "upper-class", "expiration", "expiration-warning"]

    with allure.step("Create System object"):
        system = System(None)

    with allure.step("Show system security"):
        output = OutputParsingTool.parse_json_str_to_dictionary(system.security.show()).get_returned_value()
        assert "password-hardening" in output.keys(), "'password-hardening' can't be found in the output"

        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(output["password-hardening"],
                                                                          expected_fields).verify_result()

    with allure.step("Show system security password-hardening"):
        output = OutputParsingTool.parse_json_str_to_dictionary(
            system.security.show("password-hardening")).get_returned_value()
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(output,
                                                                          expected_fields).verify_result()


''' ---------------------------------------------------------------------- '''


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_show_system_security_password_hardening(engines, system):
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
        output = OutputParsingTool.parse_json_str_to_dictionary(system.security.password_hardening.show())\
            .get_returned_value()

    with allure.step("Verify all fields exist in output"):
        logging.info("Verify all fields exist in output")
        ValidationTool.verify_all_fileds_value_exist_in_output_dictionary(output, PwhConsts.FIELDS).verify_result()

    with allure.step("Verify all initial values are set to default"):
        logging.info("Verify all initial values are set to default")
        ValidationTool.validate_fields_values_in_output(expected_fields=PwhConsts.FIELDS,
                                                        expected_values=PwhConsts.DEFAULTS.values(),
                                                        output_dict=output).verify_result()


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_enable_disable_password_hardening(engines, system, testing_users):
    """
    Check pwh configuration values (in show) when feature is enabled/disabled.
    Also, check pwh functionality when feature is enabled/disabled.
    * functionality: pwh rules are enforced on new pws when feature is enabled,
        and not enforced when feature is disabled.

    Steps:
    1. Disable feature
    2. Verify pwh configuration in show
    3. Set weak pw which violates all pwh conf rules
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
        PwhTools.set_pw_and_apply(user_obj, weak_pw).verify_result()

    with allure.step("Verify pw changed (no rule enforcing on new pws)"):
        logging.info("Verify pw changed (no rule enforcing on new pws)")
        PwhTools.verify_login(engines.dut, usrname, orig_pw, login_should_succeed=False)
        PwhTools.verify_login(engines.dut, usrname, weak_pw)
        pw_history.append(weak_pw)  # save successful new pws in this list for 'history record' for the test

    with allure.step("Enable feature"):
        logging.info("Enable feature")
        pwh.set(PwhConsts.STATE, PwhConsts.ENABLED, apply=True).verify_result()

    with allure.step("Verify pwh configuration in show matches to original pwh conf"):
        logging.info("Verify pwh configuration in show matches to original pwh conf")
        cur_pwh_conf = OutputParsingTool.parse_json_str_to_dictionary(pwh.show()).get_returned_value()
        ValidationTool.compare_dictionaries(cur_pwh_conf, orig_pwh_conf, True).verify_result()

    with allure.step("Set weak pw which violates (some) pwh conf rules"):
        logging.info("Set weak pw which violates (some) pwh conf rules")
        weak_pw2 = PwhTools.generate_weak_pw(cur_pwh_conf, usrname, weak_pw)
        PwhTools.set_pw_and_apply(user_obj, weak_pw2).verify_result(should_succeed=False)

    with allure.step("Verify pw didn't change (rules enforced)"):
        logging.info("Verify pw didn't change (rules enforced)")
        PwhTools.verify_login(engines.dut, usrname, weak_pw2, login_should_succeed=False)
        PwhTools.verify_login(engines.dut, usrname, weak_pw)

    with allure.step("Set strong pw"):
        logging.info("Set strong pw")
        strong_pw = PwhTools.generate_strong_pw(cur_pwh_conf, usrname, pw_history)
        PwhTools.set_pw_and_apply(user_obj, strong_pw).verify_result()

    with allure.step("Verify pw changed"):
        logging.info("Verify pw changed")
        PwhTools.verify_login(engines.dut, usrname, weak_pw, login_should_succeed=False)
        PwhTools.verify_login(engines.dut, usrname, strong_pw)


@pytest.mark.system
@pytest.mark.security
@pytest.mark.simx
def test_set_unset_password_hardening(engines, system):
    """
    Verify set/unset to each pwh setting, with valid inputs.
    The verification is done in show only (without functionality check - tested later)

    Steps:
        1. Set pwh setting with valid value
        2. Verify new setting in show
        3. Unset pwh setting
        4. Verify setting is set to default value in show
        * do the above to each pwh setting
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


def t_test(engines, system):
    with allure.step("ALON: START"):
        logging.info("ALON: START")

    with allure.step("ALON: SHOW USERS"):
        logging.info("ALON: SHOW USERS")
        # monitor_usr = System(username="monitor").aaa.user
        # # logging.info(monitor_usr.show())
        # # logging.info(system.aaa.user.show())
        # logging.info("ALON: {}".format(system.aaa.show('user alonn')))
        # logging.info('ALON: {}'.format(engines.dut.update_credentials('alonn', 'lalala', 1, 1)))

        res = system.security.password_hardening.set(PwhConsts.STATE, PwhConsts.DISABLED, apply=True)
        res2 = system.security.password_hardening.unset(apply=True)
        res3 = system.aaa.user.set('password', 'Yourpassword1!', apply=True)
        res4 = system.aaa.user.unset(apply=True)
        conf_show_output = system.security.password_hardening.show()
        dict = OutputParsingTool.parse_json_str_to_dictionary(conf_show_output).get_returned_value()

    with allure.step("ALON: END"):
        logging.info("ALON: END")
