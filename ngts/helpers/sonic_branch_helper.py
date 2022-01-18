import logging

from paramiko.ssh_exception import SSHException

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
