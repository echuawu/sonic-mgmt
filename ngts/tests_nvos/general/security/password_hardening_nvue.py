import allure
import logging
import pytest

from ngts.nvos_tools.system.System import *
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli


def output_verification(output, exp_key, exp_val):
    output_dictionary = OutputParsingTool.parse_json_str_to_dictionary(output).get_returned_value()
    output_dictionary = {key: str(value) for key, value in output_dictionary.items()}
    ValidationTool.verify_field_exist_in_json_output(output_dictionary, [exp_key]).verify_result()
    ValidationTool.verify_field_value_in_output(output_dictionary, exp_key, exp_val, should_be_equal=True)


@pytest.mark.security
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
        'expiration': '111',
        'expiration-warning': '11',
        'history-cnt': '11',
        'len-min': '11',
        'lower-class': 'disabled',
        'special-class': 'disabled',
        'upper-class': 'disabled',
        'digit-class': 'disabled',
        'reject-user-passw-match': 'disabled',
        'state': 'enabled'
    }
    for policy, value in passw_hardening_conf_dict.items():
        with allure.step('Verify config & show system security password-hardening %s' % policy):
            system = System(None)

            passw_hardening_policy = policy
            passw_hardening_value = value

            system.security.password_hardening.set(passw_hardening_policy, passw_hardening_value)
            NvueGeneralCli.apply_config(engines.dut, True)
            password_hardening_output = system.security.password_hardening.show()
            output_verification(password_hardening_output, passw_hardening_policy, passw_hardening_value)

            security_output = system.security.show()
            output_verification(security_output, passw_hardening_policy, passw_hardening_value)


@pytest.mark.security
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

    for policy, value in passw_hardening_conf_dict.items():
        with allure.step('Verify config & show system security password-hardening %s' % policy):
            system = System(None)

            passw_hardening_policy = policy
            passw_hardening_value = value

            # TODO: extend verification infra to support set command expecting bad flow instead using try-except
            try:
                system.security.password_hardening.set(passw_hardening_policy, passw_hardening_value)
                raise NameError('nv set command should failed with key=%s, value=%s' % (passw_hardening_policy,
                                                                                        passw_hardening_value))
            except Exception as e:
                for curr_err in e.args:
                    if 'Error at %s' % policy in curr_err:
                        break
                    else:
                        raise NameError('Error not expected')
