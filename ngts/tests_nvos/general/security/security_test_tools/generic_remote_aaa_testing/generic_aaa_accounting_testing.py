import logging
import random
import time

from typing import Dict, List, Callable, Any
from infra.tools.linux_tools.linux_tools import LinuxSshEngine

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.Aaa import Aaa
from ngts.nvos_tools.system.Hostname import HostnameId
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AccountingFields, AddressingType, AuthConsts, AuthType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import *
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_aaa_testing_utils import \
    detach_config
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import wait_for_ldap_nvued_restart_workaround
from ngts.tests_nvos.general.security.security_test_tools.resource_utils import configure_resource
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import verify_users_auth, verify_user_auth
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.AaaServerManager import AaaAccountingLogsFileContent, AaaServerManager
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo, \
    update_active_aaa_server
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tools.test_utils import allure_utils as allure
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts


def generic_aaa_test_accounting_basic(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                      remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                      server: RemoteAaaServerInfo, skip_local_users: bool = True):
    """
    @summary: Verify accounting basic functionality

        Steps:
        1. configure remote-aaa
        2. disable accounting
        3. enable remote-aaa
        4. verify no accounting logs on server
        5. enable accounting
        6. verify accounting logs on server only for remote-aaa users events

    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server: object containing remote server info
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure {remote_aaa_type}'):
        server.configure(engines)

    with allure.step(f'Set {remote_aaa_type} accounting disabled'):
        remote_aaa_obj.accounting.set(AccountingFields.STATE, AaaConsts.DISABLED).verify_result()

    with allure.step(f'Enable {remote_aaa_type}'):
        remote_aaa_obj.enable(failthrough=True, apply=True, engine=engines.dut, verify_res=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify no accounting logs on {remote_aaa_type} server'):
        with allure.step(f'Verify no logs for {remote_aaa_type} admin user'):
            remote_adm_user: UserInfo = [user for user in server.users if user.role == AaaConsts.ADMIN][0]
            verify_user_auth(engines, topology_obj, remote_adm_user, True, accounting_servers=[server], expect_accounting_logs=[False])

        with allure.step(f'Verify no logs for {remote_aaa_type} monitor user'):
            remote_mon_user: UserInfo = [user for user in server.users if user.role == AaaConsts.MONITOR][0]
            verify_user_auth(engines, topology_obj, remote_mon_user, True, accounting_servers=[server], expect_accounting_logs=[False])

        with allure.step('Verify no logs for local user'):
            verify_user_auth(engines, topology_obj, local_adminuser, True, accounting_servers=[server], expect_accounting_logs=[False])

    with allure.step(f'Set {remote_aaa_type} accounting enabled'):
        remote_aaa_obj.accounting.set(AccountingFields.STATE, AaaConsts.ENABLED, apply=True).verify_result()
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify accounting logs appear for {remote_aaa_type} users only'):
        with allure.step(f'Verify logs exist for {remote_aaa_type} admin user'):
            remote_adm_user: UserInfo = [user for user in server.users if user.role == AaaConsts.ADMIN][0]
            verify_user_auth(engines, topology_obj, remote_adm_user, True, accounting_servers=[server], expect_accounting_logs=[True])

        with allure.step(f'Verify logs exist for {remote_aaa_type} monitor user'):
            remote_mon_user: UserInfo = [user for user in server.users if user.role == AaaConsts.MONITOR][0]
            verify_user_auth(engines, topology_obj, remote_mon_user, True, accounting_servers=[server], expect_accounting_logs=[True])

        if not skip_local_users:
            with allure.step('Verify no logs for local user'):
                verify_user_auth(engines, topology_obj, local_adminuser, True, accounting_servers=[server], expect_accounting_logs=[False])


def generic_aaa_test_accounting_top_server_only(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                                remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                                server1: RemoteAaaServerInfo, server2: RemoteAaaServerInfo, skip_local_users: bool = True):
    """
    @summary: Verify that accounting logs are sent to top server only

        Steps:
        1. configure remote-aaa with 2 servers
        2. enable accounting
        3. enable remote-aaa
        4. verify accounting logs on top server only for remote-aaa users events

    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server1: object containing top remote server info
    @param server2: object containing 2nd remote server info
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure {remote_aaa_type} servers'):
        server1.configure(engines, set_explicit_priority=True)
        server2.configure(engines, set_explicit_priority=True)

    with allure.step(f'Set {remote_aaa_type} accounting enabled'):
        remote_aaa_obj.accounting.set(AccountingFields.STATE, AaaConsts.ENABLED)

    with allure.step(f'Enable {remote_aaa_type}'):
        remote_aaa_obj.enable(failthrough=True, apply=True, engine=engines.dut, verify_res=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify accounting logs appear for {remote_aaa_type} users on 1st server ({server1.hostname}) only'):
        with allure.step(f'Verify logs exist for {remote_aaa_type}1 user'):
            server1_user: UserInfo = random.choice(server1.users)
            verify_user_auth(engines, topology_obj, server1_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if remote_aaa_type != RemoteAaaType.LDAP:  # with LDAP - 2nd server user cant auth even with failthrough enabled
            with allure.step(f'Verify logs exist for {remote_aaa_type}2 user'):
                server2_user: UserInfo = random.choice(server2.users)
                verify_user_auth(engines, topology_obj, server2_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if not skip_local_users:
            with allure.step(f'Verify no logs for local user'):
                verify_user_auth(engines, topology_obj, local_adminuser, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[False, False])


def generic_aaa_test_accounting_unreachable_top_server(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                                       remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                                       server1: RemoteAaaServerInfo, server2: RemoteAaaServerInfo, skip_local_users: bool = True):
    """
    @summary: Verify that when top server becomes unreachable, accounting logs are sent to next available server only

        Steps:
        1. configure remote-aaa with several top unreachable servers
        2. configure also reachable server with lower priority
        3. enable accounting
        4. enable remote-aaa
        5. verify accounting logs on top available server only for remote-aaa users events
        6. make unreachable server reachable
        7. verify accounting logs now on the top reachable server

    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server1: object containing top remote server info
    @param server2: object containing 2nd remote server info
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure 2 real {remote_aaa_type} below several unreachable servers'):
        server2.priority = 1
        server1.priority = 2
        remote_aaa_obj.set(AaaConsts.SECRET, 'secret')
        # remote_aaa_obj.hostname.hostname_id['3.3.3.3'].set(AaaConsts.PRIORITY, 3)
        # remote_aaa_obj.hostname.hostname_id['4.4.4.4'].set(AaaConsts.PRIORITY, 4)
        # remote_aaa_obj.hostname.hostname_id['5.5.5.5'].set(AaaConsts.PRIORITY, 5)
        # remote_aaa_obj.hostname.hostname_id['6.6.6.6'].set(AaaConsts.PRIORITY, 6)
        server1.configure(engines, set_explicit_priority=True)
        server2.configure(engines, set_explicit_priority=True)

    with allure.step(f'Set {remote_aaa_type} accounting enabled'):
        remote_aaa_obj.accounting.set(AccountingFields.STATE, AaaConsts.ENABLED)

    with allure.step(f'Enable {remote_aaa_type}'):
        remote_aaa_obj.enable(failthrough=True, apply=True, engine=engines.dut, verify_res=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify accounting logs appear for {remote_aaa_type} users on 1st available server ({server1.hostname}) only'):
        with allure.step(f'Verify logs exist for {remote_aaa_type}1 user'):
            server1_user: UserInfo = random.choice(server1.users)
            verify_user_auth(engines, topology_obj, server1_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if remote_aaa_type != RemoteAaaType.LDAP:  # with LDAP - 2nd server user cant auth even with failthrough enabled
            with allure.step(f'Verify logs exist for {remote_aaa_type}2 user'):
                server2_user: UserInfo = random.choice(server2.users)
                verify_user_auth(engines, topology_obj, server2_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if not skip_local_users:
            with allure.step(f'Verify no logs for local user'):
                verify_user_auth(engines, topology_obj, local_adminuser, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[False, False])

    with allure.step(f'Make server1 ({server1.hostname}) also unreachable'):
        server1.make_unreachable(engines, apply=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify accounting logs appear for {remote_aaa_type} users on 1st available server ({server2.hostname}) only'):
        with allure.step(f'Verify logs exist for {remote_aaa_type}2 user'):
            server2_user: UserInfo = random.choice(server2.users)
            verify_user_auth(engines, topology_obj, server2_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[False, True])

        if not skip_local_users:
            with allure.step(f'Verify no logs for local user'):
                verify_user_auth(engines, topology_obj, local_adminuser, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[False, False])

    with allure.step(f'Make server1 ({server1.hostname}) reachable again'):
        server1.make_reachable(engines, apply=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Verify accounting logs appear for {remote_aaa_type} users on 1st available server ({server1.hostname}) only'):
        with allure.step(f'Verify logs exist for {remote_aaa_type}1 user'):
            server1_user: UserInfo = random.choice(server1.users)
            verify_user_auth(engines, topology_obj, server1_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if remote_aaa_type != RemoteAaaType.LDAP:  # with LDAP - 2nd server user cant auth even with failthrough enabled
            with allure.step(f'Verify logs exist for {remote_aaa_type}2 user'):
                server2_user: UserInfo = random.choice(server2.users)
                verify_user_auth(engines, topology_obj, server2_user, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[True, False])

        if not skip_local_users:
            with allure.step(f'Verify no logs for local user'):
                verify_user_auth(engines, topology_obj, local_adminuser, True, verify_authorization=False, accounting_servers=[server1, server2], expect_accounting_logs=[False, False])


def generic_aaa_test_accounting_local_first(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                            remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                            server: RemoteAaaServerInfo):
    """
    @summary: Verify that accounting logs are not sent when authentication order is local,aaa

        Steps:
        1. configure remote-aaa
        2. enable accounting
        3. enable remote-aaa - auth order aaa,local
        4. connect remote user and make some operation
        5. turn auth order to local,aaa while remote user still connected
        6. make another op with connected remote user
        7. verify no accounting logs sent

    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server: object containing remote server info
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure {remote_aaa_type} server'):
        remote_user: UserInfo = random.choice(server.users)
        server.configure(engines, set_explicit_priority=True)

    with allure.step(f'Set {remote_aaa_type} accounting enabled'):
        remote_aaa_obj.accounting.set(AccountingFields.STATE, AaaConsts.ENABLED)

    with allure.step(f'Enable {remote_aaa_type}'):
        remote_aaa_obj.enable(failthrough=True, apply=True, engine=engines.dut, verify_res=True)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step(f'Connect {remote_aaa_type} user "{remote_user.username}" and make operation'):
        remote_user_engine: LinuxSshEngine = LinuxSshEngine(engines.dut.ip, remote_user.username, remote_user.password)
        pwh = System(force_api=ApiType.NVUE).security.password_hardening
        pwh.set(PwhConsts.LEN_MIN, 19, dut_engine=remote_user_engine)

    with allure.step(f'Turn authentication order to local,{remote_aaa_type}'):
        System().aaa.authentication.set(AuthConsts.ORDER, f'local,{remote_aaa_type}', apply=True).verify_result()
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step('Clean accounting logs on server'):
        server_mngr = AaaServerManager(server.ipv4_addr, server.docker_name)
        server_mngr.clear_accounting_logs()

    with allure.step(f'Make another operation with already connected {remote_aaa_type} user "{remote_user.username}"'):
        pwh.set(PwhConsts.LEN_MIN, 20, dut_engine=remote_user_engine)
        pwh.unset(PwhConsts.LEN_MIN, dut_engine=remote_user_engine)

    expect_logs = True
    with allure.step(f'Verify {"" if expect_logs else "no "}logs for these operations'):
        with allure.step(f'Check accounting on server: {server_mngr.ip} , Expect logs: {expect_logs}'):
            accounting_logs: AaaAccountingLogsFileContent = server_mngr.cat_accounting_logs(grep=remote_user.username)
            assert bool(accounting_logs.logs) == expect_logs, f'There are {"no " if expect_logs else ""}accounting logs on server "{server_mngr.ip}" for user "{remote_user.username}", while expected {"" if expect_logs else "not "}to have logs.\nActual raw content:\n{accounting_logs.raw_content}'

    with allure.step(f'Verify no logs for new remote connection'):
        verify_user_auth(engines, topology_obj, remote_user, True, verify_authorization=False, accounting_servers=[server], expect_accounting_logs=[expect_logs])