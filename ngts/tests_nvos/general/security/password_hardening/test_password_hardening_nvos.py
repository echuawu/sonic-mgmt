import allure
import logging
import pytest

from ngts.nvos_tools.system.System import *
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from infra.tools.redmine.redmine_api import is_redmine_issue_active
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts

''' ----------------------------------------------------------- '''


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


''' ----------------------------------------------------------- '''


@pytest.mark.security
@pytest.mark.simx
def test_show_system_security_password_hardening(engines):
    """
    Check pwh configuration appears correctly in show output,
    and verify initial pwh configuration contains default values to all pwh settings.

    Steps:
        1. run show command
        2. verify all info exist in output
        3. verify all values are set to default initially
    """
    system = System()

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
