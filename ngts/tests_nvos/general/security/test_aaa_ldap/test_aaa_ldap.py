from itertools import product
import pytest
from infra.tools.linux_tools.linux_tools import scp_file
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import \
    generic_aaa_set_unset_show
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import \
    validate_authentication_fail_with_credentials, \
    set_local_users, user_lists_difference, mutual_users, validate_users_authorization_and_role
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_test_utils import *
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from ngts.tools.test_utils import allure_utils as allure


def a_test_ldap_priority_and_fallback_functionality(engines, devices):
    """
    @summary: in this test case we want to validate the functionality of the priority
    and fallback, we will configure 2 ldap servers and then connect through the credentials
    found only in the first server and connect through credentials in the second server only
    and we are testing the local credentials
    """
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
        validate_users_authorization_and_role(engines=engines, users=first_ldap_server_users,
                                              check_nslcd_if_login_failed=True)

    with allure.step("Validating failed connection to switch with second ldap server credentials"):
        second_ldap_server_user = second_real_ldap_server[LdapConsts.USERS][1]
        validate_authentication_fail_with_credentials(engines,
                                                      username=second_ldap_server_user[LdapConsts.USERNAME],
                                                      password=second_ldap_server_user[LdapConsts.PASSWORD])


def a_test_ldap_timeout_functionality(engines, devices):
    """
    @summary: in this test case we want to validate timeout functionality:
    there are two cases of timeout: bind-in timeout and search timeout functionalities
    """
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


def test_ldap_invalid_auth_port_error_flow(engines, devices):
    """
    @summary: in this test case we want to validate invalid port ldap error flows of ,
    we want to configure invalid port value and then see that we are not able to connect
    to switch
    """
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


def test_ldap_invalid_bind_in_password_error_flow(engines, devices):
    """
    @summary: in this test case we want to validate invalid bind in password ldap error flows,
    we want to configure invalid bind in password value and then see that we are not able to connect
    to switch
    """
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


def test_ldap_invalid_bind_dn_error_flow(engines, devices):
    """
    @summary: in this test case we want to validate invalid bind dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
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


def test_ldap_invalid_base_dn_error_flow(engines, devices):
    """
    @summary: in this test case we want to validate invalid base dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
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


def test_ldap_invalid_credentials_error_flow(engines, devices):
    """
    @summary: in this test case we want to check that with non existing credentials we are not able to
    connect to switch
    """
    ldap_server_info = LdapConsts.PHYSICAL_LDAP_SERVER
    configure_ldap_and_validate(engines, ldap_server_list=[ldap_server_info], devices=devices)

    random_user = Tools.RandomizationTool.get_random_string(20)
    random_password = Tools.RandomizationTool.get_random_string(20)
    with allure.step("Connecting with non-existing credentials: ({},{})".format(random_user, random_password)):
        validate_authentication_fail_with_credentials(engines,
                                                      username=random_user,
                                                      password=random_password)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_set_unset_show(test_api, engines):
    ldap_obj = System().aaa.ldap
    random_str = RandomizationTool.get_random_string(6)
    generic_aaa_set_unset_show(
        test_api=test_api, engines=engines,
        remote_aaa_type=RemoteAaaType.LDAP,
        main_resource_obj=ldap_obj,
        confs={
            ldap_obj: {
                LdapConsts.PORT: random.choice(LdapConsts.VALID_VALUES[LdapConsts.PORT]),
                LdapConsts.BASE_DN: random_str,
                LdapConsts.BIND_DN: random_str,
                LdapConsts.GROUP_ATTR: random_str,
                LdapConsts.BIND_PASSWORD: random_str,
                LdapConsts.TIMEOUT_BIND: random.choice(LdapConsts.VALID_VALUES[LdapConsts.TIMEOUT_BIND]),
                LdapConsts.TIMEOUT: random.choice(LdapConsts.VALID_VALUES[LdapConsts.TIMEOUT]),
                LdapConsts.VERSION: random.choice(LdapConsts.VALID_VALUES[LdapConsts.VERSION])
            },
            ldap_obj.ssl: {
                LdapConsts.SSL_CA_LIST: random.choice(LdapConsts.VALID_VALUES_SSL[LdapConsts.SSL_CA_LIST]),
                LdapConsts.SSL_CERT_VERIFY: random.choice(LdapConsts.VALID_VALUES_SSL[LdapConsts.SSL_CERT_VERIFY]),
                LdapConsts.SSL_MODE: random.choice(LdapConsts.VALID_VALUES_SSL[LdapConsts.SSL_MODE]),
                LdapConsts.SSL_PORT: random.choice(LdapConsts.VALID_VALUES_SSL[LdapConsts.SSL_PORT]),
                LdapConsts.SSL_TLS_CIPHERS: random.choice(LdapConsts.VALID_VALUES_SSL[LdapConsts.SSL_TLS_CIPHERS])
            }
        },
        hostname_conf={
            AaaConsts.PRIORITY: 2
        },
        default_confs={
            ldap_obj: LdapConsts.DEFAULT_CONF,
            ldap_obj.ssl: LdapConsts.SSL_DEFAULTS
        }
    )


