import time
import allure
import pexpect
import logging
import pytest
from infra.tools.general_constants.constants import DefaultConnectionValues
from infra.tools.connection_tools.pexpect_serial_engine import PexpectSerialEngine
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System

logger = logging.getLogger(__name__)


def create_ssh_login_engine(dut_ip, username, port=22, custom_ssh_options=None):
    '''
    @summary: in this function we want to create ssh connection to device,
    ssh connection means that only executing the command:
    'ssh {-o OPTIONS} -l {username} {dut_ip}'
    without entering password!
    :param dut_ip: device IP
    :param username: username initiating the ssh connection
    :param port: connection port, by default 22
    :return: pexpect python module with ssh connection command executed
    '''
    ssh_options = custom_ssh_options if custom_ssh_options is not None else DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS
    _ssh_command = 'ssh {} -p {} -l {} {}'.format(ssh_options,
                                                  port,
                                                  username,
                                                  dut_ip)
    # connect to device
    child = pexpect.spawn(_ssh_command, env={'TERM': 'dumb'}, timeout=10)
    return child


def ssh_to_device_and_retrieve_raw_login_ssh_notification(dut_ip,
                                                          username=DefaultConnectionValues.DEFAULT_USER,
                                                          password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                                          port=22):
    '''
    @summary: in this function we create ssh connection
    and return the raw output after connecting to device
    '''
    notification_login_message = ''

    with allure.step("Connection to dut device with SSH"):
        logger.info("Connection to dut device with SSH")
        # connecting using pexpect
        try:
            child = create_ssh_login_engine(dut_ip, username, port)
            respond = child.expect([DefaultConnectionValues.PASSWORD_REGEX, '~'])
            if respond == 0:
                notification_login_message += child.before.decode('utf-8')
                child.sendline(password)
                child.expect(DefaultConnectionValues.DEFAULT_PROMPTS[0])

            # convert output to decode
            notification_login_message += child.before.decode('utf-8')
            # close connection
        finally:
            child.close()
        return notification_login_message


@pytest.fixture(scope='function')
def serial_engine(topology_obj):
    """
    :return: serial connection
    """
    att = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']
    # add connection options to pass connection problems
    extended_rcon_command = att['Specific']['serial_conn_cmd'].split(' ')
    extended_rcon_command.insert(1, DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS)
    extended_rcon_command = ' '.join(extended_rcon_command)
    serial_engine = PexpectSerialEngine(ip=att['Specific']['ip'],
                                        username=att['Topology Conn.']['CONN_USER'],
                                        password=att['Topology Conn.']['CONN_PASSWORD'],
                                        rcon_command=extended_rcon_command,
                                        timeout=30)
    serial_engine.create_serial_engine()
    return serial_engine


@pytest.fixture(scope='function')
def post_test_remote_reboot(topology_obj):
    '''
    @summary: perform remote reboot from the physical server using the noga remote reboot command,
    usually the command should be like this: '/auto/mswg/utils/bin/rreboot <ip|hostname>'
    after the test is done as a part of cleanup
    '''
    yield

    logging.info("Performing remote reboot to switch")
    cmd = topology_obj.players['dut_serial']['attributes'].noga_query_data['attributes']['Specific'][
        'remote_reboot']
    assert cmd, "Reboot command is empty"
    topology_obj.players['server']['engine'].run_cmd(cmd)
    SLEEP_AFTER_REBOOT = 60
    logging.info("Sleeping {} secs after reboot".format(SLEEP_AFTER_REBOOT))
    time.sleep(SLEEP_AFTER_REBOOT)
    # verify dockers are up
    logging.info("Verifying that dockers are up")
    TestToolkit.engines.dut.disconnect()
    nvue_cli = NvueGeneralCli(TestToolkit.engines.dut)
    nvue_cli.verify_dockers_are_up()


@pytest.fixture(scope='function')
def is_secure_boot_enabled(engines):
    res = "0"
    try:
        res = engines.dut.run_cmd('bootctl status 2>/dev/null | grep -c "Secure Boot: enabled"')
    except BaseException as err:
        logging.info(err)

    if res != "1":
        logging.info("The test is skipped - secure boot is disabled")
        pytest.skip("The test is skipped - secure boot is disabled")


@pytest.fixture(scope='function')
def reset_aaa():
    """
    @summary: fixture to reset aaa configuration before and after test
    """
    aaa_obj = System().aaa
    with allure.step('Reset aaa configuration before test'):
        aaa_obj.unset(apply=True)

    yield

    with allure.step('Reset aaa configuration after test'):
        aaa_obj.unset(apply=True)
