import re
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts, AuthConsts
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType


class Ldap(RemoteAaaResource):

    def __init__(self, parent_obj=None):
        super().__init__(parent_obj)
        self._resource_path = '/ldap'
        self.ssl = BaseComponent(self, path='/ssl')
        self.filter = LdapFilter(self)
        self.map = LdapMap(self)

    def enable(self, failthrough=False, apply=False, engine=None, verify_res=False):
        authentication: BaseComponent = self.parent_obj.authentication
        authentication.set(AuthConsts.ORDER, f'{RemoteAaaType.LDAP},{AuthConsts.LOCAL}', dut_engine=engine).verify_result()
        failthrough_val = AaaConsts.ENABLED if failthrough else AaaConsts.DISABLED
        res = authentication.set(AuthConsts.FAILTHROUGH, failthrough_val, apply=apply, dut_engine=engine)
        if verify_res:
            res.verify_result()


class LdapFilter(BaseComponent):

    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/filter')

    def set(self, op_param_name="", op_param_value={}, expected_str='', apply=False, ask_for_confirmation=False,
            dut_engine=None):
        if TestToolkit.tested_api == ApiType.NVUE:
            pattern = r'^"(.*)"$'
            value_wrapped_with_dquotes = isinstance(op_param_value, str) and bool(re.match(pattern, op_param_value))
            if not value_wrapped_with_dquotes:
                op_param_value = f'"{op_param_value}"'  # filter values may contain special chars like '&', '!', etc

        return super().set(op_param_name, op_param_value, expected_str, apply, ask_for_confirmation, dut_engine)


class LdapMap(BaseComponent):

    def __init__(self, parent_obj=None):
        super().__init__(parent=parent_obj, path='/map')
        self.passwd = BaseComponent(self, path='/passwd')
        self.group = BaseComponent(self, path='/group')
        self.shadow = BaseComponent(self, path='/shadow')


# class Ldap(BaseComponent):
#     def __init__(self, parent_obj=None):
#         BaseComponent.__init__(self, parent=parent_obj, path='/ldap')
#         self.hostname = LdapHostname(self)
#         self.ssl = BaseComponent(self, path='/ssl')
#
#
# class LdapHostname(BaseComponent):
#     def __init__(self, parent_obj=None):
#         BaseComponent.__init__(self, parent=parent_obj, path='/hostname')
#
#     def set_priority(self, hostname, priority, apply=False, ask_for_confirmation=False):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.set("priority", priority, apply=apply, ask_for_confirmation=ask_for_confirmation)
#
#     def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)
#
#     def show_hostname(self, hostname):
#         ldap_hostname = BaseComponent(self, path='/' + hostname)
#         return ldap_hostname.show()