# -------------------- NEW TESTS ---------------------


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api, connection_method, encryption_mode', list(product(ApiType.ALL_TYPES,
                                                                                      LdapConsts.CONNECTION_METHODS,
                                                                                      LdapConsts.ENCRYPTION_MODES)))
def test_ldap_authentication(test_api, connection_method, encryption_mode, engines, devices):
    """
    @summary:
        Test basic functionality - verify authentication through the ldap server.

        Steps:
        1. Configure ldap server with the given connection method
        2. Configure the given encryption mode for the ldap communication
        3. Enable ldap and set it as main authentication method
        4. Verify authentication with the result setup
    """
    logging.info(f'Test setup: {test_api}, {connection_method}, {encryption_mode}')
    TestToolkit.tested_api = test_api

    with allure.step(f'Configure ldap server with connection method: {connection_method}'):
        ldap_obj = System().aaa.ldap
        ldap_server_info = LdapConsts.SERVER_INFO[connection_method]
        configure_ldap_server(engines, ldap_obj, ldap_server_info)

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Enable and set ldap as main authentication method'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL], apply=True)
        LdapTestTool.active_ldap_server = ldap_server_info

    with allure.step(f'Verify authentication with the current setup'):
        user_to_validate = random.choice(ldap_server_info[LdapConsts.USERS])
        validate_users_authorization_and_role(engines=engines, users=[user_to_validate],
                                              check_nslcd_if_login_failed=True)

    with allure.step('Disable ldap'):
        disable_ldap(engines)


