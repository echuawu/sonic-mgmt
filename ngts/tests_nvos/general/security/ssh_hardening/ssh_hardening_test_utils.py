import logging
import subprocess
import re

from ngts.tools.test_utils import allure_utils as allure
from infra.tools.connection_tools.proxy_ssh_engine import ProxySshEngine
from ngts.tests_nvos.general.security.ssh_hardening.constants import SshHardeningConsts


def get_ssh_verbose_output(server_engine: ProxySshEngine, timeout: int = SshHardeningConsts.TIMEOUT) -> str:
    """
    @summary: Run SSH with verbose flag and return its output
    @param server_engine: engine of the ssh server
    @param timeout: timeout to give the ssh command (to generate output)
    @return: Value of the verbose ssh command
    """
    with allure.step('Run ssh -vvvv to get info'):
        cmd = f'timeout {timeout} ssh -vvvv {server_engine.username}@{server_engine.ip}'
        try:
            logging.info(f"Run: '{cmd}'")
            res = subprocess.run(
                cmd.split(' '),
                # shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # check=True
            )
            std_output = str(res.stdout)
            err_output = str(res.stderr)
        except subprocess.CalledProcessError as e:
            logging.info(f'Error: {e}')
            raise e
    # logging.info(f'Errors: {err_output}')
    # logging.info(f'Output: {std_output}')
    output = err_output + '\n' + std_output
    return output


def get_ssh_server_proposal(server_engine: ProxySshEngine) -> str:
    """
    @summary: Get SSH server proposal from handshake phase
    @param server_engine: engine of the ssh server
    @return: Servers proposal from the handshake phase (string)
    """
    output = get_ssh_verbose_output(server_engine)

    with allure.step('Get server proposal lines'):
        pattern = r"peer server KEXINIT proposal(.*?)reserved"
        matches = re.findall(pattern, output, re.DOTALL)
        logging.info(f'Matches:\n{matches}')
        server_proposal = matches[0]
        logging.info(f'Server proposal:\n{server_proposal}')

    return server_proposal


def get_ssh_server_protocol(server_engine: ProxySshEngine) -> str:
    """
    @summary: Get the SSH protocol version of the given SSH server
    @param server_engine: engine of the ssh server
    @return: protocol version (str)
    """
    substr_to_find = 'Remote protocol version'
    ssh_verbose_output = get_ssh_verbose_output(server_engine)

    with allure.step('Extract relevant line'):
        lines = ssh_verbose_output.splitlines()
        property_line = [line for line in lines if substr_to_find in line][0]
        logging.info(f'Prop line: {property_line}')

    with allure.step('Extract ssh protocol from the relevant line'):
        pattern_to_find = fr"{substr_to_find} ([^\s\n,]+)"
        matches = re.findall(pattern_to_find, property_line)
        assert matches, f'Pattern "{pattern_to_find}" not found in "{property_line}"'
        logging.info(f'Matches: {matches}')
        return matches[0]
