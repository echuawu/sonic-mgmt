import logging
import random
from typing import Dict

import pytest

import ngts.tools.test_utils.allure_utils as allure
from ngts.constants.constants import GnmiConsts
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.security_test_tools.constants import AddressingType, AuthConsts, AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.generic_remote_aaa_testing.constants import RemoteAaaType
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.RemoteAaaServerInfo import RemoteAaaServerInfo
from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo
from ngts.tests_nvos.general.security.tacacs.constants import TacacsDockerServer0
from ngts.tests_nvos.general.security.test_aaa_ldap.ldap_servers_info import LdapServersP3
from ngts.tests_nvos.general.security.test_aaa_radius.constants import RadiusVmServer
from ngts.tests_nvos.system.gnmi.GnmiClient import GnmiClient
from ngts.tests_nvos.system.gnmi.constants import DUT_HOSTNAME_FOR_CERT, ETC_HOSTS, SERVICE_PEM, DOCKER_CERTS_DIR

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def install_gnmi_on_sonic_mgmt(engines):
    """
    enable rsyslog on sonic-mgmt container
    """
    gnmic_install_output = engines.sonic_mgmt.run_cmd("bash -c \"$(curl -sL https://get-gnmic.openconfig.net)\"")
    assert 'gnmic installed into /usr/local/bin/gnmic' in gnmic_install_output \
           or 'gnmic is already at latest' in gnmic_install_output, f"gnmic installation failed with: {gnmic_install_output}"


@pytest.fixture(scope='session', autouse=True)
def install_grpcurl_on_player(engines):
    with allure.step('install grpcurl'):
        player = GnmiClient('', '', '', '', 10, verify_tools_installed=False)
        player._run_cmd_in_process(
            'sudo wget -O /tmp/grpcurl.tar.gz https://github.com/fullstorydev/grpcurl/releases/download/v1.8.8/grpcurl_1.8.8_linux_x86_64.tar.gz')
        player._run_cmd_in_process('sudo tar -xzvf /tmp/grpcurl.tar.gz -C /tmp')
        player._run_cmd_in_process('sudo mv /tmp/grpcurl /usr/local/bin/')
        player._run_cmd_in_process('sudo rm /tmp/grpcurl.tar.gz')
    with allure.step('verify grpcurl installed'):
        player._verify_grpcurl_installed()


@pytest.fixture()
def aaa_users(engines) -> Dict[str, UserInfo]:
    with allure.step('set AAA servers'):
        with allure.step('set tacacs server'):
            tac_server: RemoteAaaServerInfo = TacacsDockerServer0.SERVER_BY_ADDRESSING_TYPE[
                random.choice(AddressingType.ALL_TYPES)]
            tac_server.configure(engines)
        with allure.step('set ldap server'):
            ldap_server: RemoteAaaServerInfo = LdapServersP3.LDAP1_SERVERS[random.choice(AddressingType.ALL_TYPES)]
            ldap_server.configure(engines)
        with allure.step('set radius server'):
            rad_server: RemoteAaaServerInfo = RadiusVmServer.SERVER_BY_ADDRESSING_TYPE[
                random.choice(AddressingType.ALL_TYPES)]
            rad_server.configure(engines)
        with allure.step('enable failthrough'):
            System().aaa.authentication.set(AuthConsts.FAILTHROUGH, AaaConsts.ENABLED, apply=True).verify_result()
    return {
        RemoteAaaType.TACACS: tac_server.users[0],
        RemoteAaaType.LDAP: ldap_server.users[0],
        RemoteAaaType.RADIUS: rad_server.users[0],
    }
    # servers config cleared in clear_conf hook func


@pytest.fixture()
def add_etc_host_mapping(engines):
    with allure.step(f'change dut hostname to {DUT_HOSTNAME_FOR_CERT}'):
        System().set('hostname', DUT_HOSTNAME_FOR_CERT, ask_for_confirmation=True, apply=True).verify_result()
    with allure.step(f'add mapping of new dut hostname to {ETC_HOSTS}'):
        client = GnmiClient('', '', '', '')
        client._run_cmd_in_process(f'echo "{engines.dut.ip} {DUT_HOSTNAME_FOR_CERT}" | sudo tee -a {ETC_HOSTS}')
    yield
    with allure.step(f'remove hostname mapping fro {ETC_HOSTS}'):
        client._run_cmd_in_process(f"sudo sed -i '/{DUT_HOSTNAME_FOR_CERT}/d' {ETC_HOSTS}")


@pytest.fixture()
def backup_and_restore_gnmi_cert(engines):
    with allure.step('backup orig gnmi cert'):
        engines.dut.run_cmd(
            f'docker exec {GnmiConsts.GNMI_DOCKER} cp {DOCKER_CERTS_DIR}/{SERVICE_PEM} {DOCKER_CERTS_DIR}/{SERVICE_PEM}-orig')
    yield
    with allure.step('restore orig gnmi cert'):
        engines.dut.run_cmd(
            f'docker exec {GnmiConsts.GNMI_DOCKER} cp {DOCKER_CERTS_DIR}/{SERVICE_PEM}-orig {DOCKER_CERTS_DIR}/{SERVICE_PEM}')
    with allure.step('reload gnmi'):
        System().gnmi_server.disable_gnmi_server(True)
        System().gnmi_server.enable_gnmi_server(True)