@pytest.mark.bug  # permissions traceback exception 3519743, wrong permission of ldap-local mutual user 3557998
@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api, encryption_mode', list(product(ApiType.ALL_TYPES, LdapConsts.ENCRYPTION_MODES)))
def test_ldap_bad_connection(test_api, encryption_mode, engines, devices):
    """
    @summary:
        Test that in case of bad connection with ldap server, authentication and authorization are done via next
            server / auth. method in line.

        Steps:
        1. Configure bad ldap servers
        2. Configure auth order - ldap, local
        3. Verify authentication and authorization are done via next in line - local:
            - server only user can not login
            - mutual/local only user can login, and role is according to local configuration
        4. Configure another (valid) ldap server, prioritized as the last of the servers
        5. Verify authentication and authorization are done via next in line - 2nd server
            - Invalid servers user can not login
            - Valid server can login
            - local user can not login
    """
    logging.info(f'Test setup: {test_api}, {encryption_mode}')
    TestToolkit.tested_api = test_api

    with allure.step('Set local users for the test'):
        invalid_servers = [LdapConsts.DOCKER_LDAP_SERVER_DNS.copy() for _ in range(3)]

        TestToolkit.tested_api = ApiType.NVUE  # todo: remove after fix set user with password in openapi

        ldap1_user = random.choice(invalid_servers[0][LdapConsts.USERS])

        with allure.step('Set local-only users'):
            local_user = random.choice(AaaConsts.LOCAL_ONLY_TEST_USERS)
            set_local_users(engines, [local_user], apply=False)

        with allure.step(f'Set ldap-local mutual user "{ldap1_user[AaaConsts.USERNAME]}" in local'):
            mutual_user = {
                AaaConsts.USERNAME: ldap1_user[AaaConsts.USERNAME],
                AaaConsts.PASSWORD: AaaConsts.STRONG_PASSWORD,
                AaaConsts.ROLE: AaaConsts.MONITOR if ldap1_user[AaaConsts.ROLE] == AaaConsts.ADMIN else AaaConsts.ADMIN
            }
            set_local_users(engines, [mutual_user], apply=True)

        TestToolkit.tested_api = test_api  # todo: remove after fix set user with password in openapi

    with allure.step('Configure invalid ldap servers'):
        aaa = System().aaa
        ldap_obj = aaa.ldap
        configure_ldap_common_fields(engines, ldap_obj)
        i = 4
        for server in invalid_servers:
            server[LdapConsts.HOSTNAME] = f'{1 + i}.{2 + i}.{3 + i}.{4 + i}'
            server[LdapConsts.PRIORITY] = str(i)
            ldap_obj.hostname.set_priority(hostname=server[LdapConsts.HOSTNAME], priority=i).verify_result()
            i -= 1

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Set ldap as main authentication method'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL], apply=True)

    with allure.step('Verify authentication and authorization are done via next in line - local'):
        with allure.step('Verify ldap-only user can not auth'):
            validate_users_authorization_and_role(engines=engines, users=[ldap1_user], login_should_succeed=False)

        with allure.step('Verify mutual user can auth (via local)'):
            validate_users_authorization_and_role(engines=engines, users=[mutual_user],
                                                  check_nslcd_if_login_failed=True)

        with allure.step('Verify local-only user can auth'):
            validate_users_authorization_and_role(engines=engines, users=[local_user])

    with allure.step('Add valid ldap server server'):
        ldap2_server_info = LdapConsts.PHYSICAL_LDAP_SERVER.copy()
        ldap2_server_info[LdapConsts.PRIORITY] = 1
        ldap_obj.hostname.set_priority(hostname=ldap2_server_info[LdapConsts.HOSTNAME], priority=1,
                                       apply=True).verify_result()
        LdapTestTool.active_ldap_server = ldap2_server_info

    with allure.step('Verify authentication and authorization are done via next in line - valid ldap server'):
        ldap1_only_user = random.choice(user_lists_difference(invalid_servers[0][LdapConsts.USERS],
                                                              ldap2_server_info[LdapConsts.USERS]))
        ldap_ldap_mutual_user = random.choice(mutual_users(ldap2_server_info[LdapConsts.USERS],
                                                           invalid_servers[0][LdapConsts.USERS]))
        ldap2_user = random.choice(ldap2_server_info[LdapConsts.USERS])

        with allure.step(f'Verify 1st server only user "{ldap1_only_user[AaaConsts.USERNAME]}" can not auth'):
            validate_users_authorization_and_role(engines=engines, users=[ldap1_only_user], login_should_succeed=False)

        with allure.step(
                f'Verify 1st and 2nd servers mutual user "{ldap_ldap_mutual_user[AaaConsts.USERNAME]}" can auth (via valid server)'):
            validate_users_authorization_and_role(engines=engines, users=[ldap_ldap_mutual_user],
                                                  check_nslcd_if_login_failed=True)

        with allure.step(f'Verify 2nd server user "{ldap2_user[AaaConsts.USERNAME]}" can auth'):
            validate_users_authorization_and_role(engines=engines, users=[ldap2_user], check_nslcd_if_login_failed=True)

        with allure.step(f'Verify local user "{local_user[AaaConsts.USERNAME]}" can not auth'):
            validate_users_authorization_and_role(engines=engines, users=[local_user], login_should_succeed=False)

    with allure.step('Disable ldap'):
        disable_ldap(engines)


