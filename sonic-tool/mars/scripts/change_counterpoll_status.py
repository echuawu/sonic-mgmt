# Builtin libs
import argparse
import os
import sys

# Third-party libs
import yaml
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("Change_counterpoll_status")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--test-name", required=True, dest="test_name",
                        help="Specify the test name in case file, <Test><name>this_name</name></Test>")
    parser.add_argument("--sonic-topo", required=True, dest="sonic_topo",
                        help="The topo for SONiC testing, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--repo-name", dest="repo_name", help="Specify the sonic-mgmt repository name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo")
    parser.add_argument("--counterpoll-action", dest="counterpoll_action",
                        help="Specify the status of counterpoll")
    parser.add_argument("--setup-name", default="", dest="setup_name",
                        help="Specify the test setup name. Default: ''")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    workspace_path = args.workspace_path
    repo_path = os.path.join(args.workspace_path, 'sonic-mgmt')
    ansible_path = os.path.join(repo_path, "ansible")
    counterpoll_action = args.counterpoll_action
    setup_name = args.setup_name

    topo = parse_topology(args.topo)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)

    sonic_mgmt = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                            config=Config(overrides={"run": {"echo": True}}),
                            connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})


    with sonic_mgmt.cd(ansible_path):
        logger.info(" {} counterpoll ".format(counterpoll_action))
        cmd = "PYTHONPATH=/devts:{sonic_mgmt_dir} {ngts_pytest} --setup_name={setup_name} --rootdir={" \
              "sonic_mgmt_dir}/ngts -c {sonic_mgmt_dir}/ngts/pytest.ini --log-level=INFO --clean-alluredir " \
              "--alluredir=/tmp/allure-results {sonic_mgmt_dir}/ngts/scripts/test_change_counterpoll_status.py " \
              "-k test_change_counterpoll_status[{action}]".format(ngts_pytest=constants.NGTS_PATH_PYTEST,
                                      sonic_mgmt_dir=constants.SONIC_MGMT_DIR,
                                      setup_name=setup_name,
                                      action=counterpoll_action)

        logger.info("Running CMD: {}".format(cmd))
        sonic_mgmt.run(cmd)

