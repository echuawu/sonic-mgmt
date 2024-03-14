import pytest

from ngts.tests_nvos.general.security.security_test_tools.constants import AccountingConsts, \
    AuthType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_aaa_accounting_testing import *
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import *
from ngts.tests_nvos.general.security.security_test_tools.resource_utils import configure_resource
from ngts.tests_nvos.general.security.security_test_tools.switch_authenticators import SshAuthenticator
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.tacacs.constants import TacacsConsts, TacacsDockerServer1, TacacsDockerServer2, \
    TacacsServers
from ngts.tests_nvos.general.security.tacacs.tacacs_test_utils import update_tacacs_server_auth_type, \
    get_two_different_tacacs_servers
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.nvos_chipsim_ci
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_tacacs_set_unset_show(test_api, engines):
    tacacs_obj = System().aaa.tacacs
    generic_aaa_test_set_unset_show(
        test_api=test_api, engines=engines,
        remote_aaa_type=RemoteAaaType.TACACS,
        main_resource_obj=tacacs_obj,
        confs={
            tacacs_obj: {
                AaaConsts.AUTH_TYPE: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.AUTH_TYPE]),
                AaaConsts.PORT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.PORT]),
                # AaaConsts.RETRANSMIT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.RETRANSMIT]),
                AaaConsts.SECRET: 'alontheking',
                AaaConsts.TIMEOUT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT])
            },
            tacacs_obj.accounting: {
                AccountingFields.STATE: random.choice(AccountingConsts.VALUES[AccountingFields.STATE])
            }
        },
        hostname_conf={
            AaaConsts.AUTH_TYPE: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.AUTH_TYPE]),
            AaaConsts.PORT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.PORT]),
            # AaaConsts.RETRANSMIT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.RETRANSMIT]),
            AaaConsts.SECRET: 'alontheking',
            AaaConsts.TIMEOUT: random.choice(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT]),
            AaaConsts.PRIORITY: 2
        },
        default_confs={
            tacacs_obj: TacacsConsts.DEFAULT_TACACS_CONF,
            tacacs_obj.accounting: AccountingConsts.DEFAULT
        }
    )


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_tacacs_set_invalid_param(test_api, engines):
    """
    @summary: Verify failure for invalid param values
    """
    tacacs_obj = System().aaa.tacacs
    global_tacacs_fields = [AaaConsts.AUTH_TYPE, AaaConsts.PORT, AaaConsts.SECRET, AaaConsts.TIMEOUT]
    tacacs_hostname_fields = global_tacacs_fields + [AaaConsts.PRIORITY]
    generic_aaa_test_set_invalid_param(
        test_api=test_api,
        field_is_numeric=TacacsConsts.FIELD_IS_NUMERIC,
        valid_values=TacacsConsts.VALID_VALUES,
        resources_and_fields={
            tacacs_obj: global_tacacs_fields,
            tacacs_obj.hostname.hostname_id['1.2.3.4']: tacacs_hostname_fields
        }
    )


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
@pytest.mark.parametrize('addressing_type', AddressingType.ALL_TYPES)
def test_tacacs_auth(test_api, addressing_type, engines, topology_obj, local_adminuser, request):
    """
    @summary: Basic test to verify authentication and authorization through tacacs, using all possible auth mediums:
        SSH, OpenApi, rcon, scp.

        Steps:
        1. configure tacacs server
        2. set tacacs in authentication order, and set failthrough off
        3. verify only tacacs user can authenticate
            - verify auth with tacacs user - expect success
            - verify auth with local user - expect fail
    """
    tacacs = System().aaa.tacacs
    generic_aaa_test_auth(test_api=test_api, addressing_type=addressing_type, engines=engines,
                          topology_obj=topology_obj, local_adminuser=local_adminuser, request=request,
                          remote_aaa_type=RemoteAaaType.TACACS,
                          remote_aaa_obj=tacacs,
                          server_by_addr_type=TacacsServers.DOCKER_SERVERS,
                          test_param=AuthType.ALL_TYPES,
                          test_param_update_func=update_tacacs_server_auth_type)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_bad_secret(test_api, engines, topology_obj):
    """
    @summary: Verify that tacacs users can't auth when bad/no secret is configured.

        Steps:
        1. configure tacacs server
        2. set no/blank secret
        3. verify auth - expect fail
        4. set bad secret
        5. verify auth - expect fail
    """
    tacacs_server = TacacsServers.PHYSICAL_SERVER.copy()
    tacacs_server.secret = RandomizationTool.get_random_string(6)
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.TACACS,
                                           remote_aaa_obj=System().aaa.tacacs,
                                           bad_param_name=AaaConsts.SECRET, bad_configured_server=tacacs_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_bad_port(test_api, engines, topology_obj):
    """
    @summary: Verify that tacacs users can't auth when bad port is configured.

        Steps:
        1. configure tacacs server
        2. set bad port
        3. verify auth - expect fail
    """
    tacacs_server = TacacsServers.PHYSICAL_SERVER.copy()
    tacacs_server.port = RandomizationTool.select_random_value(TacacsConsts.VALID_VALUES[AaaConsts.PORT],
                                                               [tacacs_server.port]).get_returned_value()
    generic_aaa_test_bad_configured_server(test_api, engines, topology_obj,
                                           remote_aaa_type=RemoteAaaType.TACACS,
                                           remote_aaa_obj=System().aaa.tacacs,
                                           bad_param_name=AaaConsts.PORT, bad_configured_server=tacacs_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_unique_priority(test_api, engines, topology_obj):
    """
    @summary: Verify that hostname priority must be unique

        Steps:
        1. Set 2 hostnames with different priority - expect success
        2. set another hostname with existing priority - expect failure

    """
    generic_aaa_test_unique_priority(test_api, remote_aaa_obj=System().aaa.tacacs)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_priority(test_api, engines, topology_obj, request):
    """
    @summary: Verify that auth is done via the top prioritized server

        Steps:
        1. set and prioritize 2 servers
        2. verify auth is done via top prioritized server
        3. advance the lowest prioritized server to be most prioritized
        4. repeat steps 2-3 until reach priority 8 (max)
    """
    server1, server2 = get_two_different_tacacs_servers()
    generic_aaa_test_priority(test_api, engines, topology_obj, request, remote_aaa_type=RemoteAaaType.TACACS,
                              remote_aaa_obj=System().aaa.tacacs, server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_server_unreachable(test_api, engines, topology_obj, local_adminuser, request):
    """
    @summary: Verify that when a server is unreachable, auth is done via next in line
        (next server or authentication method – local)

        Steps:
        1.	Configure server
        2.	Set tacacs in authentication order and failthrough off
        3.	Make server unreachable
        4.	Verify auth - success only with local user
        5.	Configure secondary prioritized server
        6.	Verify auth – success only with 2nd server user
        7.	Make the 2nd server also unreachable
        8.	Verify auth – success only with local user
        9.	Bring back the first server
        10. Verify auth – success only with top server user
    """
    server1, server2 = get_two_different_tacacs_servers()
    generic_aaa_test_server_unreachable(test_api, engines, topology_obj, request,
                                        local_adminuser=local_adminuser,
                                        remote_aaa_type=RemoteAaaType.TACACS,
                                        remote_aaa_obj=System().aaa.tacacs,
                                        server1=server1, server2=server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_auth_error(test_api, engines, topology_obj, local_adminuser: UserInfo, request):
    """
    @summary: Verify the behavior in case of auth error (username not found or bad credentials).

        In case of auth error (username not found, or bad credentials):
        - if failthrough is off -> fail authentication attempt
        - if failthrough is on  -> check credentials on the next server/auth method.

        Steps:
        1.	Configure tacacs servers
        2.	Set failthrough off
        3.	Verify auth with 2nd server credentials – expect fail
        4.  Verify auth with local user credentials - expect fail
        5.	Set failthrough on
        6.	Verify auth with 2nd server credentials – expect success
        7.  Verify auth with local user credentials - expect success
        8.  Verify auth with credentials from none of servers/local - expect fail
    """
    server1, server2 = get_two_different_tacacs_servers()
    generic_aaa_test_auth_error(test_api, engines, topology_obj, request, local_adminuser=local_adminuser,
                                remote_aaa_type=RemoteAaaType.TACACS,
                                remote_aaa_obj=System().aaa.tacacs,
                                server1=server1, server2=server2)


# -------------------- FEATURE SPECIFIC TESTS ---------------------


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
@pytest.mark.parametrize('addressing_type', AddressingType.ALL_TYPES)
def test_tacacs_accounting_basic(test_api, addressing_type, engines, topology_obj, request, local_adminuser: UserInfo,
                                 switch_hostname: str):
    """
    @summary: Verify accounting basic functionality

        Steps:
        1. configure tacacs
        2. disable accounting
        3. enable tacacs
        4. verify no accounting logs on server
        5. enable accounting
        6. verify accounting logs on server only for tacacs users events
    """
    test_server = TacacsDockerServer1.SERVER_BY_ADDRESSING_TYPE[addressing_type].copy()
    test_server.auth_type = random.choice(AuthType.ALL_TYPES)
    test_server.users = TacacsDockerServer1.USERS_BY_AUTH_TYPE[test_server.auth_type]

    generic_aaa_test_accounting_basic(test_api, engines, topology_obj, request, switch_hostname, local_adminuser,
                                      remote_aaa_type=RemoteAaaType.TACACS,
                                      remote_aaa_obj=System().aaa.tacacs,
                                      server=test_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_accounting_top_server_only(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                           switch_hostname: str):
    """
    @summary: Verify that accounting logs are sent to top server only

        Steps:
        1. configure tacacs with 2 servers
        2. enable accounting
        3. enable tacacs
        4. verify accounting logs on top server only for tacacs users events
    """
    addressing_type1 = random.choice(AddressingType.ALL_TYPES)
    auth_type1 = random.choice(AuthType.ALL_TYPES)
    addressing_type2 = RandomizationTool.select_random_value(AddressingType.ALL_TYPES,
                                                             [addressing_type1]).get_returned_value()
    auth_type2 = random.choice(AuthType.ALL_TYPES)

    test_server1 = TacacsDockerServer1.SERVER_BY_ADDRESSING_TYPE[addressing_type1].copy()
    test_server2 = TacacsDockerServer2.SERVER_BY_ADDRESSING_TYPE[addressing_type2].copy()

    test_server1.priority = 2
    test_server2.priority = 1

    test_server1.auth_type = auth_type1
    test_server1.users = TacacsDockerServer1.USERS_BY_AUTH_TYPE[auth_type1]
    test_server2.auth_type = auth_type2
    test_server2.users = TacacsDockerServer2.USERS_BY_AUTH_TYPE[auth_type2]

    generic_aaa_test_accounting_top_server_only(test_api, engines, topology_obj, request, switch_hostname,
                                                local_adminuser,
                                                remote_aaa_type=RemoteAaaType.TACACS,
                                                remote_aaa_obj=System().aaa.tacacs,
                                                server1=test_server1, server2=test_server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_accounting_unreachable_top_server(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                                  switch_hostname: str):
    """
    @summary: Verify that when top server becomes unreachable, accounting logs are sent to next available server only

        Steps:
        1. configure tacacs with several top unreachable servers
        2. configure also reachable server with lower priority
        3. enable accounting
        4. enable tacacs
        5. verify accounting logs on top available server only for tacacs users events
        6. make unreachable server reachable
        7. verify accounting logs now on the top reachable server
    """
    addressing_type1 = random.choice(AddressingType.ALL_TYPES)
    auth_type1 = random.choice(AuthType.ALL_TYPES)
    addressing_type2 = RandomizationTool.select_random_value(AddressingType.ALL_TYPES,
                                                             [addressing_type1]).get_returned_value()
    auth_type2 = random.choice(AuthType.ALL_TYPES)

    test_server1 = TacacsDockerServer1.SERVER_BY_ADDRESSING_TYPE[addressing_type1].copy()
    test_server2 = TacacsDockerServer2.SERVER_BY_ADDRESSING_TYPE[addressing_type2].copy()

    test_server1.priority = 2
    test_server2.priority = 1

    test_server1.auth_type = auth_type1
    test_server1.users = TacacsDockerServer1.USERS_BY_AUTH_TYPE[test_server1.auth_type]
    test_server2.auth_type = auth_type2
    test_server2.users = TacacsDockerServer2.USERS_BY_AUTH_TYPE[test_server2.auth_type]

    generic_aaa_test_accounting_unreachable_top_server(test_api, engines, topology_obj, request, switch_hostname,
                                                       local_adminuser,
                                                       remote_aaa_type=RemoteAaaType.TACACS,
                                                       remote_aaa_obj=System().aaa.tacacs,
                                                       server1=test_server1, server2=test_server2)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_accounting_local_first(test_api, engines, topology_obj, request, local_adminuser: UserInfo,
                                       switch_hostname: str):
    """
    @summary: Verify that when top server becomes unreachable, accounting logs are sent to next available server only

        Steps:
        1. configure tacacs with several top unreachable servers
        2. configure also reachable server with lower priority
        3. enable accounting
        4. enable tacacs
        5. verify accounting logs on top available server only for tacacs users events
        6. make unreachable server reachable
        7. verify accounting logs now on the top reachable server
    """
    addressing_type = random.choice(AddressingType.ALL_TYPES)
    auth_type = random.choice(AuthType.ALL_TYPES)

    test_server = TacacsDockerServer1.SERVER_BY_ADDRESSING_TYPE[addressing_type].copy()
    test_server.auth_type = auth_type
    test_server.users = TacacsDockerServer1.USERS_BY_AUTH_TYPE[test_server.auth_type]

    generic_aaa_test_accounting_local_first(test_api, engines, topology_obj, request, switch_hostname, local_adminuser,
                                            remote_aaa_type=RemoteAaaType.TACACS,
                                            remote_aaa_obj=System().aaa.tacacs,
                                            server=test_server)


@pytest.mark.security
@pytest.mark.simx_security
@pytest.mark.parametrize('test_api', [random.choice(ApiType.ALL_TYPES)])
def test_tacacs_timeout(test_api, engines, topology_obj, local_adminuser: UserInfo):
    """
    @summary: Verify timeout functionality

        In case that server is not reachable, the client (switch) will wait for respond for <timeout> seconds,
            after which it aborts and fails the attempt.

        Steps:
        1. Set unreachable tacacs server with some timeout
        2. Make authentication attempt and measure time
        3. Verify respond time >= timeout
        4. Set another unreachable server
        5. Make authentication attempt and measure time
        6. Verify respond time >= sum of timeouts

    """
    TestToolkit.tested_api = test_api

    aaa = System().aaa
    try:
        with allure.step('Set unreachable tacacs server with some timeout'):
            rand_timeout = random.randint(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][0],
                                          TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][-1] // 3)
            rand_timeout = 19
            logging.info(f'Chosen timeout: {rand_timeout}')
            # configure_resource(engines, resource_obj=aaa.tacacs, conf={
            #     AaaConsts.RETRANSMIT: 0
            # })
            configure_resource(engines, resource_obj=aaa.tacacs.hostname.hostname_id['1.2.3.4'], conf={
                AaaConsts.TIMEOUT: rand_timeout,
                AaaConsts.SECRET: "xyz",
                AaaConsts.PORT: 555
            })

        with allure.step('Set tacacs in authentication order and failthrough off'):
            configure_resource(engines, resource_obj=aaa.authentication, conf={
                AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
                AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
            }, apply=True, verify_apply=False)

        with allure.step('Make authentication attempt and measure time'):
            authenticator = SshAuthenticator(local_adminuser.username, local_adminuser.password, engines.dut.ip)
            _, timestamp1 = authenticator.attempt_login_failure()
            _, timestamp2 = authenticator.attempt_login_success(restart_session_process=False)
            engines.dut.disconnect()

        with allure.step(f'Verify respond time >= timeout'):
            assert timestamp2 - timestamp1 >= rand_timeout, f'Timeout was too short. Expected: {rand_timeout}'

        with allure.step('Set another unreachable server with timeout'):
            rand_timeout2 = random.randint(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][0],
                                           TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][-1] // 3)
            logging.info(f'Chosen timeout: {rand_timeout2}')
            configure_resource(engines, resource_obj=aaa.tacacs.hostname.hostname_id['2.4.6.8'], conf={
                AaaConsts.PRIORITY: 2,
                AaaConsts.TIMEOUT: rand_timeout2,
                AaaConsts.SECRET: "xyz",
                AaaConsts.PORT: 555
            }, apply=True, verify_apply=False)

        with allure.step('Make authentication attempt and measure time'):
            _, timestamp1 = authenticator.attempt_login_failure()
            _, timestamp2 = authenticator.attempt_login_success(restart_session_process=False)
            engines.dut.disconnect()

        with allure.step('Verify respond time >= sum of timeouts'):
            assert timestamp2 - timestamp1 >= rand_timeout + rand_timeout2, \
                f'Timeout was too short. Expected: {rand_timeout + rand_timeout2}'
    finally:
        logging.info('Disconnect local engine for cleanup steps')
        engines.dut.disconnect()

        # with allure.step('Remote reboot'):
        #     NvueGeneralCli(engines.dut).remote_reboot(topology_obj)

        # with allure.step('Clear aaa configuration'):
        #     aaa.unset(apply=True).verify_result()