@pytest.mark.bug  # opened bug for fail through 3501518
@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api, encryption_mode', list(product(ApiType.ALL_TYPES, LdapConsts.ENCRYPTION_MODES)))
def test_ldap_failthrough(test_api, encryption_mode, engines, devices):
    """
    @summary: Test ldap failthrough mechanism.
        * Fail through: In case of auth. error (e.g. bad credentials, user not found, etc) move forward to the
            next server/auth. method in line, according to ldap servers priority and authentication order.

        Steps:
        1. Configure 2 ldap servers
        2. Configure auth order
        3. Disable failthrough
        4. Verify only server1 user can login
        5. Enable failthrough
        6. Verify also server2 user can login
        7. Verify also local user can login
    """
    logging.info(f'Test setup: {test_api}, {encryption_mode}')
    TestToolkit.tested_api = test_api

    with allure.step('Set local-only user'):
        TestToolkit.tested_api = ApiType.NVUE  # todo: remove after fix set user with password in openapi
        local_user = random.choice(AaaConsts.LOCAL_ONLY_TEST_USERS)
        set_local_users(engines, [local_user], apply=True)
        TestToolkit.tested_api = test_api  # todo: remove after fix set user with password in openapi

    with allure.step('Configure 2 ldap servers'):
        server1 = LdapConsts.PHYSICAL_LDAP_SERVER.copy()
        server2 = LdapConsts.DOCKER_LDAP_SERVER_DNS.copy()
        server1[LdapConsts.PRIORITY] = str(2)
        server2[LdapConsts.PRIORITY] = str(1)
        ldap_obj = System().aaa.ldap
        configure_ldap_common_fields(engines, ldap_obj)
        ldap_obj.hostname.set_priority(hostname=server1[LdapConsts.HOSTNAME], priority=2).verify_result()
        ldap_obj.hostname.set_priority(hostname=server2[LdapConsts.HOSTNAME], priority=1).verify_result()

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Configure authentication order and disable failthrough'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL],
                                 failthrough=LdapConsts.DISABLED, apply=True)
        LdapTestTool.active_ldap_server = server1

    with allure.step('Verify only 1st server user can login'):
        server1_user = random.choice(server1[LdapConsts.USERS])
        server2_user = random.choice(user_lists_difference(server2[LdapConsts.USERS], server1[LdapConsts.USERS]))

        with allure.step(f'Verify 1st server user "{server1_user[AaaConsts.USERNAME]}" can login'):
            validate_users_authorization_and_role(engines=engines, users=[server1_user],
                                                  check_nslcd_if_login_failed=True)

        with allure.step(f'Verify 2nd server user "{server2_user[AaaConsts.USERNAME]}" can not login'):
            validate_users_authorization_and_role(engines=engines, users=[server2_user], login_should_succeed=False)

        with allure.step(f'Verify local user "{local_user[AaaConsts.USERNAME]}" can not login'):
            validate_users_authorization_and_role(engines=engines, users=[local_user], login_should_succeed=False)

    with allure.step('Set failthrough on'):
        active_engine = get_active_dut_engine(engines)
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL],
                                 failthrough=LdapConsts.ENABLED, apply=True, dut_engine=active_engine)

    with allure.step('Verify all users can login'):
        with allure.step(f'Verify 1st server user "{server1_user[AaaConsts.USERNAME]}" can login'):
            validate_users_authorization_and_role(engines=engines, users=[server1_user],
                                                  check_nslcd_if_login_failed=True)

        with allure.step(f'Verify 2nd server user "{server2_user[AaaConsts.USERNAME]}" can login'):
            validate_users_authorization_and_role(engines=engines, users=[server2_user],
                                                  check_nslcd_if_login_failed=True)

        with allure.step(f'Verify local user "{local_user[AaaConsts.USERNAME]}" can login'):
            validate_users_authorization_and_role(engines=engines, users=[local_user])

    with allure.step('Disable ldap'):
        disable_ldap(engines)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api, encryption_mode', list(product(ApiType.ALL_TYPES, LdapConsts.ENCRYPTION_MODES)))
def test_cert_verify(test_api, encryption_mode, engines, devices, backup_and_restore_certificates,
                     alias_ldap_server_dn):
    logging.info(f'Test setup: {test_api}, {encryption_mode}')
    TestToolkit.tested_api = test_api

    with allure.step('Upload server certificate from fixed shared location to the switch'):
        scp_file(engines.dut, LdapConsts.DOCKER_LDAP_SERVER_CERT_PATH, LdapConsts.SERVER_CERT_FILE_IN_SWITCH)

    with allure.step('Configure ldap server that allows cert verify'):
        ldap_obj = System().aaa.ldap
        ldap_server_info = LdapConsts.DOCKER_LDAP_SERVER_DNS_WITH_CERT
        configure_ldap_server(engines, ldap_obj, ldap_server_info)

    with allure.step(f'Configure encryption mode: {encryption_mode}'):
        configure_ldap_encryption(engines, ldap_obj, encryption_mode)

    with allure.step('Enable cert-verify'):
        configure_resource(engines, ldap_obj.ssl, conf={LdapConsts.SSL_CERT_VERIFY: LdapConsts.ENABLED})

    with allure.step('Enable and set ldap as main authentication method'):
        configure_authentication(engines, devices, order=[AuthConsts.LDAP, AuthConsts.LOCAL],
                                 failthrough=LdapConsts.ENABLED, apply=True)

    with allure.step(f'Verify authentication fail when there is no certificate in the switch'):
        user_to_validate = random.choice(ldap_server_info[LdapConsts.USERS])
        validate_users_authorization_and_role(engines=engines, users=[user_to_validate], login_should_succeed=False)

    with allure.step('Add the server certificate to the switch'):
        add_ldap_server_certificate_to_switch(engines)
        LdapTestTool.active_ldap_server = ldap_server_info

    with allure.step(f'Verify authentication success'):
        validate_users_authorization_and_role(engines=engines, users=[user_to_validate],
                                              check_nslcd_if_login_failed=True)

    with allure.step('Disable ldap'):
        disable_ldap(engines)

# ----------------------------------- NEW -----------------------------------
