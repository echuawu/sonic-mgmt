import copy
import logging
from typing import List, Dict

from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.Hostname import HostnameId
from ngts.nvos_tools.system.Ldap import Ldap
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.resource_utils import configure_resource
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts
from ngts.tools.test_utils import allure_utils as allure


class RemoteAaaServerInfo:
    def __init__(self, hostname, priority, secret, port, users: List[UserInfo], ipv4_addr: str = '',
                 docker_name: str = ''):
        self.hostname = hostname
        self.priority = priority
        self.secret = secret
        self.port = port
        self.users = users
        # info for mgmt of server
        self.ipv4_addr = ipv4_addr
        self.docker_name = docker_name

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)

    def configure(self, engines, set_explicit_priority=False, apply=False, dut_engine=None):
        raise Exception('Method "configure" is not implemented!')

    def _configure(self, engines, hostname_resource_obj: HostnameId, conf_to_set: dict, set_explicit_priority: bool,
                   apply: bool, dut_engine: ProxySshEngine = None):
        if set_explicit_priority:
            conf_to_set[AaaConsts.PRIORITY] = self.priority
        configure_resource(engines, resource_obj=hostname_resource_obj, conf=conf_to_set, apply=apply,
                           verify_apply=False, dut_engine=dut_engine)

    def make_unreachable(self, engines, apply=False, dut_engine=None):
        raise Exception('Method "configure" is not implemented!')

    def make_reachable(self, engines, apply=False, dut_engine=None):
        raise Exception('Method "configure" is not implemented!')


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
    def __init__(self, hostname, priority, secret, port, timeout, auth_type, users: List[UserInfo], ipv4_addr: str = '',
                 docker_name: str = '', users_per_auth_type: Dict[str, List[UserInfo]] = None):
        super().__init__(hostname, priority, secret, port, users, ipv4_addr, docker_name)
        self.timeout = timeout
        # self.retransmit = retransmit
        self.auth_type = auth_type
        self.users_per_auth_type = users_per_auth_type

    def configure(self, engines, set_explicit_priority=False, apply=False, dut_engine=None):
        conf_to_set = {
            AaaConsts.SECRET: self.secret,
            AaaConsts.PORT: self.port,
            AaaConsts.TIMEOUT: self.timeout,
            AaaConsts.AUTH_TYPE: self.auth_type
            # AaaConsts.RETRANSMIT: server.retransmit
        }
        hostname_resource_obj = System().aaa.tacacs.hostname.hostname_id[self.hostname]
        self._configure(engines, hostname_resource_obj, conf_to_set, set_explicit_priority, apply, dut_engine)

    def make_unreachable(self, engines, apply=False, dut_engine=None):
        System().aaa.tacacs.hostname.hostname_id[self.hostname].set(AaaConsts.PORT, AaaConsts.AAA_SERVER_BAD_PORT, apply=apply,
                                                                    dut_engine=dut_engine)

    def make_reachable(self, engines, apply=False, dut_engine=None):
        System().aaa.tacacs.hostname.hostname_id[self.hostname].set(AaaConsts.PORT, self.port, apply=apply,
                                                                    dut_engine=dut_engine)

    def update_auth_type(self, auth_type: str, item, dut_engine=None, set_on_dut: bool = True):
        logging.info(f'Update server info of "{self.hostname} - {self.port}" users to use {auth_type} passwords')
        self.auth_type = auth_type
        self.users = self.users_per_auth_type[auth_type]

        if set_on_dut:
            assert item, f"argument 'item' was not provided"
            engine = dut_engine or (
                item.active_remote_admin_engine if hasattr(item, 'active_remote_admin_engine') else None)
            System().aaa.tacacs.hostname.hostname_id[self.hostname].set(AaaConsts.AUTH_TYPE, auth_type, apply=True,
                                                                        dut_engine=engine)


