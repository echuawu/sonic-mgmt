import logging
import random
import allure
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()


def test_set_password(engines):
    """

        Test flow:
            1. generate new valid password
            2. create new admin user
            3. create new monitor user
            4. nv set system aaa user user_monitor password <new_password>
            5. nv set system aaa user user_admin password <new_password>
            6. nv config apply
            7. connect as admin
            8. connect as monitor
    """
    system = System(None)
    with allure.step('generating valid password'):
        new_password = system.security.password_hardening.generate_password(is_valid=True)
    with allure.step('creating two user with different roles'):
        viewer_name, viewer_password = system.create_new_user(engine=engines.dut, role=SystemConsts.ROLE_VIEWER)
        configurator_name, configurator_password = system.create_new_user(engine=engines.dut)
    with allure.step('try to set the password of two user to a new valid password'):
        system.aaa.user.set_username(configurator_name)
        system.aaa.user.set(SystemConsts.USER_PASSWORD, '"' + new_password + '"').verify_result()
        system.aaa.user.set_username(viewer_name)
        system.aaa.user.set(SystemConsts.USER_PASSWORD, '"' + new_password + '"').verify_result()
        NvueGeneralCli.apply_config(engines.dut)
    with allure.step('try to connect with new users using the new password'):
        ConnectionTool.create_ssh_conn(engines.dut.ip, viewer_name, new_password).verify_result()
        ConnectionTool.create_ssh_conn(engines.dut.ip, configurator_name, new_password).verify_result()


def test_set_invalid_password(engines):
    """

        Test flow:
            1. generate invalid password
            2. nv set system aaa user monitor password <new_password>
            3. nv config apply
            3. verify the output message includes relevant error messages
    """
    system = System(None)
    with allure.step('generate invalid password'):
        secutiry_output = system.security.password_hardening.show()
        password_min_len, enabled_rules = system.security.password_hardening.parse_password_hardening_enabled_rules(secutiry_output)
        invalid_password, random_labels = generate_invalid_password(enabled_rules, password_min_len)
    with allure.step('try to set the invalid password and verify the output message'):
        system.aaa.user.set_username(SystemConsts.DEFAULT_USER_MONITOR)
        set_output = system.aaa.user.set(SystemConsts.USER_PASSWORD, '"' + invalid_password + '"').verify_result()
        verify_invalid_messages(random_labels, set_output)

    NvueGeneralCli.detach_config(engines.dut)


def test_set_invalid_password_length(engines):
    """

        Test flow:
            1. get min password length
            2. generate new password of random length 1-min
            3. run nv set system aaa user monitor password <invalid_password>
            4. verify the output message includes
                msg = Password should contain at least 8 characters
            2. nv set system aaa user monitor password <new_password>
            3. nv config apply
            3. verify the output message includes relevant error messages
    """
    system = System(None)
    with allure.step('generate invalid password - length < min'):
        secutiry_output = system.security.password_hardening.show()
        password_min_len, enabled_rules = system.security.password_hardening.parse_password_hardening_enabled_rules(secutiry_output)
        invalid_password, rules = generate_invalid_password(enabled_rules=enabled_rules, password_min_len=password_min_len, length_case=True)
    with allure.step('try to set the invalid password and verify the output message'):
        system.aaa.user.set_username(SystemConsts.DEFAULT_USER_MONITOR)
        result_obj = system.aaa.user.set(SystemConsts.USER_PASSWORD, '"' + invalid_password + '"', apply=False)
        assert not result_obj.result and 'Password should contain at least' in result_obj.info, \
            "length error message not as expected the output = {output} expected = {expected}".format(output=result_obj.info,
                                                                                                      expected='Password should contain at least')
    NvueGeneralCli.detach_config(engines.dut)


def test_password_not_in_logs(engines):
    """

        Test flow:
            1. run set system aaa user admin password <new_password>
            2. run history 3
            3. verify 'password *' in the output
    """
    system = System(None)
    with allure.step('generate new user password and try to set'):
        new_password = system.security.password_hardening.generate_password(is_valid=True)
        system.aaa.user.set(SystemConsts.USER_PASSWORD, '"' + new_password + '"').verify_result()
    with allure.step('run history 3 to verify no password'):
        history_output = engines.dut.run_cmd('history 3')
        assert 'password *' in history_output, "the history output is {history} does not include password * as expected".format(
            history=history_output)
    NvueGeneralCli.detach_config(engines.dut)


def generate_invalid_password(enabled_rules, password_min_len, length_case=False):
    """

    :param enabled_rules: all enabled rules in password hardening
    :param password_min_len: the min password len
    :param length_case: if true random len > min else random len < min
    :return:
    """
    with allure.step('generate invalid password'):
        with allure.step('pick random rules to support'):
            random_count = random.randint(1, len(enabled_rules) - 1)
            random_labels = random.choices(enabled_rules, k=random_count)
            logger.info('the password will support only {rules}'.format(rules=random_labels))

        with allure.step('pick random password length'):
            if length_case:
                password_length = random.randint(1, int(password_min_len) - 1)
            else:
                password_length = random.randint(int(password_min_len), 32)
                logger.info('the password length = {length}'.format(length=password_length))
        each_type_list = RandomizationTool.random_list(len(random_labels), password_length - len(random_labels))
        password_chars = []
        for rule, count in zip(random_labels, each_type_list):
            password_chars += random.choices(SystemConsts.PASSWORD_HARDENING_DICT[rule], k=count + 1)

        random.shuffle(password_chars)
        return ''.join(password_chars), random_labels


def verify_invalid_messages(supported_rules, set_output):
    """

    :param supported_rules: list of rules that password should support
    :param set_output:  the set password command output
    :return:
    """
    messeges_dict = {
        'digits-class': '    Password should contain at least one digit',
        'lower-class': '    Password should contain at least one lowercase character',
        'upper-class': '    Password should contain at least one uppercase character',
        'special-class': '    Password should contain at least one special character'
    }
    with allure.step('verify the error message is as expected'):
        output_lines = set_output.splitlines()[2:]
        expected_output = [messeges_dict[value] for value in messeges_dict.keys() if value not in supported_rules]
        assert expected_output.sort() == output_lines.sort(), "at least one of the error messages is missing, output = {output} expected = {expected}".format(output=output_lines, expected=expected_output)
