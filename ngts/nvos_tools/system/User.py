import logging
import allure
import random
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli
from ngts.nvos_tools.system.Role import Role

logger = logging.getLogger()


class User(BaseComponent):
    def __init__(self, parent_obj=None, username=''):
        BaseComponent.__init__(self)
        self.password = Password(self)
        self.full_name = FullName(self)
        self.state = State(self)
        self.role = Role(self)
        self.username = username
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/user/' + self.username
        self.parent_obj = parent_obj

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
                name_len = random.randint(1, length)
                logger.info('the username length will be : {len}'.format(len=name_len))
            else:
                name_len = length

            name = "".join(random.choice(characters) for _ in range(name_len))
            while name in not_usernames:
                name = "".join(random.choice(characters) for _ in range(name_len))

            if not is_valid:
                name = str(random.choice(SystemConsts.USERNAME_INVALID_CHARACTERS)) + name[:-1]
            logger.info('generated username is : {username}'.format(username=name))
            return ResultObj(True, "", name)


class Password(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/password'
        self.parent_obj = parent_obj


class FullName(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/full-name'
        self.parent_obj = parent_obj


class State(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/state'
        self.parent_obj = parent_obj
