from ngts.nvos_tools.system.Hostname import HostnameId
from ngts.tests_nvos.general.security.security_test_tools.constants import AuthType, AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo, \
    update_active_aaa_server
from ngts.tests_nvos.general.security.tacacs.constants import TacacsServers
from ngts.tools.test_utils import allure_utils as allure
import logging


def update_tacacs_auth_type(engines, item, server_info: RemoteAaaServerInfo, server_resource: HostnameId, auth_type: str):
    assert auth_type in AuthType.ALL_TYPES, f'{auth_type} is not one of {AuthType.ALL_TYPES}'
    with allure.step(f'Set auth-type to: {auth_type}'):
        server_resource.set(AaaConsts.AUTH_TYPE, auth_type, dut_engine=getattr(item, 'active_remote_admin_engine'),
                            apply=True)
        logging.info(f'Update users to use {auth_type} passwords')
        server_info.users = TacacsServers.VM_SERVER_USERS_BY_AUTH_TYPE[auth_type]
        update_active_aaa_server(item, server_info)
