import copy
import logging
from typing import List

from ngts.nvos_tools.system.Ldap import Ldap
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts
from ngts.tools.test_utils import allure_utils as allure
from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.Hostname import Hostname, HostnameId
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import configure_resource
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class RemoteAaaServerInfo:
    def __init__(self, hostname, priority, secret, port, users: List[UserInfo]):
        self.hostname = hostname
        self.priority = priority
        self.secret = secret
        self.port = port
        self.users = users

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)

    def configure(self, engines, hostname_resource_obj: HostnameId, set_explicit_priority=False, apply=False,
                  dut_engine=None):
        raise Exception('Method "configure" is not implemented!')

    def _configure(self, engines, hostname_resource_obj: HostnameId, conf_to_set: dict, set_explicit_priority: bool,
                   apply: bool, dut_engine: ProxySshEngine = None):
        if set_explicit_priority:
            conf_to_set[AaaConsts.PRIORITY] = self.priority
        configure_resource(engines, resource_obj=hostname_resource_obj, conf=conf_to_set, apply=apply,
                           dut_engine=dut_engine)


def update_active_aaa_server(item, server: RemoteAaaServerInfo):
    item.active_remote_aaa_server = server
    if server is None:
        with allure.step('Change active remote auth server to None'):
            item.active_remote_aaa_server = None
            item.active_remote_admin_engine = None
    else:
        with allure.step('Update to new active remote auth server'):
            item.active_remote_auth_server = server
        with allure.step('Create ssh engine with remote admin user'):
            logging.info('Find remote admin user to use')
            remote_admin = [user for user in server.users if user.role == 'admin'][0]
            logging.info(f'Create ssh engine with user: {remote_admin.username}')
            item.active_remote_admin_engine = ProxySshEngine(device_type=TestToolkit.engines.dut.device_type,
                                                             ip=TestToolkit.engines.dut.ip,
                                                             username=remote_admin.username,
                                                             password=remote_admin.password)


class TacacsServerInfo(RemoteAaaServerInfo):
    def __init__(self, hostname, priority, secret, port, timeout, auth_type, users: List[UserInfo]):
        super().__init__(hostname, priority, secret, port, users)
        self.timeout = timeout
        # self.retransmit = retransmit
        self.auth_type = auth_type

    def configure(self, engines, hostname_resource_obj: HostnameId, set_explicit_priority=False, apply=False,
                  dut_engine=None):
        conf_to_set = {
            AaaConsts.SECRET: self.secret,
            AaaConsts.PORT: self.port,
            AaaConsts.TIMEOUT: self.timeout,
            AaaConsts.AUTH_TYPE: self.auth_type
            # AaaConsts.RETRANSMIT: server.retransmit
        }
        self._configure(engines, hostname_resource_obj, conf_to_set, set_explicit_priority, apply, dut_engine)


class LdapServerInfo(RemoteAaaServerInfo):
    def __init__(self, hostname, priority, secret, port, users: List[UserInfo],
                 base_dn, bind_dn, group_attr,
                 timeout_bind, timeout_search, version, ssl_port=636):
        super().__init__(hostname, priority, secret, port, users)
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.group_attr = group_attr
        self.timeout_bind = timeout_bind
        self.timeout_search = timeout_search
        self.version = version
        self.ssl_port = ssl_port

    def configure(self, engines, hostname_resource_obj: HostnameId, set_explicit_priority=False, apply=False,
                  dut_engine=None):
        ldap_obj: Ldap = hostname_resource_obj.parent_obj.parent_obj
        hostname_resource_obj.set(dut_engine=dut_engine)
        conf_to_set = {
            LdapConsts.SECRET: self.secret,
            LdapConsts.PORT: self.port,
            LdapConsts.BASE_DN: self.base_dn,
            LdapConsts.BIND_DN: self.bind_dn,
            LdapConsts.GROUP_ATTR: self.group_attr,
            LdapConsts.VERSION: self.version,
            # LdapConsts.HOSTNAME: self.hostname
        }
        configure_resource(engines, resource_obj=ldap_obj, conf=conf_to_set, apply=False, dut_engine=dut_engine)
        ldap_obj.ssl.set(LdapConsts.SSL_CERT_VERIFY, LdapConsts.DISABLED, dut_engine=dut_engine).verify_result()
        self._configure(engines, hostname_resource_obj, {}, set_explicit_priority, apply, dut_engine)
