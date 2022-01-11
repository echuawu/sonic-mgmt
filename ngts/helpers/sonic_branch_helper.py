def get_sonic_branch(topology):
    """
    Get the SONiC branch based on release field from /etc/sonic/sonic_version.yml
    :param topology: topology fixture object
    :return: branch name
    """
    branch = topology.players['dut']['engine'].run_cmd("sonic-cfggen -y /etc/sonic/sonic_version.yml -v release")
    # master branch always has release "none"
    if branch == "none":
        branch = "master"
    return branch
