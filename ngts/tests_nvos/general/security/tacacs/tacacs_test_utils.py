import random
from typing import Union

from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.system.Hostname import HostnameId
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthType
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo, \
    update_active_aaa_server, TacacsServerInfo
from ngts.tests_nvos.general.security.tacacs.constants import TacacsVmServer, TacacsConsts
from ngts.tools.test_utils import allure_utils as allure


def update_tacacs_server_auth_type(engines, item, server_info: RemoteAaaServerInfo, server_resource: HostnameId,
                                   auth_type: str):
    assert auth_type in AuthType.ALL_TYPES, f'{auth_type} is not one of {AuthType.ALL_TYPES}'
    with allure.step(f'Set server auth-type to: {auth_type}'):
        server: Union[TacacsServerInfo, RemoteAaaServerInfo] = server_info
        server.update_auth_type(auth_type, item)
        update_active_aaa_server(item, server_info)


def get_two_different_tacacs_servers():
    server1 = list(TacacsVmServer.VM_SERVERS.values())[0].copy()
    server2 = list(TacacsVmServer.VM_SERVERS.values())[1].copy()
    auth_type1 = random.choice(TacacsConsts.AUTH_TYPES)
    auth_type2 = RandomizationTool.select_random_value(TacacsConsts.AUTH_TYPES,
                                                       forbidden_values=[auth_type1]).get_returned_value()
    server1.auth_type = auth_type1
    server1.users = TacacsVmServer.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type1]
    server2.auth_type = auth_type2
    server2.users = TacacsVmServer.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type2]
    return server1, server2
