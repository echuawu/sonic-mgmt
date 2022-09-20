import json
import logging
import random
import allure
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli

logger = logging.getLogger()


class Password_hardening(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/password-hardening'
        self.parent_obj = parent_obj

    def generate_password(self, random_length=True, max_length=32, is_valid=True):
        """
        :param random_length: if true we will pick randomly the username len
        :param max_length: user name max len
        :param is_valid: if true the password will be valid else
        :return: password
            flow:
                1. using parse_password_hardening_enabled_rules get password min length + enabled rules
                2. if random length pick randomly the password length
                3. get for enable rule how many chars will be this type [for each type >=1 and sums to length]
                4. chose the subset of string for each type
                5. random all these lists
        """
        with allure.step('generate password'):
            show = self.show()
            password_min_len, enabled_rules = Password_hardening.parse_password_hardening_enabled_rules(show)
            password_min_len = int(password_min_len)

            assert password_min_len <= max_length, "the password max length {max} < {min} min length".format(max=max_length, min=password_min_len)
            if random_length:
                password_length = random.randint(password_min_len, max_length)
            else:
                password_length = max_length

            each_type_list = RandomizationTool.random_list(len(enabled_rules), password_length - len(enabled_rules))
            password_chars = []
            for rule, count in zip(enabled_rules, each_type_list):
                password_chars += random.choices(SystemConsts.PASSWORD_HARDENING_DICT[rule], k=count + 1)

            random.shuffle(password_chars)
            return ''.join(password_chars)

    @staticmethod
    def parse_password_hardening_enabled_rules(password_hardening_output):
        """

        :param password_hardening_output: nv show system security output
        :return:
        """
        with allure.step('parssing nv show system security output'):
            assert password_hardening_output, "cmd output is empty"
            output_dictionary = json.loads(password_hardening_output)
            rules = [key for key in SystemConsts.PASSWORD_HARDENING_DEFAULT if output_dictionary[key] == SystemConsts.USER_STATE_ENABLED]

            assert SystemConsts.USERNAME_PASSWORD_HARDENING_STATE in output_dictionary.keys(), "{} not in cmd output"

            if output_dictionary[SystemConsts.USERNAME_PASSWORD_HARDENING_STATE] == SystemConsts.USER_STATE_DISABLED:
                rules = SystemConsts.PASSWORD_HARDENING_DEFAULT

            assert SystemConsts.USERNAME_PASSWORD_LENGTH_LABEL in output_dictionary.keys(), "{} not in cmd output"
            return output_dictionary[SystemConsts.USERNAME_PASSWORD_LENGTH_LABEL], rules
