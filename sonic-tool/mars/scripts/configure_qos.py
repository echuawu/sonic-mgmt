# Builtin libs
import argparse
import os

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("Configure qos")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--setup-name", dest="setup_name", help="Setup name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo")
    parser.add_argument("--qos-config-action", dest="qos_config_action", help="Qos config action, reload or clear")
    return parser.parse_args()


def configure_qos(ansible_path, mgmt_docker_engine, setup_name, qos_config_action):
    """
    Method which will reload or clear qos config
    """
    logger.info("Configure qos type {}".format(qos_config_action))

    cmd = "PYTHONPATH=/devts:{sonic_mgmt_dir} {ngts_path} --setup_name={setup_name} --rootdir={sonic_mgmt_dir}/ngts " \
          "-c {sonic_mgmt_dir}/ngts/pytest.ini --log-level=INFO --clean-alluredir --alluredir=/tmp/allure-results " \
          "--disable_loganalyzer --qos_config_action={qos_config_action} {" \
          "sonic_mgmt_dir}/ngts/scripts/test_configure_qos.py".format(sonic_mgmt_dir=constants.SONIC_MGMT_DIR,
                                                                      ngts_path=constants.NGTS_PATH_PYTEST,
                                                                      setup_name=setup_name,
                                                                      qos_config_action=qos_config_action)
    with mgmt_docker_engine.cd(ansible_path):
        logger.info("Running CMD: {}".format(cmd))
        mgmt_docker_engine.run(cmd)


if __name__ == "__main__":
    args = _parse_args()
    repo_path = os.path.join(args.workspace_path, 'sonic-mgmt')
    ansible_path = os.path.join(repo_path, "ansible")
    setup_name = args.setup_name
    qos_config_action = args.qos_config_action

    topo = parse_topology(args.topo)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)
    sonic_mgmt = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                            config=Config(overrides={"run": {"echo": True}}),
                            connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})

    configure_qos(ansible_path, sonic_mgmt, setup_name, qos_config_action)