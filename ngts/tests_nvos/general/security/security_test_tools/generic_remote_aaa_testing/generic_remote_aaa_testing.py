import logging
import random
import time

from typing import Dict, List, Callable, Any

from ngts.nvos_constants.constants_nvos import ApiType, ConfState
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool, wait_until_cli_is_up
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
from ngts.tests_nvos.general.security.security_test_tools.resource_utils import configure_resource
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import verify_users_auth, verify_user_auth
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo, \
    update_active_aaa_server
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tools.test_utils import allure_utils as allure


def generic_aaa_test_set_unset_show(test_api, engines, remote_aaa_type: str, main_resource_obj: RemoteAaaResource,
                                    confs: Dict[BaseComponent, dict],
                                    hostname_conf: dict,
                                    default_confs: Dict[BaseComponent, dict]):
    """
    @summary: Verify set, unset, show commands for remote AAA feature

        Steps:
        1. set general/global configurations
        2. set hostnames
            1- with default configuration
            2- with new configuration
        3. apply changes
        4. verify new configurations with show commands
            1- general configurations as required
            2- hostname1 configuration as default
            3- hostname2 configuration as required
        5. unset configurations
        6. verify default configuration
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param main_resource_obj: BaseComponent object representing the feature resource
    @param confs: configurations to set
    @param hostname_conf: configuration for hostname2 (the non-default one)
    @param default_confs: default configurations
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'

    TestToolkit.tested_api = test_api

    with allure.step('Set general configuration'):
        for resource, conf in confs.items():
            configure_resource(engines, resource, conf)

    with allure.step('Set hostnames'):
        hostname1 = '1.2.3.4'
        hostname2 = '2.3.4.5'
        main_resource_obj.hostname.set(hostname1)
        configure_resource(engines, main_resource_obj.hostname.hostname_id[hostname2], hostname_conf, apply=True)

    with allure.step('Verify general configurations'):
        for resource, expected_conf in confs.items():
            with allure.step(f'Verify {resource.get_resource_path()} configuration'):
                cur_conf = OutputParsingTool.parse_json_str_to_dictionary(resource.show()).get_returned_value()
                if AaaConsts.SECRET in expected_conf.keys():
                    expected_conf[AaaConsts.SECRET] = '*'
                ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                                expected_values=expected_conf.values(),
                                                                output_dict=cur_conf).verify_result()

    with allure.step('Verify hostnames exist in show output'):
        show_rev_param = '' if remote_aaa_type == RemoteAaaType.LDAP else ConfState.APPLIED
        show_hostname_output = OutputParsingTool.parse_json_str_to_dictionary(
            main_resource_obj.hostname.show(rev=show_rev_param)).get_returned_value()
        ValidationTool.verify_field_exist_in_json_output(show_hostname_output, [hostname1, hostname2]).verify_result()

    with allure.step('Verify hostnames configurations'):
        with allure.step(f'Verify default configuration for hostname {hostname1}'):
            global_conf = OutputParsingTool.parse_json_str_to_dictionary(main_resource_obj.show()).get_returned_value()
            expected_conf = {
                key: 1 if key == AaaConsts.PRIORITY else global_conf[key]
                for key in hostname_conf.keys()
            } if remote_aaa_type == RemoteAaaType.LDAP else {AaaConsts.PRIORITY: 1}
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname1].show(rev=show_rev_param)).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

        with allure.step(f'Verify new configuration for hostname {hostname2}'):
            expected_conf = hostname_conf
            if AaaConsts.SECRET in expected_conf.keys():
                expected_conf[AaaConsts.SECRET] = '*'
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname2].show(rev=show_rev_param)).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

    if list(hostname_conf.keys()) != [AaaConsts.PRIORITY]:
        with allure.step(f'Clear hostname {hostname2} configuration'):
            for field in hostname_conf.keys():
                if field != AaaConsts.PRIORITY:
                    main_resource_obj.hostname.hostname_id[hostname2].unset(field).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut,
                                            True).verify_result()
        with allure.step(f'Verify default configuration for hostname {hostname2}'):
            global_conf = OutputParsingTool.parse_json_str_to_dictionary(main_resource_obj.show(rev=show_rev_param)).get_returned_value()
            expected_conf = {
                key: 2 if key == AaaConsts.PRIORITY else global_conf[key]
                for key in hostname_conf.keys()
            } if remote_aaa_type == RemoteAaaType.LDAP else {AaaConsts.PRIORITY: 2}
            cur_hostname_conf = OutputParsingTool.parse_json_str_to_dictionary(
                main_resource_obj.hostname.hostname_id[hostname2].show(rev=show_rev_param)).get_returned_value()
            ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                            expected_values=expected_conf.values(),
                                                            output_dict=cur_hostname_conf).verify_result()

    with allure.step('Unset configuration'):
        main_resource_obj.unset(apply=True).verify_result()

    with allure.step('Verify default configuration with show command'):
        for resource, expected_conf in default_confs.items():
            with allure.step(f'Verify default configuration for {resource.get_resource_path()}'):
                cur_conf = OutputParsingTool.parse_json_str_to_dictionary(resource.show(rev=show_rev_param)).get_returned_value()
                if AaaConsts.SECRET in expected_conf.keys():
                    # expected_conf[AaaConsts.SECRET] = '*'
                    del expected_conf[AaaConsts.SECRET]
                ValidationTool.validate_fields_values_in_output(expected_fields=expected_conf.keys(),
                                                                expected_values=expected_conf.values(),
                                                                output_dict=cur_conf).verify_result()


def generic_aaa_test_set_invalid_param(test_api,
                                       field_is_numeric: Dict[str, bool],
                                       valid_values: dict,
                                       resources_and_fields: Dict[BaseComponent, List[str]]):
    """
    @summary: Verify set, unset, show commands for remote AAA feature

        Flow:
        - for every given resource (related to AAA feature):
            - go over all fields, set it with invalid value, and verify failure
    @param test_api: api to use
    @param field_is_numeric: dictionary for each field, whether it is numeric or not
    @param valid_values: dictionary for each field, it's valid values
    @param resources_and_fields: dictionary containing resource object as key, and it's list of fields to set as value
    """
    TestToolkit.tested_api = test_api

    def check_invalid_set_to_resource(resource_obj, field_name):
        if TestToolkit.tested_api == ApiType.NVUE and field_name != AaaConsts.SECRET:
            logging.info(f'Set {field_name} to: nothing (incomplete)')
            resource_obj.set(field_name, '').verify_result(False)

        if valid_values[field_name] != str:
            invalid_value = RandomizationTool.get_random_string(6)
            logging.info(f'Set {field_name} to: {invalid_value}')
            resource_obj.set(field_name, invalid_value).verify_result(False)

        if field_is_numeric[field_name]:
            invalid_value = RandomizationTool.select_random_value(
                list_of_values=list(range(-1000, 1000)),
                forbidden_values=valid_values[field_name]).get_returned_value()
            logging.info(f'Set {field_name} to: {invalid_value}')
            resource_obj.set(field_name, invalid_value).verify_result(False)

        if field_name == AaaConsts.SECRET:
            logging.info(f'Set {field_name} to: empty string (\'""\')')
            resource_obj.set(field_name, '""', apply=True).verify_result(False)
            detach_config()

    for resource, fields in resources_and_fields.items():
        for field in fields:
            with allure.step(f'Check invalid {field} for {resource.get_resource_path()}'):
                check_invalid_set_to_resource(resource, field)


def auth_testing(engines, topology_obj, local_adminuser: UserInfo, remote_aaa_type: str, server: RemoteAaaServerInfo,
                 skip_auth_mediums: List[str] = None):
    with allure.step(f'Sleep for {RemoteAaaConsts.WAIT_TIME_BEFORE_AUTH} seconds'):
        time.sleep(RemoteAaaConsts.WAIT_TIME_BEFORE_AUTH)
    with allure.step(f'Verify auth with {remote_aaa_type} user - expect success'):
        verify_users_auth(engines, topology_obj, server.users, skip_auth_mediums=skip_auth_mediums)
    with allure.step(f'Verify auth with non {remote_aaa_type} user - expect fail'):
        verify_user_auth(engines, topology_obj, local_adminuser, expect_login_success=False,
                         skip_auth_mediums=skip_auth_mediums)


def wait_for_ldap_nvued_restart_workaround(test_item, engine_to_use=None):
    with allure.step('After LDAP configuration - wait for NVUE restart Workaround'):
        sleep_time = 6
        with allure.step(f'Sleep {sleep_time} seconds'):
            time.sleep(sleep_time)
        if not engine_to_use:
            engine_to_use = test_item.active_remote_admin_engine
        engine_to_use.disconnect()
        with allure.step(f'Start checking connection and services - using user "{engine_to_use.username}"'):
            wait_until_cli_is_up(engine=engine_to_use)
            # DutUtilsTool.wait_for_nvos_to_become_functional(engine=engine_to_use,
            #                                                 find_prompt_tries=2,
            #                                                 find_prompt_delay=5).verify_result()


def generic_aaa_test_auth(test_api: str, addressing_type: str, engines, topology_obj, local_adminuser: UserInfo,
                          request,
                          remote_aaa_type: str,
                          remote_aaa_obj: RemoteAaaResource,
                          server_by_addr_type: Dict[str, RemoteAaaServerInfo],
                          test_param: List[str] = None,
                          test_param_update_func: Callable[
                              [Any, Any, RemoteAaaServerInfo, HostnameId, str], None] = None,
                          skip_auth_mediums: List[str] = None):
    """
    @summary: Basic test to verify authentication and authorization through remote aaa, using all possible auth mediums:
        SSH, OpenApi, rcon, scp.

        Steps:
        1. configure aaa server
        2. set authentication order, and set failthrough off
        3. verify only remote user can authenticate
            - verify auth with remote user - expect success
            - verify auth with local user - expect fail
    @param test_api: run commands with NVUE / OpenApi
    @param addressing_type: whether to check connectivity with ipv4/ipv6/domain-name addressing
    @param engines: engines object
    @param topology_obj: topology object
    @param local_adminuser: local admin user info
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server_by_addr_type: dictionary containing server info, by addressing type
    @param test_param: list of other parameters to run the test on
    @param test_param_update_func: function to update the test configuration for each test param
    @param skip_auth_mediums: auth mediums to skip from the test (optional)
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'
    assert addressing_type in AddressingType.ALL_TYPES, f'{addressing_type} is not one of {AddressingType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure {remote_aaa_type} server'):
        server = server_by_addr_type[addressing_type].copy()
        server_resource = remote_aaa_obj.hostname.hostname_id[server.hostname]
        server.configure(engines)

    with allure.step(f'Enable {remote_aaa_type}'):
        configure_resource(engines, resource_obj=System().aaa.authentication, conf={
            AuthConsts.ORDER: f'{remote_aaa_type},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True, verify_apply=False)
        update_active_aaa_server(item, server)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item)

    if test_param:
        assert test_param_update_func, 'test_param_update_func function was not specified!'
        for param in test_param:
            with allure.step(f'Update test param: {param}'):
                test_param_update_func(engines, item, server, server_resource, param)
            with allure.step('Test auth'):
                auth_testing(engines, topology_obj, local_adminuser, remote_aaa_type, server, skip_auth_mediums)
    else:
        auth_testing(engines, topology_obj, local_adminuser, remote_aaa_type, server, skip_auth_mediums)


def generic_aaa_test_bad_configured_server(test_api, engines, topology_obj, remote_aaa_type: str,
                                           remote_aaa_obj: RemoteAaaResource,
                                           bad_param_name: str,
                                           bad_configured_server: RemoteAaaServerInfo):
    """
    @summary: Verify that when configuring remote AAA server with wrong required value, it is unreachable,
        and remote user can't authenticate

        Steps:
        1. configure aaa server with bad required param
        2. enable remote auth method
        3. verify remote user can't authenticate
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param bad_param_name: name of the field to assign the bad value to
    @param bad_configured_server: object containing the remote server info
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'

    TestToolkit.tested_api = test_api

    with allure.step(f'Configure {remote_aaa_type} server with bad {bad_param_name}'):
        bad_configured_server.configure(engines)

    with allure.step(f'Enable {remote_aaa_type}'):
        aaa = remote_aaa_obj.parent_obj
        aaa.authentication.set(AuthConsts.ORDER,
                               f'{remote_aaa_type},{AuthConsts.LOCAL}', apply=True).verify_result()

    with allure.step(f'Verify auth with {remote_aaa_type} user. Expect fail'):
        verify_user_auth(engines, topology_obj, random.choice(bad_configured_server.users), expect_login_success=False)


def generic_aaa_test_unique_priority(test_api, remote_aaa_obj: RemoteAaaResource):
    """
    @summary: Verify that hostname priority must be unique

        Steps:
        1. Set 2 hostnames with different priority - expect success
        2. set another hostname with existing priority - expect failure
    @param test_api: run commands with NVUE / OpenApi
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    """
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api

    with allure.step('Set 2 hostnames with different priority - expect success'):
        rand_prio1 = RandomizationTool.select_random_value(ValidValues.PRIORITY).get_returned_value()
        remote_aaa_obj.hostname.hostname_id['1.2.3.4'].set(AaaConsts.PRIORITY, rand_prio1).verify_result()
        rand_prio2 = RandomizationTool.select_random_value(ValidValues.PRIORITY,
                                                           forbidden_values=[rand_prio1]).get_returned_value()
        remote_aaa_obj.hostname.hostname_id['2.4.6.8'].set(AaaConsts.PRIORITY, rand_prio2,
                                                           apply=True).verify_result()

    with allure.step('Set another hostname with existing priority - expect fail'):
        remote_aaa_obj.hostname.hostname_id['3.6.9.12'].set(AaaConsts.PRIORITY, rand_prio2,
                                                            apply=True).verify_result(False)


def generic_aaa_test_priority(test_api, engines, topology_obj, request, remote_aaa_type: str,
                              remote_aaa_obj: RemoteAaaResource,
                              server1: RemoteAaaServerInfo, server2: RemoteAaaServerInfo):
    """
    @summary: Verify that auth is done via the top prioritized server

        Steps:
        1. set and prioritize 2 servers
        2. verify auth is done via top prioritized server
        3. advance the lowest prioritized server to be most prioritized
        4. repeat steps 2-3 until reach priority 8 (max)

        NOTE: in order to make this test meaningful, user should provide 2 servers info, with distinct users credentials
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server1: object containing remote server info
    @param server2: another server info (with different users credentials)
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Set and prioritize 2 {remote_aaa_type} servers'):
        server1.priority = 1
        server2.priority = 2
        server1.configure(engines, set_explicit_priority=True)
        server2.configure(engines, set_explicit_priority=True)

    with allure.step(f'Enable {remote_aaa_type}'):
        configure_resource(engines, resource_obj=remote_aaa_obj.parent_obj.authentication, conf={
            AuthConsts.ORDER: f'{remote_aaa_type},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True, verify_apply=False)
        top_server = server2
        lower_server = server1
        update_active_aaa_server(item, top_server)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item)

    while True:
        with allure.step('Wait for configuration to be fully applied'):
            time.sleep(RemoteAaaConsts.WAIT_TIME_BEFORE_AUTH)

        with allure.step(f'Verify auth is done via top prioritized server: {top_server.hostname}'):
            with allure.step(f'Verify auth via top server: {top_server.hostname} - expect success'):
                verify_user_auth(engines, topology_obj, top_server.users[0], expect_login_success=True,
                                 verify_authorization=False)

            with allure.step(f'Verify auth via lower server: {lower_server.hostname} - expect fail'):
                verify_user_auth(engines, topology_obj, lower_server.users[0], expect_login_success=False)

        if top_server.priority == ValidValues.PRIORITY[-1]:
            break

        next_prio = random.randint(top_server.priority + 1, ValidValues.PRIORITY[-1])
        with allure.step(f'Advance lower server to be top prioritized to: {next_prio}'):
            lower_server_resource = remote_aaa_obj.hostname.hostname_id[lower_server.hostname]
            lower_server.priority = next_prio
            lower_server_resource.set(AaaConsts.PRIORITY, lower_server.priority, apply=True,
                                      dut_engine=item.active_remote_admin_engine)
            lower_server, top_server = top_server, lower_server
            update_active_aaa_server(item, top_server)
            if remote_aaa_type == RemoteAaaType.LDAP:
                wait_for_ldap_nvued_restart_workaround(item)


def generic_aaa_test_server_unreachable(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                        remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                        server1: RemoteAaaServerInfo, server2: RemoteAaaServerInfo):
    """
    @summary: Verify that when a server is unreachable, auth is done via next in line
        (next server or next authentication method – local)

        Steps:
        1.	Configure aaa method
        2.	Enable aaa method
        3.	Make server unreachable
        4.	Verify auth - success only with local user
        5.	Configure secondary prioritized server
        6.	Verify auth – success only with 2nd server user
        7.	Make the 2nd server also unreachable
        8.	Verify auth – success only with local user
        9.	Bring back the first server
        10. Verify auth – success only with top server user
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server1: object containing remote server info
    @param server2: another server info (with different users credentials)
    """
    assert remote_aaa_type in RemoteAaaType.ALL_TYPES, f'{remote_aaa_type} is not one of {RemoteAaaType.ALL_TYPES}'
    assert test_api in ApiType.ALL_TYPES, f'{test_api} is not one of {ApiType.ALL_TYPES}'

    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step('Configure unreachable server'):
        server1 = server1.copy()
        server2 = server2.copy()
        server1.priority = 2
        server2.priority = 1
        server1.configure(engines, set_explicit_priority=True)
        server1.make_unreachable(engines)

    with allure.step(f'Enable {remote_aaa_type}'):
        configure_resource(engines, resource_obj=remote_aaa_obj.parent_obj.authentication, conf={
            AuthConsts.ORDER: f'{remote_aaa_type},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True)

    with allure.step('Verify auth - success only with local user'):
        verify_users_auth(engines, topology_obj,
                          users=[random.choice(server1.users), local_adminuser],
                          expect_login_success=[False, True], verify_authorization=False)

    with allure.step('Configure secondary prioritized reachable server'):
        server2.configure(engines, set_explicit_priority=True, apply=True)
        update_active_aaa_server(item, server2)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item)

    with allure.step('Verify auth – success only with 2nd server user'):
        verify_users_auth(engines, topology_obj,
                          users=[local_adminuser, random.choice(server2.users)],
                          expect_login_success=[False, True], verify_authorization=False)

    with allure.step('Make the 2nd server also unreachable'):
        server2.make_unreachable(engines, apply=True, dut_engine=item.active_remote_admin_engine)
        update_active_aaa_server(item, None)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    with allure.step('Verify auth - success only with local user'):
        verify_users_auth(engines, topology_obj,
                          users=[random.choice(server2.users), local_adminuser],
                          expect_login_success=[False, True], verify_authorization=False)

    with allure.step('Bring back the first server'):
        server1.make_reachable(engines, apply=True)
        update_active_aaa_server(item, server1)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item)

    with allure.step('Verify auth – success only with top server user'):
        verify_users_auth(engines, topology_obj,
                          users=[local_adminuser, server2.users[0], server1.users[0]],
                          expect_login_success=[False, False, True], verify_authorization=False)


def generic_aaa_test_auth_error(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                remote_aaa_type: str, remote_aaa_obj: RemoteAaaResource,
                                server1: RemoteAaaServerInfo, server2: RemoteAaaServerInfo):
    """
    @summary: Verify the behavior in case of auth error (username not found or bad credentials).

        In case of auth error (username not found, or bad credentials):
        - if failthrough is off -> fail authentication attempt
        - if failthrough is on  -> check credentials on the next server/auth method.

        Steps:
        1.	Configure remote aaa servers
        2.	Set failthrough off
        3.	Verify auth with 2nd server credentials – expect fail
        4.  Verify auth with local user credentials - expect fail
        5.	Set failthrough on
        6.	Verify auth with 2nd server credentials – expect success
        7.  Verify auth with local user credentials - expect success
        8.  Verify auth with credentials from none of servers/local - expect fail
    @param test_api: run commands with NVUE / OpenApi
    @param engines: engines object
    @param topology_obj: topology object
    @param request: object containing pytest information about current test
    @param remote_aaa_type: name of he remote Aaa type (tacacs, ldap, radius)
    @param local_adminuser: info of local admin user
    @param remote_aaa_obj: BaseComponent object representing the feature resource
    @param server1: object containing remote server info
    @param server2: another server info (with different users credentials)
    """
    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step(f'Configure {remote_aaa_type} servers'):
        server1 = server1.copy()
        server2 = server2.copy()
        server1.priority = 2
        server2.priority = 1
        server1.configure(engines, set_explicit_priority=True)
        server2.configure(engines, set_explicit_priority=True)

    with allure.step(f'Enable {remote_aaa_type} and disable failthrough'):
        configure_resource(engines, resource_obj=remote_aaa_obj.parent_obj.authentication, conf={
            AuthConsts.ORDER: f'{remote_aaa_type},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True, verify_apply=False)
        update_active_aaa_server(item, server1)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item)

    with allure.step('Verify auth with 2nd server credentials – expect fail'):
        verify_user_auth(engines, topology_obj, server2.users[0], expect_login_success=False)

    with allure.step('Verify auth with local user credentials - expect fail'):
        verify_user_auth(engines, topology_obj, local_adminuser, expect_login_success=False)

    with allure.step('Enable failthrough'):
        aaa: Aaa = remote_aaa_obj.parent_obj
        aaa.authentication.set(AuthConsts.FAILTHROUGH, AaaConsts.ENABLED, apply=True,
                               dut_engine=item.active_remote_admin_engine).verify_result()
        update_active_aaa_server(item, None)
        if remote_aaa_type == RemoteAaaType.LDAP:
            wait_for_ldap_nvued_restart_workaround(item, engine_to_use=engines.dut)

    if remote_aaa_type != RemoteAaaType.LDAP:  # with LDAP + failthrough on - only move to next method, and not server
        with allure.step('Verify auth with 2nd server credentials – expect success'):
            verify_user_auth(engines, topology_obj, server2.users[0], expect_login_success=True, verify_authorization=False)

    with allure.step('Verify auth with local user credentials - expect success'):
        verify_user_auth(engines, topology_obj, local_adminuser, expect_login_success=True, verify_authorization=False)

    with allure.step('Verify auth with credentials from none of servers/local - expect fail'):
        dummy_user = local_adminuser.copy()
        dummy_user.username = f'dummy_{dummy_user.username}'
        verify_user_auth(engines, topology_obj, dummy_user, expect_login_success=False)
