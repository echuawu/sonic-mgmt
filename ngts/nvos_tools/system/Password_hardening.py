import json
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.constants.constants_nvos import ApiType, SystemConsts
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.cli_wrappers.openapi.openapi_system_clis import OpenApiSystemCli


class Password_hardening(BaseComponent):

    def __init__(self, parent_obj):
        BaseComponent.__init__(self)
        self.api_obj = {ApiType.NVUE: NvueSystemCli, ApiType.OPENAPI: OpenApiSystemCli}
        self._resource_path = '/password-hardening'
        self.parent_obj = parent_obj

    @staticmethod
    def parse_password_hardening_enabled_rules(password_hardening_output):
        """

        :param password_hardening_output: nv show system security output
        :return:
        """
        output_dictionary = json.loads(password_hardening_output)[SystemConsts.PASSWORD_HARDENING_LABEL]
        rules = [key for key in SystemConsts.PASSWORD_HARDENING_DEFAULT if output_dictionary[key] == SystemConsts.USER_STATE_ENABLED]

        if output_dictionary[SystemConsts.USERNAME_PASSWORD_HARDENING_STATE] == SystemConsts.USER_STATE_DISABLED:
            rules = SystemConsts.PASSWORD_HARDENING_DEFAULT

        return output_dictionary[SystemConsts.USERNAME_PASSWORD_LENGTH_LABEL], rules
