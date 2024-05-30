import logging
import random
from typing import Dict

import pytest

import ngts.tools.test_utils.allure_utils as allure
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AddressingType, AuthConsts, AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.tacacs.constants import TacacsDockerServer0
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_servers_info import LdapServersP3
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusVmServer

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def install_gnmi_on_sonic_mgmt(engines):
    """
    enable rsyslog on sonic-mgmt container
    """
    gnmic_install_output = engines.sonic_mgmt.run_cmd("bash -c \"$(curl -sL https://get-gnmic.openconfig.net)\"")
    assert 'gnmic installed into /usr/local/bin/gnmic' in gnmic_install_output \
           or 'gnmic is already at latest' in gnmic_install_output, f"gnmic installation failed with: {gnmic_install_output}"


@pytest.fixture()
def aaa_users(engines) -> Dict[str, UserInfo]:
    with allure.step('set AAA servers'):
        with allure.step('set tacacs server'):
            tac_server: RemoteAaaServerInfo = TacacsDockerServer0.SERVER_BY_ADDRESSING_TYPE[random.choice(AddressingType.ALL_TYPES)]
            tac_server.configure(engines)
        with allure.step('set ldap server'):
            ldap_server: RemoteAaaServerInfo = LdapServersP3.LDAP1_SERVERS[random.choice(AddressingType.ALL_TYPES)]
            ldap_server.configure(engines)
        with allure.step('set radius server'):
            rad_server: RemoteAaaServerInfo = RadiusVmServer.SERVER_BY_ADDRESSING_TYPE[random.choice(AddressingType.ALL_TYPES)]
            rad_server.configure(engines)
        with allure.step('enable failthrough'):
            System().aaa.authentication.set(AuthConsts.FAILTHROUGH, AaaConsts.ENABLED, apply=True).verify_result()
    return {
        RemoteAaaType.TACACS: tac_server.users[0],
        RemoteAaaType.LDAP: ldap_server.users[0],
        RemoteAaaType.RADIUS: rad_server.users[0],
    }
    # servers config cleared in clear_conf hook func
