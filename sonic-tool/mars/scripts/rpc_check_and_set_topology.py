# Builtin libs
import argparse
import os
import sys
import re

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("PreTestCheck")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", required=True, dest="dut_name", help="The DUT name")
    parser.add_argument("--current_topo", required=True, dest="current_topo",
                        help="Current topology for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--expected_topo", required=True, dest="expected_topo",
                        help="Expected topology, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo")
    return parser.parse_args()


def get_sonic_branch(duthost):
    branch = duthost.run("sonic-cfggen -y /etc/sonic/sonic_version.yml -v release").stdout
    if branch == "none":
        branch = "master"
    return branch.strip()


if __name__ == "__main__":
    args = _parse_args()

    workspace_path = args.workspace_path
    repo_path = os.path.join(args.workspace_path, 'sonic-mgmt')
    ansible_path = os.path.join(repo_path, "ansible")

    current_topo = args.current_topo
    expected_topo = args.expected_topo
    dut_name = args.dut_name

    if current_topo == expected_topo:
        sys.exit()

    topo = parse_topology(args.topo)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)
    sonic_dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)

    sonic_mgmt = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                            config=Config(overrides={"run": {"echo": True}}),
                            connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})
    sonic_dut = Connection(sonic_dut_device.BASE_IP, user=sonic_dut_device.USERS[0].USERNAME,
                           config=Config(overrides={"run": {"echo": True}}),
                           connect_kwargs={"password": sonic_dut_device.USERS[0].PASSWORD})

    sonic_branch = get_sonic_branch(sonic_dut)
    logger.info('SONiC branch is: {}'.format(sonic_branch))
    ptf_tag = constants.BRANCH_PTF_MAPPING.get(sonic_branch, 'latest')

    try:
        with sonic_mgmt.cd(ansible_path):
            logger.info("Remove topo {}".format(current_topo))
            cmd = "./testbed-cli.sh -k ceos remove-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name, TOPO=current_topo)
            logger.info("Running CMD: {}".format(cmd))
            sonic_mgmt.run(cmd)
    except Exception as err:
        logger.info("Remove topo {} fail. Err log:{}".format(current_topo, err))

    with sonic_mgmt.cd(ansible_path):
        logger.info("Add topology")
        cmd = "./testbed-cli.sh -k ceos add-topo {SWITCH}-{TOPO} vault -e ptf_imagetag={PTF_TAG}".format(SWITCH=dut_name,
                                                                                                         TOPO=expected_topo,
                                                                                                         PTF_TAG=ptf_tag)
        logger.info("Running CMD: {}".format(cmd))
        sonic_mgmt.run(cmd)

    with sonic_mgmt.cd(ansible_path):
        cmd = "./testbed-cli.sh deploy-mg {SWITCH}-{TOPO} lab vault".format(SWITCH=dut_name, TOPO=expected_topo)
        logger.info("Running CMD: {}".format(cmd))
        sonic_mgmt.run(cmd)
