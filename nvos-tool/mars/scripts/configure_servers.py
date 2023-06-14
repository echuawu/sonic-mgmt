#!/usr/bin/env python
import re
import sys
import os
import traceback
import logging
import time
import subprocess
from retry import retry
from fabric import Connection
from fabric import Config

REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {server_name}-ilo -U root -P 3tango11 chassis power cycle"
REBOOT_SCRIPT_PATH = '/.autodirect/mswg/utils/bin/rreboot {server_name}'

servers_to_configure = ['fit-nvos-vrt-60', 'fit-l-vrt-1140', 'arc-host84', 'fit-l-vrt-9100']

servers_to_check_functionality = {'fit-l-docker-720': {'description': 'Traffic server for NVOS_QTM_CI_1 setup',
                                                       'ip': '10.237.37.20',
                                                       'reboot_cmd': REBOOT_SCRIPT_PATH},
                                  'fit-nvos-vrt-60': {'description': 'Server for sonic-mgmt dockers',
                                                      'ip': '10.237.116.60',
                                                      'reboot_cmd': REBOOT_SCRIPT_PATH},
                                  'arc-host84': {'description': 'Server for sonic-mgmt dockers',
                                                 'ip': '10.213.86.120',
                                                       'reboot_cmd': REBOOT_SCRIPT_PATH},
                                  'fit-l-vrt-1140': {'description': 'Server for sonic-mgmt dockers',
                                                     'ip': '10.237.211.40',
                                                     'reboot_cmd': REBOOT_SCRIPT_PATH},
                                  'fit-l-vrt-7220': {'description': 'Server for ChipSim dockers',
                                                     'ip': '10.237.177.220',
                                                     'reboot_cmd': REBOOT_CMD_TO_RUN},
                                  'fit-l-vrt-660': {'description': 'Server for ChipSim dockers',
                                                    'ip': '10.237.6.60',
                                                    'reboot_cmd': REBOOT_CMD_TO_RUN},
                                  'fit-l-vrt-9100': {'description': 'Traffic server for gorilla-153/gorilla154',
                                                     'ip': '10.237.19.100',
                                                     'reboot_cmd': REBOOT_CMD_TO_RUN}
                                  }


def get_logger(name, level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s"):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(level)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = get_logger("ConfigureServers")


def run_cmd(test_server_conn, cmd):
    try:
        return test_server_conn.run(cmd)
    except BaseException as exc:
        logger.info(exc)


def configure_server(server_name, test_server_conn):
    try:
        logger.info(f"Configuring server {server_name}")

        cmd = "sudo service docker start"
        logger.info(f"Run cmd: {cmd}")
        run_cmd(test_server_conn, cmd)

        cmd = "sudo groupadd docker"
        logger.info(f"Run cmd: {cmd}")
        run_cmd(test_server_conn, cmd)

        cmd = "sudo usermod -aG docker $USER"
        logger.info(f"Run cmd: {cmd}")
        run_cmd(test_server_conn, cmd)

        cmd = "sudo chgrp docker /var/run/docker.sock"
        logger.info(f"Run cmd: {cmd}")
        run_cmd(test_server_conn, cmd)
    except BaseException as exc:
        logger.error(f"Failed to configure server {server_name}:\n {exc}")


@retry(Exception, tries=5, delay=10)
def ping_device(server_name):
    ip_add = servers_to_check_functionality[server_name]['ip']
    logger.info(f"Ping {server_name}")
    cmd = f"ping -c 3 {ip_add}"
    logger.info(f"Running cmd: {cmd}")
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    logger.info("output: " + str(output))
    logger.info("error: " + str(error))
    if " 0% packet loss" in str(output):
        logger.info("Reachable using ip address: " + ip_add)
        return True
    else:
        logger.info(f"ip address {ip_add} is unreachable")
        raise Exception(f"ip address {ip_add} is unreachable")


def is_device_up(server_name):
    try:
        return ping_device(server_name)
    except BaseException as ex:
        logger.error(str(ex))
        logger.info(f"server {server_name} is unreachable")
        return False


def reboot_server(server_name):
    logger.info(f"Reboot {server_name}")
    cmd = servers_to_check_functionality[server_name]["reboot_cmd"].format(server_name=server_name)
    logger.info("Reboot cmd: " + cmd)
    os.system(cmd)
    logger.info("Sleep for 5 min")
    time.sleep(300)


def check_directory_accessibility(server_name, test_server_conn):
    cmd = "ls /auto/sw_regression/system"
    output = run_cmd(test_server_conn, cmd)
    if "cannot access" in output:
        reboot_server(server_name)
        return is_device_up(server_name)
    return True


def verify_server_is_functional(server_name):
    if not is_device_up(server_name):
        reboot_server(server_name)
        return is_device_up(server_name)
    return True


def main():
    logger.info("Checking servers functionality")
    for server_name in servers_to_check_functionality.keys():
        try:
            logger.info(f"Checking server {server_name} functionality")
            logger.info("Server usage: " + servers_to_check_functionality[server_name]['description'])

            is_functional = verify_server_is_functional(server_name)

            if is_functional:
                user_name = os.getenv("TEST_SERVER_USER")
                password = os.getenv("TEST_SERVER_PASSWORD")

                logger.info(f"Create {server_name} connection object using username {user_name}")
                test_server_conn = Connection(servers_to_check_functionality[server_name]['ip'],
                                              user=user_name,
                                              config=Config(overrides={"run": {"echo": True}}),
                                              connect_kwargs={"password": password})

                if server_name in servers_to_configure:
                    if check_directory_accessibility(server_name, test_server_conn):
                        configure_server(server_name, test_server_conn)
        except BaseException as ex:
            logger.warning(ex)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
