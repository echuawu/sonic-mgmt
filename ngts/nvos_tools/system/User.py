import allure
import logging
import random
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool

logger = logging.getLogger()


class User(BaseComponent):
    def __init__(self, parent_obj=None, username='admin'):
        BaseComponent.__init__(self, parent=parent_obj, path='/user/' + username)
        self.username = username
        self.password = BaseComponent(self, path='/password')
        self.full_name = BaseComponent(self, path='/full-name')
        self.state = BaseComponent(self, path='/state')
        self.role = BaseComponent(self, path='/role')

    @staticmethod
    def get_lslogins(engine, username):
        return OutputParsingTool.parse_lslogins_cmd(
            engine.run_cmd('lslogins {username}'.format(username=username))).verify_result()

    def verify_user_label(self, username, label, new_full_name):
        with allure.step('verify the user {username} {label} value'.format(username=username, label=label)):
            self.set_username(username)
            output = OutputParsingTool.parse_json_str_to_dictionary(self.show()).verify_result()
            assert output[label] == new_full_name, "the new user {username} full name is {full_name} not " \
                                                   "{new_full_name} as expected".format(
                username=username,
                full_name=output[SystemConsts.USER_ADMIN_DEFAULT_FULL_NAME],
                new_full_name=new_full_name)

    def action_disconnect(self, username=''):
        self.set_username(username)
        return SendCommandTool.execute_command_expected_str(self.api_obj[TestToolkit.tested_api].action_disconnect,
                                                            "Action succeeded", TestToolkit.engines.dut,
                                                            self.get_resource_path().replace('/',
                                                                                             ' ')).get_returned_value()

    def set_username(self, username):
        self.username = username
        self._resource_path = '/user/' + self.username

    @staticmethod
    def generate_username(is_valid=True, random_length=True, length=SystemConsts.USERNAME_MAX_LEN,
                          not_usernames=[SystemConsts.DEFAULT_USER_ADMIN, SystemConsts.DEFAULT_USER_MONITOR],
                          characters=SystemConsts.USERNAME_VALID_CHARACTERS):
        """
        if valid will generate username starts with _ or A-Z or a-z
        else : the username will start with 0-9 or *
        :param is_valid: if is True, the username need to be valid, False- the username invalid.
        :param random_length: True if the username length need to be randomly
        :param length: the max length of the username if random_length is True, else - this is the length of the username
        :param not_usernames: list of the usernames that we don't want to generate.
        :param characters: random username with those characters
        :return:
        """
        with allure.step('generate random username'):
            if random_length:
                name_len = random.randint(3, length)
                logger.info('the username length will be : {len}'.format(len=name_len))
            else:
                name_len = length

            name = "".join(random.choice(characters) for _ in range(name_len))
            while name in not_usernames:
                name = "".join(random.choice(characters) for _ in range(name_len))

            if not is_valid:
                name = str(random.choice(SystemConsts.USERNAME_INVALID_CHARACTERS)) + name[:-1]
            logger.info('generated username is : {username}'.format(username=name))
            return name