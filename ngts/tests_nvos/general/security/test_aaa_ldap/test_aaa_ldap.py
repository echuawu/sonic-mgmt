import pytest

from infra.tools.linux_tools.linux_tools import scp_file
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.tests_nvos.general.security.password_hardening.PwhConsts import PwhConsts
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import *
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import \
    check_ldap_user_groups_with_id, \
    check_ldap_user_with_getent_passwd
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapDefaults, LdapFilterFields, \
    LdapGroupAttributes, LdapPasswdAttributes
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_servers_info import LdapServers, LdapServersP3
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_test_utils import *
from ngts.tools.test_utils import allure_utils as allure
from ngts.tools.test_utils.nvos_general_utils import loganalyzer_ignore, wait_for_ldap_nvued_restart_workaround


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_set_unset_show(test_api, engines):
    ldap_obj = System().aaa.ldap
    random_str = RandomizationTool.get_random_string(6)
    generic_aaa_test_set_unset_show(
        test_api=test_api, engines=engines,
        remote_aaa_type=RemoteAaaType.LDAP,
        main_resource_obj=ldap_obj,
        confs={
            ldap_obj: {
                LdapConsts.PORT: random.choice(LdapConsts.VALID_VALUES[LdapConsts.PORT]),
                LdapConsts.BASE_DN: random_str,
                LdapConsts.BIND_DN: random_str,
                LdapConsts.GROUP_ATTR: random_str,
                LdapConsts.SECRET: random_str,
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
            },
            ldap_obj.filter: {
                LdapConsts.PASSWD: random_str,
                LdapConsts.GROUP: random_str,
                LdapConsts.SHADOW: random_str
            },
            ldap_obj.map.passwd: {
                LdapPasswdAttributes.UID: random_str,
                LdapPasswdAttributes.UID_NUMBER: random_str,
                LdapPasswdAttributes.GID_MUMBER: random_str,
                LdapPasswdAttributes.USER_PASSWORD: random_str
            },
            ldap_obj.map.group: {
                LdapGroupAttributes.CN: random_str,
                LdapGroupAttributes.GID_NUMBER: random_str,
                LdapGroupAttributes.MEMBER_UID: random_str
            },
            # ldap_obj.map.shadow: {
            #     LdapShadowAttributes.USER_PASSWORD: random_str,
            #     LdapShadowAttributes.MEMBER: random_str,
            #     LdapShadowAttributes.UID: random_str
            # }
        },
        hostname_conf={
            AaaConsts.PRIORITY: 2
        },
        default_confs={
            ldap_obj: LdapDefaults.GLOBAL_DEFAULTS,
            ldap_obj.ssl: LdapDefaults.SSL_DEFAULTS,
            ldap_obj.filter: LdapDefaults.FILTER_DEFAULTS,
            ldap_obj.map.passwd: LdapDefaults.MAP_PASSWD_DEFAULTS,
            ldap_obj.map.group: LdapDefaults.MAP_GROUP_DEFAULTS,
            # ldap_obj.map.shadow: LdapDefaults.MAP_SHADOW_DEFAULTS
        }
    )


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_set_invalid_param(test_api, engines):
    """
    @summary: Verify failure for invalid param values
    """
    ldap_obj = System().aaa.ldap
    global_ldap_fields = LdapConsts.LDAP_FIELDS
    ldap_ssl_fields = LdapConsts.SSL_FIELDS
    ldap_hostname_fields = [AaaConsts.PRIORITY]
    generic_aaa_test_set_invalid_param(
        test_api=test_api,
        field_is_numeric=LdapConsts.FIELD_IS_NUMERIC,
        valid_values=LdapConsts.ALL_VALID_VALUES,
        resources_and_fields={
            ldap_obj: global_ldap_fields,
            ldap_obj.ssl: ldap_ssl_fields,
            ldap_obj.hostname.hostname_id['1.2.3.4']: ldap_hostname_fields
        }
    )


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
@pytest.mark.parametrize('addressing_type', AddressingType.ALL_TYPES)
def test_ldap_auth(test_api, addressing_type, engines, topology_obj, local_adminuser, request):
    """
    @summary: Basic test to verify authentication and authorization through LDAP, using all possible auth mediums:
        SSH, OpenApi, rcon, scp.

        Steps:
        1. configure LDAP server
        2. set LDAP in authentication order, and set failthrough off
        3. verify only LDAP user can authenticate
            - verify auth with tacacs user - expect success
            - verify auth with local user - expect fail
    """
    ldap = System().aaa.ldap
    generic_aaa_test_auth(test_api=test_api, addressing_type=addressing_type, engines=engines,
                          topology_obj=topology_obj, local_adminuser=local_adminuser, request=request,
                          remote_aaa_type=RemoteAaaType.LDAP,
                          remote_aaa_obj=ldap,
                          server_by_addr_type=LdapServersP3.LDAP1_SERVERS,
                          test_param=LdapEncryptionModes.ALL_MODES,
                          test_param_update_func=update_ldap_encryption_mode)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_bad_port_error_flow(test_api, engines, topology_obj):
    """
    @summary: in this test case we want to validate invalid port ldap error flows of ,
    we want to configure invalid port value and then see that we are not able to connect
    to switch
    """
    ldap_server = LdapServers.PHYSICAL_SERVER.copy()
    ldap_server.port = 6692
    # RandomizationTool.select_random_value(LdapConsts.POSSIBLE_PORTS, [ldap_server.port]).get_returned_value()
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.LDAP, remote_aaa_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.PORT, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_bad_secret_error_flow(test_api, engines, topology_obj):
    """
    @summary: in this test case we want to validate invalid bind in password ldap error flows,
    we want to configure invalid bind in password value and then see that we are not able to connect
    to switch
    """
    ldap_server = LdapServers.PHYSICAL_SERVER.copy()
    ldap_server.secret = RandomizationTool.get_random_string(6)
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.LDAP, remote_aaa_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.SECRET, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_bad_bind_dn_error_flow(test_api, engines, topology_obj):
    """
    @summary: in this test case we want to validate invalid bind dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
    ldap_server = LdapServers.PHYSICAL_SERVER.copy()
    ldap_server.bind_dn = RandomizationTool.get_random_string(6)
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.LDAP, remote_aaa_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.BIND_DN, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_bad_base_dn_error_flow(test_api, engines, topology_obj):
    """
    @summary: in this test case we want to validate invalid base dn ldap error flows,
    we want to configure invalid bind dn value and then see that we are not able to connect
    to switch
    """
    ldap_server = LdapServers.PHYSICAL_SERVER.copy()
    ldap_server.base_dn = RandomizationTool.get_random_string(6)
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.LDAP, remote_aaa_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.BASE_DN, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_unique_priority(test_api, engines, topology_obj):
    """
    @summary: Verify that hostname priority must be unique

        Steps:
        1. Set 2 hostnames with different priority - expect success
        2. set another hostname with existing priority - expect failure

    """
    generic_aaa_test_unique_priority(test_api, remote_aaa_obj=System().aaa.ldap)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_priority(test_api, engines, topology_obj, request):
    """
    @summary: Verify that auth is done via the top prioritized server

        Steps:
        1. set and prioritize 2 servers
        2. verify auth is done via top prioritized server
        3. advance the lowest prioritized server to be most prioritized
        4. repeat steps 2-3 until reach priority 8 (max)
    """
    server1 = LdapServers.PHYSICAL_SERVER.copy()
    server2 = random.choice(list(LdapServers.DOCKER_SERVERS.values())).copy()

    generic_aaa_test_priority(test_api, engines, topology_obj, request, remote_aaa_type=RemoteAaaType.LDAP,
                              remote_aaa_obj=System().aaa.ldap, server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_server_unreachable(test_api, engines, topology_obj, local_adminuser, request):
    """
    @summary: Verify that when a server is unreachable, auth is done via next in line
        (next server or authentication method – local)

        Steps:
        1.	Configure server
        2.	Set LDAP in authentication order and failthrough off
        3.	Make server unreachable
        4.	Verify auth - success only with local user
        5.	Configure secondary prioritized server
        6.	Verify auth – success only with 2nd server user
        7.	Make the 2nd server also unreachable
        8.	Verify auth – success only with local user
        9.	Bring back the first server
        10. Verify auth – success only with top server user
    """
    server1 = LdapServers.PHYSICAL_SERVER.copy()
    server2 = LdapServers.DOCKER_SERVER_DN.copy()
    generic_aaa_test_server_unreachable(test_api, engines, topology_obj, request,
                                        local_adminuser=local_adminuser,
                                        remote_aaa_type=RemoteAaaType.LDAP,
                                        remote_aaa_obj=System().aaa.ldap,
                                        server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_auth_error(test_api, engines, topology_obj, local_adminuser: UserInfo, request):
    """
    @summary: Verify the behavior in case of auth error (username not found or bad credentials).

        In case of auth error (username not found, or bad credentials):
        - if failthrough is off -> fail authentication attempt
        - if failthrough is on  -> check credentials on the next auth method (next server not possible in LDAP)

        Steps:
        1.	Configure tacacs servers
        2.	Set failthrough off
        3.	Verify auth with 2nd server credentials – expect fail
        4.  Verify auth with local user credentials - expect fail
        5.	Set failthrough on
        6.
        7.  Verify auth with local user credentials - expect success
        8.  Verify auth with credentials from none of servers/local - expect fail
    """
    server1 = LdapServers.PHYSICAL_SERVER.copy()
    server2 = LdapServers.DOCKER_SERVER_DN.copy()
    generic_aaa_test_auth_error(test_api, engines, topology_obj, request, local_adminuser=local_adminuser,
                                remote_aaa_type=RemoteAaaType.LDAP,
                                remote_aaa_obj=System().aaa.ldap,
                                server1=server1, server2=server2)


# -------------------- FEATURE SPECIFIC TESTS ---------------------


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_cert_verify(test_api, engines, devices, backup_and_restore_certificates, alias_ldap_server_dn, request,
                     topology_obj):
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Upload server certificate to tmp location on the switch'):
        scp_file(engines.dut, LdapConsts.DOCKER_LDAP_SERVER_CERT_PATH, LdapConsts.SERVER_CERT_FILE_IN_SWITCH)

    with allure.step('Configure ldap server that allows cert verify'):
        aaa = System().aaa
        ldap_obj = System().aaa.ldap
        ldap_server_info = LdapServers.DOCKER_SERVER_DN_WITH_CERT
        server_resource = ldap_obj.hostname.hostname_id[ldap_server_info.hostname]
        ldap_server_info.configure(engines)

    with allure.step('Enable cert-verify'):
        ldap_obj.ssl.set(LdapConsts.SSL_CERT_VERIFY, LdapConsts.ENABLED).verify_result()

    with allure.step('Enable and set ldap as main authentication method'):
        configure_resource(engines, aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.LDAP},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: LdapConsts.ENABLED
        })

    for encryption_mode in LdapEncryptionModes.ALL_MODES:
        with allure.step(f'Verify with encryption mode: {encryption_mode}'):
            user_to_validate = random.choice(ldap_server_info.users)

            with allure.step(f'Configure encryption mode: {encryption_mode}'):
                update_ldap_encryption_mode(engines, item, ldap_server_info, server_resource, encryption_mode, False)
                update_active_aaa_server(item,
                                         ldap_server_info if encryption_mode == LdapEncryptionModes.NONE else None)
                engine = engines.dut if not item.active_remote_admin_engine else item.active_remote_admin_engine
                DutUtilsTool.wait_for_nvos_to_become_functional(engine, find_prompt_delay=5)

            if encryption_mode != LdapEncryptionModes.NONE:
                with allure.step(f'Verify auth with LDAP user when there is no CA cert in the switch- expect fail'):
                    verify_user_auth(engines, topology_obj, user_to_validate, expect_login_success=False)

                with allure.step('Add the server certificate to the switch'):
                    add_ldap_server_certificate_to_switch(engine)
                    update_active_aaa_server(item, ldap_server_info)
                    DutUtilsTool.wait_for_nvos_to_become_functional(item.active_remote_admin_engine,
                                                                    find_prompt_delay=5)

            with allure.step(f'Verify auth with LDAP user when there is CA cert in the switch - expect success'):
                verify_user_auth(engines, topology_obj, user_to_validate, verify_authorization=False)

            with allure.step('Restore certificates file'):
                engine = engines.dut if not item.active_remote_admin_engine else item.active_remote_admin_engine
                engine.run_cmd(f"sudo cp -f {LdapConsts.SWITCH_CA_BACKUP_FILE} {LdapConsts.SWITCH_CA_FILE}")
                update_active_aaa_server(item, None)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_filter_passwd(test_api, engines, request, topology_obj):
    """
    Check functionality of filter to passwd

        Steps:
        1. set ldap configuration
        2. set passwd filter to exclude users with uidNumber < 2000
            * ldap user 'ldap1adm1' has uidNumber=1111 (filtered out)
        3. enable ldap
        4. verify ldap user 'ldap1adm1' does not exist in getent passwd
        5. also, verify ldap user 'ldap1adm1' cant auth
        6. sanity: clear filter and check the opposite
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        server.configure(engines)

    with allure.step('Set passwd filter'):
        passwd_filter = '(&(objectClass=posixAccount)(uidNumber>=2000))'
        ldap = System().aaa.ldap
        ldap.filter.set(LdapFilterFields.PASSWD, passwd_filter).verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step(f'Verify user {test_user.username} does not exist in getent passwd'):
        check_ldap_user_with_getent_passwd(engine=engines.dut, username=test_user.username, user_should_exist=False)

    with allure.step(f'Verify user {test_user.username} can not auth'):
        with loganalyzer_ignore():  # supposed to be able to ignore LA here because failthrough enabled
            verify_user_auth(engines, topology_obj, test_user,
                             expect_login_success=False)  # TODO: need all auth mediums?

    with allure.step('Sanity: clear filter and check the opposite'):
        with allure.step('Clear passwd filter'):
            ldap.filter.unset(LdapConsts.PASSWD, apply=True).verify_result()
            wait_for_ldap_nvued_restart_workaround(item)
        with allure.step(f'Verify user "{test_user.username}" exists in getent passwd'):
            check_ldap_user_with_getent_passwd(engine=engines.dut, username=test_user.username, user_should_exist=True)
        with allure.step(f'Verify user {test_user.username} can auth'):
            verify_user_auth(engines, topology_obj, test_user, expect_login_success=True, verify_authorization=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_filter_group(test_api, engines, request, topology_obj):
    """
    Check functionality of filter to group

        Steps:
        1. set ldap configuration
        2. set group filter to exclude groups with gidNumber=9999
            * ldap server is configured with group 'ldap1grp1' with gidNumber=9999 (filtered out)
            * configured that user 'ldap1adm1' is member of this group
        3. enable ldap
        4. verify user 'ldap1adm1' does not have group 'ldap1grp1' (with id/groups command)
        5. also, verify ldap user 'ldap1adm1' cant auth
        6. sanity: clear filter and check the opposite
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        server.configure(engines)

    with allure.step('Set group filter'):
        group_filter = '(&(objectClass=posixGroup)(!(gidNumber=9999)))'
        ldap = System().aaa.ldap
        ldap.filter.set(LdapFilterFields.GROUP, group_filter).verify_result()
        group_9999 = 'ldap1grp1'

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step(f'Verify user {test_user.username} does not have group "{group_9999}"'):
        check_ldap_user_groups_with_id(engine=engines.dut, username=test_user.username, groupname=group_9999,
                                       group_should_exist=False)

    with allure.step('Sanity: clear filter and check the opposite'):
        with allure.step('Clear group filter'):
            ldap.filter.unset(LdapConsts.GROUP, apply=True).verify_result()
            wait_for_ldap_nvued_restart_workaround(item)
        with allure.step(f'Verify user {test_user.username} now has group "{group_9999}"'):
            check_ldap_user_groups_with_id(engine=engines.dut, username=test_user.username, groupname=group_9999,
                                           group_should_exist=True)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_filter_shadow(test_api, engines, request, topology_obj):
    """
    Check functionality of filter to shadow

        Steps:
        1. set ldap configuration
        2. set shadow filter to exclude users with uidNumber < 2000
            * ldap user 'ldap1adm1' has uidNumber=1111 (filtered out)
        3. enable ldap
        4. verify ldap user 'ldap1adm1' exist in getent shadow
        5. however, verify ldap user 'ldap1adm1' can not auth
        6. sanity: clear filter and check the opposite
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        server.configure(engines)

    with allure.step('Set shadow filter'):
        shadow_filter = '(&(objectClass=shadowAccount)(uidNumber>=2000))'
        ldap = System().aaa.ldap
        ldap.filter.set(LdapFilterFields.SHADOW, shadow_filter).verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step(f'Verify user {test_user.username} exist in getent passwd'):
        check_ldap_user_with_getent_passwd(engine=engines.dut, username=test_user.username, user_should_exist=True)

    with allure.step(f'Verify user {test_user.username} can not auth'):
        with loganalyzer_ignore():  # supposed to be able to ignore LA here because failthrough enabled
            verify_user_auth(engines, topology_obj, test_user,
                             expect_login_success=False)  # TODO: need all auth mediums?

    with allure.step('Sanity: clear filter and check the opposite'):
        with allure.step('Clear shadow filter'):
            ldap.filter.unset(LdapConsts.SHADOW, apply=True).verify_result()
            wait_for_ldap_nvued_restart_workaround(item)
        with allure.step(f'Verify user "{test_user.username}" exists in getent passwd'):
            check_ldap_user_with_getent_passwd(engine=engines.dut, username=test_user.username, user_should_exist=True)
        with allure.step(f'Verify user {test_user.username} can auth'):
            verify_user_auth(engines, topology_obj, test_user, expect_login_success=True, verify_authorization=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_filter_combo(test_api, engines, request, topology_obj):
    """
    Check functionality of filters combination
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        ldapadm1 = [user for user in server.users if user.username == 'ldap1adm1'][0]
        ldapadm2 = [user for user in server.users if user.username == 'ldap1adm2'][0]
        ldapadm3 = [user for user in server.users if user.username == 'ldap1adm3'][0]
        group_9999 = 'ldap1grp1'
        server.configure(engines)

    with allure.step('Set filters combination'):
        passwd_filter = '(&(objectClass=posixAccount)(uidNumber<=3000))'
        group_filter = '(&(objectClass=posixGroup)(!(gidNumber=9999)))'
        shadow_filter = '(&(objectClass=shadowAccount)(uidNumber>=2000))'
        ldap = System().aaa.ldap
        ldap.filter.set(LdapFilterFields.PASSWD, passwd_filter).verify_result()
        ldap.filter.set(LdapFilterFields.GROUP, group_filter).verify_result()
        ldap.filter.set(LdapFilterFields.SHADOW, shadow_filter).verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    def check_users_in_combo_filter_test(adm1_exists: bool, adm2_exists: bool, adm3_exists: bool, adm1_can_auth: bool,
                                         adm2_can_auth: bool, adm3_can_auth: bool, grp9999_exists: bool):
        def check_user_getent_and_auth(user: UserInfo, user_exists: bool, user_can_auth: bool):
            with allure.step(f'Verify user {user.username} {"" if user_exists else "does not "}exist in getent passwd'):
                check_ldap_user_with_getent_passwd(engine=engines.dut, username=user.username,
                                                   user_should_exist=user_exists)
            with allure.step(f'Verify user {user.username} can {"" if user_can_auth else "not "}auth'):
                with loganalyzer_ignore(
                        cond=not user_can_auth):  # supposed to be able to ignore LA here because failthrough enabled
                    verify_user_auth(engines, topology_obj, user, expect_login_success=user_can_auth,
                                     verify_authorization=False)  # TODO: need all auth mediums?

        check_user_getent_and_auth(ldapadm1, adm1_exists, adm1_can_auth)
        with allure.step(
                f'Verify user {ldapadm1.username} {"" if grp9999_exists else "does not "}have group "{group_9999}"'):
            check_ldap_user_groups_with_id(engine=engines.dut, username=ldapadm1.username, groupname=group_9999,
                                           group_should_exist=grp9999_exists)
        check_user_getent_and_auth(ldapadm2, adm2_exists, adm2_can_auth)
        check_user_getent_and_auth(ldapadm3, adm3_exists, adm3_can_auth)

    with allure.step('Check with all filters'):
        check_users_in_combo_filter_test(adm1_exists=True, adm2_exists=True, adm3_exists=False, adm1_can_auth=False,
                                         adm2_can_auth=True, adm3_can_auth=False, grp9999_exists=False)

    with allure.step('Clear group filter'):
        ldap.filter.unset(LdapFilterFields.GROUP, apply=True).verify_result()
        wait_for_ldap_nvued_restart_workaround(item)
    with allure.step('Check with passwd, shadow filters'):
        check_users_in_combo_filter_test(adm1_exists=True, adm2_exists=True, adm3_exists=False, adm1_can_auth=False,
                                         adm2_can_auth=True, adm3_can_auth=False, grp9999_exists=True)

    with allure.step('Clear shadow filter'):
        ldap.filter.unset(LdapFilterFields.SHADOW, apply=True).verify_result()
        wait_for_ldap_nvued_restart_workaround(item)
    with allure.step('Check with passwd filter only'):
        check_users_in_combo_filter_test(adm1_exists=True, adm2_exists=True, adm3_exists=False, adm1_can_auth=True,
                                         adm2_can_auth=True, adm3_can_auth=False, grp9999_exists=True)

    with allure.step('Clear passwd filter'):
        ldap.filter.unset(LdapFilterFields.PASSWD, apply=True).verify_result()
        wait_for_ldap_nvued_restart_workaround(item)
    with allure.step('Check with no filters'):
        check_users_in_combo_filter_test(adm1_exists=True, adm2_exists=True, adm3_exists=True, adm1_can_auth=True,
                                         adm2_can_auth=True, adm3_can_auth=True, grp9999_exists=True)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_map_passwd(test_api, engines, request, topology_obj):
    """
    Check functionality of map of passwd attribute

        Steps:
        1. set ldap configuration
        2. set passwd map to map attribute 'uid' to 'cn'
            * ldap user 'ldap1adm3' is defined also with cn in the server
            * ldap user 'ldapadm1' on the other hand, is not
        3. enable ldap
        4. verify ldap user 'ldap1adm3' exists in getent passwd
        5. also, verify ldap user 'ldap1adm3' can auth
        6. verify 'ldap1adm1' does not exist in getent passwd
        7. also, verify 'ldap1adm1' cant auth
        6. sanity: clear the map and check the opposite (for ldap1adm1)
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        cn_test_user = [user for user in server.users if user.username == 'ldap1adm3'][0]
        non_cn_test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        server.configure(engines)

    with allure.step('Set passwd map from uid to cn'):
        ldap = System().aaa.ldap
        ldap.map.passwd.set(LdapPasswdAttributes.UID, 'cn').verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step(f'Verify user {cn_test_user.username} exist in getent passwd'):
        check_ldap_user_with_getent_passwd(engine=engines.dut, username=cn_test_user.username, user_should_exist=True)

    with allure.step(f'Verify user {cn_test_user.username} can auth'):
        verify_user_auth(engines, topology_obj, cn_test_user, expect_login_success=True, verify_authorization=False)

    with allure.step(f'Verify user {non_cn_test_user.username} does not exist in getent passwd'):
        check_ldap_user_with_getent_passwd(engine=engines.dut, username=non_cn_test_user.username,
                                           user_should_exist=False)

    with allure.step(f'Verify user {non_cn_test_user.username} can not auth'):
        with loganalyzer_ignore():  # supposed to be able to ignore LA here because failthrough enabled
            verify_user_auth(engines, topology_obj, non_cn_test_user, expect_login_success=False)

    with allure.step('Sanity: clear filter and check the opposite'):
        with allure.step('Clear passwd map'):
            ldap.map.passwd.unset(apply=True).verify_result()
            wait_for_ldap_nvued_restart_workaround(item)
        with allure.step(f'Verify user "{non_cn_test_user.username}" now exists in getent passwd'):
            check_ldap_user_with_getent_passwd(engine=engines.dut, username=non_cn_test_user.username,
                                               user_should_exist=True)
        with allure.step(f'Verify user {non_cn_test_user.username} can auth'):
            verify_user_auth(engines, topology_obj, non_cn_test_user, expect_login_success=True,
                             verify_authorization=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_map_group(test_api, engines, request, topology_obj):
    """
    Check functionality of map of group attribute

        Steps:
        1. set ldap configuration
        2. preparation step - set filter for group to fetch only groups of type groupOfNames
            * group 'ldap1grp2' configured as groupOfNames, containing
                gidNumber 8888 as 'description' attribute
                and user 'ldap1adm1' is member of it.
            * without the mapping of 'gidNumber' to 'description', nslcd won't be able to fetch this group,
                so without the map, 'ldap1adm1' doesn't have group 'ldap1grp2',
                and with the map, 'ldap1adm1' has group 'ldap1grp2'
        2. set group map to map attribute 'gidNumber' to 'member'
        3. enable ldap
        4. verify ldap user 'ldap1adm1' has group 'ldap1grp2'
        6. sanity: clear the map and check the opposite
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        test_groups = ['adm', 'sudo', 'nvapply', 'nvset', 'docker', 'redis', 'ldap1grp1']
        server.configure(engines)

    with allure.step('Set group map from "memberUid" to "member"'):
        ldap = System().aaa.ldap
        ldap.map.group.set(LdapGroupAttributes.MEMBER_UID, 'member').verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step(f'Verify user {test_user.username} dont have groups "{test_groups}"'):
        check_ldap_user_groups_with_id(engine=engines.dut, username=test_user.username, groupname=test_groups,
                                       group_should_exist=False)

    with allure.step('Sanity: clear filter and check the opposite'):
        with allure.step('Clear group map'):
            ldap.map.group.unset(apply=True).verify_result()
            wait_for_ldap_nvued_restart_workaround(item)
        with allure.step(f'Verify user {test_user.username} has groups "{test_groups}"'):
            check_ldap_user_groups_with_id(engine=engines.dut, username=test_user.username, groupname=test_groups,
                                           group_should_exist=True)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_filter_performance(test_api, engines, request, topology_obj):
    """
    Check the affection of filter on the performance of connection/running command

        Steps:
        1. set ldap configuration
        2. set some filters
        3. enable ldap
        4. connect with ldap user and make some operation + measure time
        5. clear filters
        6. repeat the connection with ldap user and operation + measure time
        7. calc time diff
    """
    item = request.node
    TestToolkit.tested_api = test_api

    with allure.step('Set ldap configuration'):
        server = LdapServersP3.LDAP1_IPV4.copy()
        test_user = [user for user in server.users if user.username == 'ldap1adm1'][0]
        server.configure(engines)

    with allure.step('Set filters'):
        with allure.step('Set passwd filter'):
            passwd_filter = '(&(objectClass=posixAccount)(uidNumber<=2000))'
            ldap = System().aaa.ldap
            ldap.filter.set(LdapFilterFields.PASSWD, passwd_filter).verify_result()
        with allure.step('Set group filter'):
            group_filter = '(&(objectClass=posixGroup)(!(gidNumber=9999)))'
            ldap = System().aaa.ldap
            ldap.filter.set(LdapFilterFields.GROUP, group_filter).verify_result()

    with allure.step('Enable LDAP'):
        ldap.enable(failthrough=True, apply=True, verify_res=True)
        wait_for_ldap_nvued_restart_workaround(item)

    def get_ssh_and_command_execution_duration(engine: ProxySshEngine, resource_obj: BaseComponent, set_param_name: str,
                                               set_param_val, description: str = '') -> float:
        start_time = time.time()
        resource_obj.set(set_param_name, set_param_val, apply=True, dut_engine=engine).verify_result()
        end_time = time.time()
        duration = end_time - start_time
        duration_formatted = time.strftime("%H:%M:%S", time.gmtime(duration))
        logging.info(f'Duration {description}: Took {duration_formatted}')
        return duration

    with allure.step('With filters - Connect with LDAP user and make operation'):
        ldap_user_engine = ProxySshEngine(device_type=engines.dut.device_type,
                                          ip=engines.dut.ip,
                                          username=test_user.username,
                                          password=test_user.password)
        pwh_obj = System().security.password_hardening
        duration_with_filters = get_ssh_and_command_execution_duration(ldap_user_engine, pwh_obj, PwhConsts.LEN_MIN, 19,
                                                                       'with filters')

    with allure.step('Clear filters'):
        ldap.filter.unset(apply=True).verify_result()
        wait_for_ldap_nvued_restart_workaround(item)

    with allure.step('Without filters - Connect with LDAP user and make operation'):
        ldap_user_engine.disconnect()
        duration_without_filters = get_ssh_and_command_execution_duration(ldap_user_engine, pwh_obj, PwhConsts.LEN_MIN,
                                                                          20, 'without filters')

    with allure.step('Performance - Calc duration diff'):
        diff = abs(duration_with_filters - duration_without_filters)
        diff_formatted = time.strftime("%H:%M:%S", time.gmtime(diff))
        logging.info(f'Diff |with-filters - without|: {diff_formatted}')

    with allure.step(f'Diff |with-filters - without|: {diff_formatted} - {100 * diff / duration_without_filters}%'):
        assert diff <= 0.15 * duration_without_filters, f'Expected diff: <= 10% . Actual: {100 * diff / duration_without_filters}%'
