import logging
import time
from itertools import product

import pytest

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_utils import validate_users_authorization_and_role, \
    validate_authentication_fail_with_credentials, set_local_users
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapConsts
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_test_utils import *
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from ngts.tools.test_utils import allure_utils as allure


def test_ldap_priority_and_fallback_functionality(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate the functionality of the priority
    and fallback, we will configure 2 ldap servers and then connect through the credentials
    found only in the first server and connect through credentials in the second server only
    and we are testing the local credentials
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    first_real_ldap_server = LdapConsts.PHYSICAL_LDAP_SERVER.copy()
    first_real_ldap_server[LdapConsts.PRIORITY] = '2'
    second_real_ldap_server = LdapConsts.DOCKER_LDAP_SERVER_DNS.copy()
    second_real_ldap_server[LdapConsts.PRIORITY] = '1'
    ldap_server_list = [first_real_ldap_server, second_real_ldap_server]
    configure_ldap_and_validate(engines, ldap_server_list=ldap_server_list, devices=devices)

    with allure.step("Create invalid ldap server and configuring as high priority"):
        randomized_ldap_server_dict = randomize_ldap_server()
        randomized_ldap_server_dict[LdapConsts.PRIORITY] = LdapConsts.MAX_PRIORITY
        configure_ldap(randomized_ldap_server_dict)

    with allure.step("Validating first ldap server credentials"):
        first_ldap_server_users = first_real_ldap_server[LdapConsts.USERS]
        validate_users_authorization_and_role(engines=engines, users=first_ldap_server_users)

    with allure.step("Validating failed connection to switch with second ldap server credentials"):
        second_ldap_server_user = second_real_ldap_server[LdapConsts.USERS][1]
        validate_authentication_fail_with_credentials(engines,
                                                      username=second_ldap_server_user[LdapConsts.USERNAME],
                                                      password=second_ldap_server_user[LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def a_test_ldap_timeout_functionality(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate timeout functionality:
    there are two cases of timeout: bind-in timeout and search timeout functionalities
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER.copy()

    with allure.step("Configuring LDAP server with low bind-in timeout value: {}".format(LdapConsts.LDAP_LOW_TIMOEUT)):
        ldap_server_info[LdapConsts.TIMEOUT_BIND] = LdapConsts.LDAP_LOW_TIMOEUT
        configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    with allure.step("Validating failed connection to ldap server credentials"):
        ldap_server_users = LdapConsts.LDAP_SERVERS_LIST[0][LdapConsts.NESTED_USERS]
        validate_authentication_fail_with_credentials(engines=engines,
                                                      username=ldap_server_users[0][LdapConsts.USERNAME],
                                                      password=ldap_server_users[0][LdapConsts.PASSWORD])

    with allure.step(
            "Configuring LDAP server with high bind-in timeout value: {}, and low search timeout value: {}".format(
                LdapConsts.LDAP_HIGH_TIMEOUT, LdapConsts.LDAP_LOW_TIMOEUT)):
        ldap_server_info[LdapConsts.TIMEOUT_BIND] = LdapConsts.LDAP_HIGH_TIMEOUT
        ldap_server_info[LdapConsts.TIMEOUT] = LdapConsts.LDAP_LOW_TIMOEUT
        configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    with allure.step("Validating failed connection to ldap server credentials"):
        ldap_server_users = LdapConsts.LDAP_SERVERS_LIST[0][LdapConsts.NESTED_USERS]
        validate_authentication_fail_with_credentials(engines=engines,
                                                      username=ldap_server_users[0][LdapConsts.USERNAME],
                                                      password=ldap_server_users[0][LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def test_ldap_invalid_auth_port_error_flow(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate invalid port ldap error flows of ,
    we want to configure invalid port value and then see that we are not able to connect
    to switch
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    system = System(None)
    invalid_port = Tools.RandomizationTool.select_random_value(
        [i for i in range(SshConfigConsts.MIN_LOGIN_PORT, SshConfigConsts.MAX_LOGIN_PORT)],
        [int(ldap_server_info[LdapConsts.PORT])]).get_returned_value()
    with allure.step("Setting invalid auth-port: {}".format(str(invalid_port))):
        system.aaa.ldap.set(LdapConsts.PORT, str(invalid_port), apply=True)
        with allure.step(
                "Waiting {} secs to apply configurations".format(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)):
            time.sleep(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)
        validate_authentication_fail_with_credentials(engines,
                                                      username=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.USERNAME],
                                                      password=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def test_ldap_invalid_bind_in_password_error_flow(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate invalid bind in password ldap error flows,
    we want to configure invalid bind in password value and then see that we are not able to connect
    to switch
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    system = System(None)
    random_string = Tools.RandomizationTool.get_random_string(20)
    with allure.step("Configuring invalid password: {}".format(random_string)):
        system.aaa.ldap.set(LdapConsts.BIND_PASSWORD, random_string, apply=True)
        with allure.step(
                "Waiting {} secs to apply configurations".format(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)):
            time.sleep(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)
        validate_authentication_fail_with_credentials(engines,
                                                      username=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.USERNAME],
                                                      password=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def test_ldap_invalid_bind_dn_error_flow(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate invalid bind dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    system = System(None)
    random_string = Tools.RandomizationTool.get_random_string(20)
    with allure.step("Configuring invalid bind-dn: {}".format(random_string)):
        system.aaa.ldap.set(LdapConsts.BIND_DN, random_string, apply=True)
        with allure.step(
                "Waiting {} secs to apply configurations".format(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)):
            time.sleep(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)
        validate_authentication_fail_with_credentials(engines,
                                                      username=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.USERNAME],
                                                      password=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def test_ldap_invalid_base_dn_error_flow(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to validate invalid base dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    system = System(None)
    random_string = Tools.RandomizationTool.get_random_string(20)
    with allure.step("Configuring invalid base-dn: {}".format(random_string)):
        system.aaa.ldap.set(LdapConsts.BASE_DN, random_string, apply=True)
        with allure.step(
                "Waiting {} secs to apply configurations".format(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)):
            time.sleep(LdapConsts.LDAP_SLEEP_TO_APPLY_CONFIGURATIONS)
        validate_authentication_fail_with_credentials(engines,
                                                      username=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.USERNAME],
                                                      password=ldap_server_info[LdapConsts.USERS][0][
                                                          LdapConsts.PASSWORD])
    engines.dut.run_cmd('stat /var/log/audit.log')


def test_ldap_invalid_credentials_error_flow(engines, remove_ldap_configurations, devices):
    """
    @summary: in this test case we want to check that with non existing credentials we are not able to
    connect to switch
    """
    engines.dut.run_cmd('stat /var/log/audit.log')
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    random_user = Tools.RandomizationTool.get_random_string(20)
    random_password = Tools.RandomizationTool.get_random_string(20)
    with allure.step("Connecting with non-existing credentials: ({},{})".format(random_user, random_password)):
        validate_authentication_fail_with_credentials(engines,
                                                      username=random_user,
                                                      password=random_password)
    engines.dut.run_cmd('stat /var/log/audit.log')


@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_set_show_unset(engines, remove_ldap_configurations, test_api):
    """
    @summary: in this test case we want to validate ldap commands:
        1. set
        2. show
        3. unset
    """
    TestToolkit.tested_api = test_api

    engines.dut.run_cmd('stat /var/log/audit.log')
    configured_ldap_servers_hostname = []
    system = System()
    ldap_obj = system.aaa.ldap

    with allure.step('Validate show command output'):
        show_output = OutputParsingTool.parse_json_str_to_dictionary(ldap_obj.show()).get_returned_value()
        ValidationTool.verify_all_fields_value_exist_in_output_dictionary(show_output, LdapConsts.LDAP_FIELDS)

    with allure.step('Validate set and unset of general fields of the feature'):
        for field in LdapConsts.LDAP_FIELDS:
            logging.info(f'Current field: {field}')
            if field == LdapConsts.PASSWORD:
                continue

            if LdapConsts.VALID_VALUES[field] == str:
                new_val = RandomizationTool.get_random_string(length=10)
            else:
                new_val = RandomizationTool.select_random_value(LdapConsts.VALID_VALUES[field], [show_output[field]]) \
                    .get_returned_value()
            logging.info(f'Set field "{field}" to "{new_val}"')
            ldap_obj.set(field, new_val, apply=True).verify_result()

            logging.info('Verify new value in show')
            show_output = OutputParsingTool.parse_json_str_to_dictionary(ldap_obj.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(show_output, field, new_val).verify_result()

            logging.info(f'Unset field {field}')
            ldap_obj.unset(field, apply=True).verify_result()

            logging.info('Verify default value in show')
            show_output = OutputParsingTool.parse_json_str_to_dictionary(ldap_obj.show()).get_returned_value()
            ValidationTool.verify_field_value_in_output(show_output, field, LdapConsts.DEFAULTS[field]).verify_result()

    with allure.step("Configuring LDAP Server"):
        for ldap_server_info in LdapConsts.LDAP_SERVERS_LIST:
            configure_ldap(ldap_server_info)
            configured_ldap_servers_hostname.append(ldap_server_info[LdapConsts.HOSTNAME])
    with allure.step("Validate Unset specific ldap hostname command"):
        for hostname in configured_ldap_servers_hostname:
            system.aaa.ldap.hostname.unset_hostname(hostname, True, True).verify_result(should_succeed=True)
            output = system.aaa.ldap.hostname.show_hostname(hostname=hostname)
            assert hostname not in output, "hostname: {}, appears in the show radius hostname after removing it".format(
                hostname)

    configured_ldap_servers_hostname = []
    with allure.step("Configuring LDAP Servers again to test unset ldap"):
        for ldap_server_info in LdapConsts.LDAP_SERVERS_LIST:
            configure_ldap(ldap_server_info)
            configured_ldap_servers_hostname.append(ldap_server_info[LdapConsts.HOSTNAME])

    system.aaa.ldap.unset(apply=True).verify_result(should_succeed=True)
    with allure.step("Validating the show hostname command output"):
        output = system.aaa.ldap.hostname.show()
        for hostname in configured_ldap_servers_hostname:
            assert hostname not in output, "hostname: {}, appears in the show radius hostname after removing it".format(
                hostname)
    engines.dut.run_cmd('stat /var/log/audit.log')


@pytest.mark.parametrize('connection_method, encryption_mode, test_api', list(product(LdapConsts.CONNECTION_METHODS,
                                                                                      LdapConsts.ENCRYPTION_MODES,
                                                                                      ApiType.ALL_TYPES)))
def test_ldap_authentication(connection_method, encryption_mode, test_api, engines, devices,
                             remove_ldap_configurations):
    """
    @summary:
        Test basic functionality - verify authentication through the ldap server.

        Steps:
        1. Configure ldap server with the given connection method
        2. Configure the given encryption mode for the ldap communication
        3. Enable ldap and set it as main authentication method
        4. Verify authentication with the result setup
    """
    logging.info(f'Test setup: {connection_method}, {encryption_mode}, {test_api}')
    TestToolkit.tested_api = test_api

    engines.dut.run_cmd('stat /var/log/audit.log')  # todo: ask azmy - what is that?

    with allure.step(f'Configure ldap server with connection method: {connection_method}'):
        ldap_obj = System().aaa.ldap
        ldap_server_info = LdapConsts.SERVER_INFO[connection_method]
        configure_ldap_server(engines, ldap_obj, ldap_server_info)

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Enable and set ldap as main authentication method'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL],
                                 failthrough=LdapConsts.ENABLED)

    with allure.step(f'Verify authentication with the current setup'):
        validate_users_authorization_and_role(engines=engines, users=ldap_server_info[LdapConsts.USERS])

    engines.dut.run_cmd('stat /var/log/audit.log')


@pytest.mark.parametrize('test_api, encryption_mode', list(product(ApiType.ALL_TYPES, LdapConsts.ENCRYPTION_MODES)))
def test_no_connection(engines, devices, test_api, encryption_mode, reset_aaa):
    """
    @summary:
        Test that in case of bad connection with ldap server, authentication and authorization are done via local

        Steps:
        1. Configure bad ldap server
        2. Configure auth order - ldap, local
        3. Verify authentication and authorization are done via local:
            - server only user can not login
            - mutual/local only user can login, and role is according to local configuration
    """
    logging.info(f'Test setup: {encryption_mode}, {test_api}')
    TestToolkit.tested_api = test_api

    engines.dut.run_cmd('stat /var/log/audit.log')

    with allure.step('Configure bad ldap server'):
        aaa = System().aaa
        ldap_obj = aaa.ldap
        ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER.copy()
        ldap_server_info[LdapConsts.HOSTNAME] = '1.2.3.4'
        configure_ldap_server(engines, ldap_obj, ldap_server_info)

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Set ldap as main authentication method'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL])

    with allure.step('Verify authentication and authorization are done via local'):
        ldap_users = ldap_server_info[LdapConsts.USERS]

        with allure.step('Set local-only users'):
            local_users = LdapConsts.LOCAL_ONLY_TEST_USERS
            set_local_users(local_users)

        with allure.step(f'Set mutual user "{ldap_users[0][AaaConsts.USERNAME]}" in local'):
            mutual_user = {
                AaaConsts.USERNAME: ldap_users[0][AaaConsts.USERNAME],
                AaaConsts.PASSWORD: LdapConsts.STRONG_PASSWORD,
                AaaConsts.ROLE: AaaConsts.MONITOR if ldap_users[0][AaaConsts.ROLE] == AaaConsts.ADMIN else AaaConsts.ADMIN
            }
            set_local_users([mutual_user])

        with allure.step('Verify ldap-only user can not login'):
            validate_users_authorization_and_role(engines=engines, users=ldap_users, login_should_succeed=False)

        with allure.step('Verify mutual user can be authenticated and authorized (via local)'):
            pass  # validate_users_authorization_and_role(engines=engines, users=[mutual_user])

        with allure.step('Verify local-only user be authenticated and authorized (via local)'):
            validate_users_authorization_and_role(engines=engines, users=local_users)

    engines.dut.run_cmd('stat /var/log/audit.log')
