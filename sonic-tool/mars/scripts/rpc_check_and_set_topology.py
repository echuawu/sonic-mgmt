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


def get_sonic_hwsku(duthost):
    return duthost.run('redis-cli -n 4 hget "DEVICE_METADATA|localhost" hwsku').stdout.strip()


def mock_t1_topo_on_ptf32(duthost):
    """
    Hack the DEVICE_NEIGHBOR_METADATA table for the ptf32 topo on "Mellanox-SN4600C-C64" to simulate the
    dual tor t1 topo
    :param duthost: dut host engine
    """
    logger.info("mock t1 topo on ptf32")
    neighbors = duthost.run("redis-cli -n 4 keys DEVICE_NEIGHBOR*").stdout.strip("\n").split("\n")
    vm_hwsku = "Arista-VM"
    lo_addr = None

    add_neighbor_metadata_cmd_pattern = 'redis-cli -n 4 hset "DEVICE_NEIGHBOR_METADATA|{}" hwsku {} lo_addr {} mgmt_addr {}  type {}'

    mgmt_addr_patern = "10.75.207.{}"
    for index, neighbor in enumerate(neighbors):
        neighbor_name = duthost.run('redis-cli -n 4 hget \"{}\" name'.format(neighbor)).stdout.strip("\n")
        mgmt_addr = mgmt_addr_patern.format(10+index)
        if neighbor_name.endswith("T0"):
            router_type = "ToRRouter"
        else:
            router_type = "SpineRouter"
        add_neighbor_metadata_cmd = add_neighbor_metadata_cmd_pattern.format(neighbor_name, vm_hwsku, lo_addr, mgmt_addr, router_type)
        duthost.run(add_neighbor_metadata_cmd)
    enable_qos_config_and_reload_config(duthost)


def mock_t0_topo_on_ptf32(duthost):
    """
    Hack the DEVICE_NEIGHBOR_METADATA table for the ptf32 topo on "Mellanox-SN2700-D48C8" to simulate the
    dual tor t0 topo
    :param duthost: dut host engine
    """
    logger.info("mock t0 topo on ptf32")
    neighbors = duthost.run("redis-cli -n 4 keys DEVICE_NEIGHBOR*").stdout.strip("\n").split("\n")
    for index, neighbor in enumerate(neighbors):
        neighbor_name = duthost.run('redis-cli -n 4 hget \"{}\" name'.format(neighbor)).stdout.strip("\n")
        mgmt_addr = "10.75.207.{}".format(index+1)
        if neighbor_name.endswith("T0"):
            new_neighbor_name = neighbor_name.replace("T0", "T1")
            router_type = "LeafRouter"
            add_neighbor_metadata_cmd = 'redis-cli -n 4 hset "DEVICE_NEIGHBOR_METADATA|{}" ' \
                                        'hwsku Arista-VM lo_addr None mgmt_addr {} type {}'.format(new_neighbor_name, mgmt_addr, router_type)
            logger.info("Add DEVICE_NEIGHBOR_METADATA with cmd:{}".format(add_neighbor_metadata_cmd))
            duthost.run(add_neighbor_metadata_cmd)
            update_neighbor_name_cmd = 'redis-cli -n 4 hset "{}" name {}'.format(neighbor, new_neighbor_name)
        elif neighbor_name.endswith("T2"):
            update_neighbor_name_cmd = 'redis-cli -n 4 hset "{}" name Servers{} port eth0'.format(neighbor, index)
        logger.info("Update DEVICE_NEIGHBOR name with cmd:{}".format(update_neighbor_name_cmd))
        duthost.run(update_neighbor_name_cmd)
    logger.info("Set type to ToRRouter and subtype to DualToR in DEVICE_METADATA|localhost")
    duthost.run('redis-cli -n 4 hset "DEVICE_METADATA|localhost" type ToRRouter subtype DualToR')

    enable_qos_config_and_reload_config(duthost)


def enable_qos_config_and_reload_config(duthost):
    enable_qos_remap_table = 'redis-cli -n 4 hset "SYSTEM_DEFAULTS|tunnel_qos_remap" status enabled'
    duthost.run(enable_qos_remap_table)
    duthost.run("sudo config qos reload --no-dynamic-buffer")
    duthost.run("sudo config save -y")
    duthost.run("sudo config reload -y -f")
    duthost.run("sleep 180")


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

    with sonic_mgmt.cd(ansible_path):
        cmd = "ansible-playbook -i inventory --limit {SWITCH} post_upgrade_check.yml -e topo={TOPO} -b -vvv ".format(SWITCH=dut_name, TOPO=expected_topo)
        logger.info("Running CMD: {}".format(cmd))
        sonic_mgmt.run(cmd)

    sonic_dut.open()
    hwsku = get_sonic_hwsku(sonic_dut)
    if expected_topo == "ptf32" and hwsku in ["Mellanox-SN4600C-C64"]:
        mock_t1_topo_on_ptf32(sonic_dut)
    elif expected_topo == "ptf32" and hwsku in ["Mellanox-SN2700-D48C8"]:
        mock_t0_topo_on_ptf32(sonic_dut)