class LdapServerInfo(RemoteAaaServerInfo):
    def __init__(self, hostname, priority, secret, port, users: List[UserInfo],
                 base_dn, bind_dn, timeout_bind, timeout_search, version,
                 ssl_port=636, ipv4_addr: str = '', docker_name: str = ''):
        super().__init__(hostname, priority, secret, port, users, ipv4_addr, docker_name)
        self.base_dn = base_dn
        self.bind_dn = bind_dn
        self.timeout_bind = timeout_bind
        self.timeout_search = timeout_search
        self.version = version
        self.ssl_port = ssl_port

    def configure(self, engines, set_explicit_priority=False, apply=False, dut_engine=None):
        ldap_obj: Ldap = System().aaa.ldap
        hostname_resource_obj = ldap_obj.hostname.hostname_id[self.hostname]
        hostname_resource_obj.set(dut_engine=dut_engine)
        conf_to_set = {
            LdapConsts.SECRET: self.secret,
            LdapConsts.PORT: self.port,
            LdapConsts.BASE_DN: self.base_dn,
            LdapConsts.BIND_DN: self.bind_dn,
            LdapConsts.VERSION: self.version,
            # LdapConsts.HOSTNAME: self.hostname
        }
        configure_resource(engines, resource_obj=ldap_obj, conf=conf_to_set, apply=False, dut_engine=dut_engine)
        ldap_obj.ssl.set(LdapConsts.SSL_CERT_VERIFY, LdapConsts.DISABLED, dut_engine=dut_engine).verify_result()
        self._configure(engines, hostname_resource_obj, {}, set_explicit_priority, apply, dut_engine)

    def make_unreachable(self, engines, apply=False, dut_engine=None):
        ldap = System().aaa.ldap
        ldap.hostname.hostname_id[self.hostname].unset(apply=False, dut_engine=dut_engine)
        ldap.hostname.hostname_id['unreachable-' + self.hostname].set(AaaConsts.PRIORITY, self.priority,
                                                                      apply=apply, dut_engine=dut_engine)

    def make_reachable(self, engines, apply=False, dut_engine=None):
        ldap = System().aaa.ldap
        ldap.hostname.hostname_id['unreachable-' + self.hostname].unset(apply=False, dut_engine=dut_engine)
        ldap.hostname.hostname_id[self.hostname].set(AaaConsts.PRIORITY, self.priority,
                                                     apply=apply, dut_engine=dut_engine)


class RadiusServerInfo(RemoteAaaServerInfo):
    def __init__(self, hostname, priority, secret, port, timeout, auth_type, users: List[UserInfo], ipv4_addr: str = '',
                 docker_name: str = ''):
        super().__init__(hostname, priority, secret, port, users, ipv4_addr, docker_name)
        self.timeout = timeout
        self.auth_type = auth_type

    def configure(self, engines, set_explicit_priority=False, apply=False, dut_engine=None):
        conf_to_set = {
            AaaConsts.SECRET: self.secret,
            AaaConsts.PORT: self.port,
            AaaConsts.TIMEOUT: self.timeout,
            AaaConsts.AUTH_TYPE: self.auth_type
        }
        hostname_resource_obj = System().aaa.radius.hostname.hostname_id[self.hostname]
        self._configure(engines, hostname_resource_obj, conf_to_set, set_explicit_priority, apply, dut_engine)

    def make_unreachable(self, engines, apply=False, dut_engine=None):
        System().aaa.radius.hostname.hostname_id[self.hostname].set(AaaConsts.PORT, AaaConsts.AAA_SERVER_BAD_PORT,
                                                                    apply=apply, dut_engine=dut_engine)

    def make_reachable(self, engines, apply=False, dut_engine=None):
        System().aaa.radius.hostname.hostname_id[self.hostname].set(AaaConsts.PORT, self.port, apply=apply,
                                                                    dut_engine=dut_engine)

    def update_auth_type(self, auth_type: str, item, dut_engine=None, set_on_dut: bool = True):
        logging.info(f'Update server info of "{self.hostname} - {self.port}" users to use {auth_type} passwords')
        self.auth_type = auth_type

        if set_on_dut:
            assert item, f"argument 'item' was not provided"
            engine = dut_engine or (
                item.active_remote_admin_engine if hasattr(item, 'active_remote_admin_engine') else None)
            System().aaa.radius.hostname.hostname_id[self.hostname].set(AaaConsts.AUTH_TYPE, auth_type, apply=True,
                                                                        dut_engine=engine)
