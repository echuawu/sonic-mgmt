import allure
import pexpect
import logging
from infra.tools.general_constants.constants import DefaultConnectionValues


logger = logging.getLogger(__name__)


def create_ssh_login_engine(dut_ip, username, port=22):
    '''
    @summary: in this function we want to create ssh connection to device,
    ssh connection means that only executing the command:
    'ssh {-o OPTIONS} -l {username} {dut_ip}'
    without entering password!
    :param dut_ip: device IP
    :param username: username intiaiting the ssh connection
    :param port: connection port, by default 22
    :return: pexpect python module with ssh connection command executed as the spwan command
    '''
    _ssh_command = 'ssh {} -p {} -l {} {}'.format(DefaultConnectionValues.BASIC_SSH_CONNECTION_OPTIONS,
                                                  port,
                                                  username,
                                                  dut_ip)
    # connect to device
    child = pexpect.spawn(_ssh_command, env={'TERM': 'dumb'}, timeout=10)
    return child


def ssh_to_device_and_retrieve_raw_login_ssh_notification(dut_ip,
                                                          username=DefaultConnectionValues.ADMIN,
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