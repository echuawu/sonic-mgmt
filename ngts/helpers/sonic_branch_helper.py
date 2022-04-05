import logging

from paramiko.ssh_exception import SSHException
from ngts.constants.constants import NvosCliTypes
logger = logging.getLogger()


def get_sonic_branch(topology):
    """
    Get the SONiC branch based on release field from /etc/sonic/sonic_version.yml
    :param topology: topology fixture object
    :return: branch name
    """
    try:
        branch = topology.players['dut']['engine'].run_cmd("sonic-cfggen -y /etc/sonic/sonic_version.yml -v release")
    except SSHException as err:
        branch = 'Unknown'
        logger.error(f'Unable to get branch. Assuming that the device is not reachable. Setting the branch as Unknown. '
                     f'Got error: {err}')
    # master branch always has release "none"
    except Exception as nvueerr:
        if topology.players['dut']['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] \
                in NvosCliTypes.NvueCliTypes:
            branch = "master"
            logger.warning(f'unable to run sonic cmd on dut. Assuming that sonic image is not installed on this device '
                           f'Got error: {nvueerr}')
        else:
            raise nvueerr

    if branch == "none":
        branch = "master"
    return branch.strip()


def update_branch_in_topology(topology, branch=None):
    """
    Method which doing update for SONiC branch in topology object
    :param topology: topology fixture object
    :param branch: SONiC branch, example: "202106"
    """
    if not branch:
        branch = get_sonic_branch(topology)
    topology.players['dut']['branch'] = branch


def update_sanitizer_in_topology(topology):
    """
    Method which doing update for SONiC branch in topology object
    :param topology: topology fixture object
    :param branch: SONiC branch, example: "202106"
    """
    topology.players['dut']['sanitizer'] = is_sanitizer_image(topology)


def is_sanitizer_image(topology):
    dut_engine = topology.players['dut']['engine']
    is_sanitizer = False
    try:
        sanitizer = dut_engine.run_cmd("sonic-cfggen -y /etc/sonic/sonic_version.yml -v asan")
    except SSHException as err:
        logger.warning(f'Unable to get sanitizer. Assuming that the device is not reachable. '
                       f'Setting the sanitizer as False, '
                       f'Got error: {err}')
    if sanitizer == "yes":
        logger.info("The sonic image has sanitizer")
        is_sanitizer = True
    return is_sanitizer
