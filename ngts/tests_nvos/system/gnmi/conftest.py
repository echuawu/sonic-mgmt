import logging
import random
import string
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
from ngts.tests_nvos.system.gnmi.GnmiClient import GnmiClient
from ngts.tests_nvos.system.gnmi.constants import ETC_HOSTS, GNMI_TEST_CERT, DUT_MOUNT_GNMI_CERT_DIR

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def install_gnmi_on_player(engines):
    """
    enable rsyslog on sonic-mgmt container
    """
    with allure.step('check if gnmic already installed'):
        player = engines.sonic_mgmt
        out = player.run_cmd('gnmic version')
        gnmic_installed = 'command not found' not in out
        logger.info(f'gnmic is {"" if gnmic_installed else "not "}installed on player')
    if not gnmic_installed:
        with allure.step('install gnmic on player'):
            out = player.run_cmd("bash -c \"$(curl -sL https://get-gnmic.openconfig.net)\"")
            assert 'gnmic installed into /usr/local/bin/gnmic' in out \
                   or 'gnmic is already at latest' in out, f"gnmic installation failed with: {out}"


@pytest.fixture(scope='session', autouse=True)
def install_grpcurl_on_player(engines):
    with allure.step('install grpcurl'):
        player = GnmiClient('', '', '', '', 10)
        player._run_cmd_in_process(
            'sudo wget -O /tmp/grpcurl.tar.gz https://github.com/fullstorydev/grpcurl/releases/download/v1.8.8/grpcurl_1.8.8_linux_x86_64.tar.gz',
            wait_till_done=True)
        player._run_cmd_in_process('sudo tar -xzvf /tmp/grpcurl.tar.gz -C /tmp', wait_till_done=True)
        player._run_cmd_in_process('sudo mv /tmp/grpcurl /usr/local/bin/', wait_till_done=True)
        player._run_cmd_in_process('sudo rm /tmp/grpcurl.tar.gz', wait_till_done=True)
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
def gnmi_cert_hostname(engines):
    cert = GNMI_TEST_CERT
    hostname = cert.ip or cert.dn

    if not cert.ip:
        assert cert.dn, f'{cert.name} has no ip/dn'
        with allure.step(f'change dut hostname to {cert.dn}'):
            System().set('hostname', cert.dn, ask_for_confirmation=True, apply=True).verify_result()
        with allure.step(f'add mapping of new dut hostname to {ETC_HOSTS}'):
            client = GnmiClient('', '', '', '')
            client._run_cmd_in_process(f'echo "{engines.dut.ip} {cert.dn}" | sudo tee -a {ETC_HOSTS}',
                                       wait_till_done=True)
    yield hostname
    if not cert.ip:
        with allure.step(f'remove hostname mapping fro {ETC_HOSTS}'):
            client._run_cmd_in_process(f"sudo sed -i '/{cert.dn}/d' {ETC_HOSTS}", wait_till_done=True)


@pytest.fixture()
def restore_gnmi_cert(engines):
    yield
    with allure.step('restore orig gnmi cert'):
        engines.dut.run_cmd(f'sudo rm -f {DUT_MOUNT_GNMI_CERT_DIR}/*')
    with allure.step('reload gnmi'):
        System().gnmi_server.disable_gnmi_server(True)
        System().gnmi_server.enable_gnmi_server(True)


@pytest.fixture()
def gnmi_cert_id():
    rand_id = ''.join(random.choice(string.ascii_letters) for _ in range(6))
    with allure.step(f'import certificate for gnmi as "{rand_id}"'):
        pass  # TODO: complete
    return rand_id
