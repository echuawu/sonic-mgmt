from itertools import product
import pytest
from infra.tools.linux_tools.linux_tools import scp_file
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.Tools import Tools
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthMedium
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import *
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import \
    validate_authentication_fail_with_credentials, \
    set_local_users, user_lists_difference, mutual_users, validate_users_authorization_and_role
from ngts.tests_nvos.general.security.test_aaa_ldap.constants import LdapEncryptionModes
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_servers_info import LdapServers
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_test_utils import *
from ngts.tests_nvos.general.security.test_ssh_config.constants import SshConfigConsts
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.security
@pytest.mark.simx
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


@pytest.mark.security
@pytest.mark.simx
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
@pytest.mark.simx
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
                          feature_resource_obj=ldap,
                          server_by_addr_type=LdapServers.DOCKER_SERVERS,
                          test_param=LdapEncryptionModes.ALL_MODES,
                          test_param_update_func=update_ldap_encryption_mode)


@pytest.mark.security
@pytest.mark.simx
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
                                           remote_aaa_type=RemoteAaaType.LDAP, feature_resource_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.PORT, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx
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
                                           remote_aaa_type=RemoteAaaType.LDAP, feature_resource_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.SECRET, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx
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
                                           remote_aaa_type=RemoteAaaType.LDAP, feature_resource_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.BIND_DN, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx
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
                                           remote_aaa_type=RemoteAaaType.LDAP, feature_resource_obj=System().aaa.ldap,
                                           bad_param_name=LdapConsts.BASE_DN, bad_configured_server=ldap_server)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_ldap_unique_priority(test_api, engines, topology_obj):
    """
    @summary: Verify that hostname priority must be unique

        Steps:
        1. Set 2 hostnames with different priority - expect success
        2. set another hostname with existing priority - expect failure

    """
    generic_aaa_test_unique_priority(test_api, feature_resource_obj=System().aaa.ldap)


@pytest.mark.security
@pytest.mark.simx
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
                              feature_resource_obj=System().aaa.ldap, server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx
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
                                        feature_resource_obj=System().aaa.ldap,
                                        server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx
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
                                feature_resource_obj=System().aaa.ldap,
                                server1=server1, server2=server2)


# -------------------- FEATURE SPECIFIC TESTS ---------------------


@pytest.mark.security
@pytest.mark.simx
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
