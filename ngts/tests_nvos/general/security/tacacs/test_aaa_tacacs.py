import logging
import time

import pytest
import random

from ngts.nvos_constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts, AuthConsts, AuthType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.generic_remote_aaa_testing import *
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import configure_resource, \
    verify_users_auth, verify_user_auth
from ngts.tests_nvos.general.security.security_test_tools.switch_authenticators import SshAuthenticator
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import \
    update_active_aaa_server
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.tacacs.constants import TacacsConsts, TacacsServers
from ngts.tests_nvos.general.security.tacacs.tacacs_test_utils import update_tacacs_auth_type
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.security
@pytest.mark.simx
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
            tacacs_obj: TacacsConsts.DEFAULT_TACACS_CONF
        }
    )


@pytest.mark.security
@pytest.mark.simx
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
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
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
                          feature_resource_obj=tacacs,
                          server_by_addr_type=TacacsServers.DOCKER_SERVERS,
                          test_param=AuthType.ALL_TYPES,
                          test_param_update_func=update_tacacs_auth_type)


# -------------------- NEW TESTS ---------------------


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_tacacs_unique_priority(test_api, engines, topology_obj):
    """
    @summary: Verify that hostname priority must be unique

        Steps:
        1. Set 2 hostnames with different priority - expect success
        2. set another hostname with existing priority - expect failure

    """
    TestToolkit.tested_api = test_api

    with allure.step('Set 2 hostnames with different priority - expect success'):
        tacacs = System().aaa.tacacs
        rand_prio1 = RandomizationTool.select_random_value(TacacsConsts.VALID_VALUES[AaaConsts.PRIORITY]) \
            .get_returned_value()
        tacacs.hostname.hostname_id['1.2.3.4'].set(AaaConsts.PRIORITY, rand_prio1).verify_result()
        rand_prio2 = RandomizationTool.select_random_value(TacacsConsts.VALID_VALUES[AaaConsts.PRIORITY],
                                                           forbidden_values=[rand_prio1]).get_returned_value()
        tacacs.hostname.hostname_id['2.4.6.8'].set(AaaConsts.PRIORITY, rand_prio2, apply=True).verify_result()

    with allure.step('Set another hostname with existing priority - expect fail'):
        tacacs.hostname.hostname_id['3.6.9.12'].set(AaaConsts.PRIORITY, rand_prio2, apply=True).verify_result(False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
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
    TestToolkit.tested_api = test_api

    with allure.step('Configure tacacs server with bad secret'):
        bad_secret = RandomizationTool.get_random_string(6)
        logging.info(f'Randomized bad secret: {bad_secret}')
        server = random.choice(list(TacacsServers.VM_SERVERS.values())).copy()
        logging.info(f'chosen server: {server.hostname}')
        auth_type = random.choice(TacacsConsts.AUTH_TYPES)
        logging.info(f'chosen auth-type: {auth_type}')
        server.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type]
        aaa = System().aaa
        server_resource = aaa.tacacs.hostname.hostname_id[server.hostname]
        configure_resource(engines, resource_obj=server_resource, conf={
            AaaConsts.SECRET: bad_secret,
            AaaConsts.PORT: server.port,
            AaaConsts.TIMEOUT: server.timeout,
            # AaaConsts.RETRANSMIT: server.retransmit,
            AaaConsts.AUTH_TYPE: auth_type
        })
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True)

    with allure.step('Verify auth fail'):
        verify_user_auth(engines, topology_obj, random.choice(server.users), expect_login_success=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_tacacs_bad_port(test_api, engines, topology_obj):
    """
    @summary: Verify that tacacs users can't auth when bad port is configured.

        Steps:
        1. configure tacacs server
        2. set bad port
        3. verify auth - expect fail
    """
    TestToolkit.tested_api = test_api

    with allure.step('Configure tacacs server with bad port'):
        server = random.choice(list(TacacsServers.VM_SERVERS.values())).copy()
        logging.info(f'chosen server: {server.hostname}')
        auth_type = random.choice(TacacsConsts.AUTH_TYPES)
        logging.info(f'chosen auth-type: {auth_type}')
        bad_port = RandomizationTool.select_random_value(TacacsConsts.VALID_VALUES[AaaConsts.PORT],
                                                         forbidden_values=[server.port]).get_returned_value()
        logging.info(f'chosen bad port: {bad_port}')
        server.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type]
        aaa = System().aaa
        server_resource = aaa.tacacs.hostname.hostname_id[server.hostname]
        configure_resource(engines, resource_obj=server_resource, conf={
            AaaConsts.SECRET: server.secret,
            AaaConsts.PORT: bad_port,
            AaaConsts.TIMEOUT: server.timeout,
            # AaaConsts.RETRANSMIT: server.retransmit,
            AaaConsts.AUTH_TYPE: auth_type
        })
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True)

    with allure.step('Verify auth fail'):
        verify_user_auth(engines, topology_obj, random.choice(server.users), expect_login_success=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_tacacs_priority(test_api, engines, topology_obj, request):
    """
    @summary: Verify that auth is done via the top prioritized server

        Steps:
        1. set and prioritize 2 servers
        2. verify auth is done via top prioritized server
        3. advance the lowest prioritized server to be most prioritized
        4. repeat steps 2-3 until reach priority 8 (max)
    """
    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step('Set and prioritize 2 tacacs servers'):
        server1 = list(TacacsServers.VM_SERVERS.values())[0].copy()
        server2 = list(TacacsServers.VM_SERVERS.values())[1].copy()
        server1.priority = 1
        server2.priority = 2
        auth_type1 = random.choice(TacacsConsts.AUTH_TYPES)
        auth_type2 = RandomizationTool.select_random_value(TacacsConsts.AUTH_TYPES,
                                                           forbidden_values=[auth_type1]).get_returned_value()
        server1.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type1]
        server2.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type2]
        aaa = System().aaa
        configure_resource(engines, resource_obj=aaa.tacacs, conf={
            AaaConsts.TIMEOUT: server1.timeout,
            # AaaConsts.RETRANSMIT: server1.retransmit
        })
        server1_resource = aaa.tacacs.hostname.hostname_id[server1.hostname]
        configure_resource(engines, resource_obj=server1_resource, conf={
            AaaConsts.SECRET: server1.secret,
            AaaConsts.PORT: server1.port,
            AaaConsts.PRIORITY: server1.priority,
            AaaConsts.AUTH_TYPE: auth_type1
        })
        server2_resource = aaa.tacacs.hostname.hostname_id[server2.hostname]
        configure_resource(engines, resource_obj=server2_resource, conf={
            AaaConsts.SECRET: server2.secret,
            AaaConsts.PORT: server2.port,
            AaaConsts.PRIORITY: server2.priority,
            AaaConsts.AUTH_TYPE: auth_type2
        })
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True, verify_apply=False)

        top_server = server2
        lower_server = server1
        update_active_aaa_server(item, top_server)

    while True:
        with allure.step(f'Wait {TacacsConsts.TIME_TILL_TACACS_CONF_TAKES_PLACE} seconds'):
            time.sleep(TacacsConsts.TIME_TILL_TACACS_CONF_TAKES_PLACE)

        with allure.step(f'Verify auth is done via top prioritized server: {top_server}'):
            with allure.step(f'Verify auth via top server: {top_server} - expect success'):
                verify_user_auth(engines, topology_obj, random.choice(top_server.users), expect_login_success=True,
                                 verify_authorization=False)

            with allure.step(f'Verify auth via lower server: {lower_server} - expect fail'):
                verify_user_auth(engines, topology_obj, random.choice(lower_server.users), expect_login_success=False)

        if top_server.priority == TacacsConsts.VALID_VALUES[AaaConsts.PRIORITY][-1]:
            break

        next_prio = random.randint(top_server.priority + 1, TacacsConsts.VALID_VALUES[AaaConsts.PRIORITY][-1])
        with allure.step(f'Advance lower server to be top prioritized to: {next_prio}'):
            lower_server_resource = aaa.tacacs.hostname.hostname_id[lower_server.hostname]
            lower_server.priority = next_prio
            configure_resource(engines, resource_obj=lower_server_resource, conf={
                AaaConsts.PRIORITY: lower_server.priority
            }, apply=True, verify_apply=False, dut_engine=item.active_remote_admin_engine)
            lower_server, top_server = top_server, lower_server
            update_active_aaa_server(item, top_server)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
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
    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step('Configure unreachable server'):
        server = list(TacacsServers.VM_SERVERS.values())[0].copy()
        logging.info(f'chosen server: {server.hostname}')
        auth_type = random.choice(TacacsConsts.AUTH_TYPES)
        logging.info(f'chosen auth-type: {auth_type}')
        server.auth_type = auth_type
        bad_port = RandomizationTool.select_random_value(TacacsConsts.VALID_VALUES[AaaConsts.PORT],
                                                         forbidden_values=[server.port]).get_returned_value()
        logging.info(f'chosen bad port: {bad_port}')
        server.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type]
        aaa = System().aaa
        configure_resource(engines, resource_obj=aaa.tacacs, conf={
            AaaConsts.TIMEOUT: server.timeout,
            # AaaConsts.RETRANSMIT: server.retransmit
        })
        server_resource = aaa.tacacs.hostname.hostname_id[server.hostname]
        configure_resource(engines, resource_obj=server_resource, conf={
            AaaConsts.SECRET: server.secret,
            AaaConsts.PORT: bad_port,
            AaaConsts.AUTH_TYPE: server.auth_type,
            AaaConsts.PRIORITY: 2
        })

    with allure.step('Set tacacs in authentication order and failthrough off'):
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True)

    with allure.step('Verify auth - success only with local user'):
        verify_users_auth(engines, topology_obj,
                          users=[random.choice(server.users), local_adminuser],
                          expect_login_success=[False, True], verify_authorization=False)

    with allure.step('Configure secondary prioritized server'):
        server2 = list(TacacsServers.VM_SERVERS.values())[1].copy()
        logging.info(f'chosen server: {server2.hostname}')
        auth_type2 = RandomizationTool.select_random_value(TacacsConsts.AUTH_TYPES,
                                                           forbidden_values=[server.auth_type]).get_returned_value()
        logging.info(f'chosen auth-type: {auth_type2}')
        server2.auth_type = auth_type2
        server2.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type2]
        server2_resource = aaa.tacacs.hostname.hostname_id[server2.hostname]
        configure_resource(engines, resource_obj=server2_resource, conf={
            AaaConsts.SECRET: server2.secret,
            AaaConsts.PORT: server2.port,
            AaaConsts.AUTH_TYPE: server2.auth_type
        }, apply=True, verify_apply=False)
        update_active_aaa_server(item, server2)

    with allure.step('Verify auth – success only with 2nd server user'):
        verify_users_auth(engines, topology_obj,
                          users=[random.choice(server.users), local_adminuser, random.choice(server2.users)],
                          expect_login_success=[False, False, True], verify_authorization=False)

    with allure.step('Make the 2nd server also unreachable'):
        configure_resource(engines, resource_obj=server2_resource, conf={
            AaaConsts.PORT: bad_port
        }, apply=True, verify_apply=False, dut_engine=item.active_remote_admin_engine)
        update_active_aaa_server(item, None)

    with allure.step('Verify auth – success only with local user'):
        verify_users_auth(engines, topology_obj,
                          users=[random.choice(server.users), random.choice(server2.users), local_adminuser],
                          expect_login_success=[False, False, True], verify_authorization=False)

    with allure.step('Bring back the first server'):
        configure_resource(engines, resource_obj=server_resource, conf={
            AaaConsts.PORT: server.port
        }, apply=True, verify_apply=False)
        update_active_aaa_server(item, server)

    with allure.step('Verify auth – success only with top server user'):
        verify_users_auth(engines, topology_obj,
                          users=[local_adminuser, random.choice(server2.users), random.choice(server.users)],
                          expect_login_success=[False, False, True], verify_authorization=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
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
    TestToolkit.tested_api = test_api
    item = request.node

    with allure.step('Configure tacacs servers'):
        server = list(TacacsServers.VM_SERVERS.values())[0].copy()
        server2 = list(TacacsServers.VM_SERVERS.values())[1].copy()
        auth_type = random.choice(TacacsConsts.AUTH_TYPES)
        auth_type2 = RandomizationTool.select_random_value(TacacsConsts.AUTH_TYPES,
                                                           forbidden_values=[auth_type]).get_returned_value()
        server.auth_type = auth_type
        server2.auth_type = auth_type2
        server.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type]
        server2.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type2]
        aaa = System().aaa
        configure_resource(engines, resource_obj=aaa.tacacs, conf={
            AaaConsts.TIMEOUT: server.timeout,
            # AaaConsts.RETRANSMIT: server.retransmit
        })
        server_resource = aaa.tacacs.hostname.hostname_id[server.hostname]
        configure_resource(engines, resource_obj=server_resource, conf={
            AaaConsts.SECRET: server.secret,
            AaaConsts.PORT: server.port,
            AaaConsts.AUTH_TYPE: server.auth_type,
            AaaConsts.PRIORITY: 2
        })
        server2_resource = aaa.tacacs.hostname.hostname_id[server2.hostname]
        configure_resource(engines, resource_obj=server2_resource, conf={
            AaaConsts.SECRET: server2.secret,
            AaaConsts.PORT: server2.port,
            AaaConsts.AUTH_TYPE: server2.auth_type,
            AaaConsts.PRIORITY: 1
        })

    with allure.step('Set tacacs in authentication order and failthrough off'):
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.ORDER: f'{AuthConsts.TACACS},{AuthConsts.LOCAL}',
            AuthConsts.FAILTHROUGH: AaaConsts.DISABLED
        }, apply=True, verify_apply=False)
        update_active_aaa_server(item, server)

    with allure.step('Verify auth with 2nd server credentials – expect fail'):
        verify_user_auth(engines, topology_obj, random.choice(server2.users), expect_login_success=False)

    with allure.step('Verify auth with local user credentials - expect fail'):
        verify_user_auth(engines, topology_obj, local_adminuser, expect_login_success=False)

    with allure.step('Set failthrough on'):
        configure_resource(engines, resource_obj=aaa.authentication, conf={
            AuthConsts.FAILTHROUGH: AaaConsts.ENABLED
        }, apply=True, dut_engine=item.active_remote_admin_engine)
        update_active_aaa_server(item, None)

    with allure.step('Verify auth with 2nd server credentials – expect success'):
        verify_user_auth(engines, topology_obj, random.choice(server2.users), expect_login_success=True,
                         verify_authorization=False)

    with allure.step('Verify auth with local user credentials - expect success'):
        verify_user_auth(engines, topology_obj, local_adminuser, expect_login_success=True, verify_authorization=False)

    with allure.step('Verify auth with credentials from none of servers/local - expect fail'):
        dummy_user = local_adminuser.copy()
        dummy_user.username = f'dummy_{dummy_user.username}'
        verify_user_auth(engines, topology_obj, dummy_user, expect_login_success=False)


@pytest.mark.security
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
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

    with allure.step('Set unreachable tacacs server with some timeout'):
        rand_timeout = random.randint(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][0],
                                      TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT][-1] // 3)
        logging.info(f'Chosen timeout: {rand_timeout}')
        aaa = System().aaa
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

    with allure.step(f'Verify respond time >= timeout'):
        assert timestamp2 - timestamp1 >= rand_timeout, f'Timeout was too short. Expected: {rand_timeout}'

    with allure.step('Set another unreachable server with timeout'):
        rand_timeout2 = random.choice(TacacsConsts.VALID_VALUES[AaaConsts.TIMEOUT])
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

    with allure.step('Verify respond time >= sum of timeouts'):
        assert timestamp2 - timestamp1 >= rand_timeout + rand_timeout2, \
            f'Timeout was too short. Expected: {rand_timeout + rand_timeout2}'

    with allure.step('Clear aaa configuration'):
        aaa.unset(apply=True).verify_result()
