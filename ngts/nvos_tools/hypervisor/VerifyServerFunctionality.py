#!/usr/bin/python

import subprocess
import traceback
import time
import getopt
from retry import retry
import sys
sys.path.append("/root/mars/workspace/sonic-mgmt/ngts/nvos_tools/infra")
from LoggerTool import get_logger

logger = get_logger()

REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {ip}-ilo -U {username} -P {password} chassis power cycle"
REBOOT_SCRIPT_PATH = '/.autodirect/mswg/utils/bin/rreboot {server_name}'

servers_list = {'fit-nvos-vrt-60': {'description': 'Server for sonic-mgmt dockers',
                                    'ip': '10.237.116.60',
                                    'reboot_cmd': REBOOT_SCRIPT_PATH.format(server_name='fit-nvos-vrt-60')},
                'fit-l-vrt-1140': {'description': 'Server for sonic-mgmt dockers',
                                   'ip': '10.237.211.40',
                                   'reboot_cmd': REBOOT_SCRIPT_PATH.format(server_name='fit-l-vrt-1140')},
                'fit-l-vrt-7220': {'description': 'Server for ChipSim dockers',
                                   'ip': '10.237.177.220',
                                   'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-660': {'description': 'Server for ChipSim dockers',
                                  'ip': '10.237.6.60',
                                  'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-1160': {'description': 'Server for CI ChipSim dockers',
                                   'ip': '10.237.211.60',
                                   'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-9100': {'description': 'Traffic server for gorilla-153/gorilla154',
                                   'ip': '10.237.19.100',
                                   'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-nvos-220': {'description': 'Traffic server for gorilla-58',
                                 'ip': '10.237.29.220',
                                 'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-3200-201': {'description': 'Traffic server for gorilla-71',
                                       'ip': '10.237.13.201',
                                       'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-240': {'description': 'Traffic server for gorilla-100',
                                  'ip': '10.237.7.240',
                                  'reboot_cmd': REBOOT_CMD_TO_RUN},
                'fit-l-vrt-1240': {'description': 'Traffic server for gorilla-152',
                                   'ip': '10.237.11.240',
                                   'reboot_cmd': REBOOT_CMD_TO_RUN}
                }


def is_device_up(server_name):
    try:
        return ping_device(server_name)
    except BaseException as ex:
        logger.info(str(ex))
        logger.info("server {} is unreachable".format(server_name))
        return False


@retry(Exception, tries=5, delay=10)
def ping_device(server_name):
    ip_add = servers_list[server_name]['ip']
    logger.info("Ping {}".format(server_name))
    cmd = "ping -c 3 {}".format(ip_add)
    logger.info("Running cmd: {}".format(cmd))
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    logger.info("output: " + str(output))
    if " 0% packet loss" in str(output):
        logger.info("Reachable using ip address: " + ip_add)
        return True
    else:
        logger.error("ip address {} is unreachable".format(ip_add))
        raise Exception("ip address {} is unreachable".format(ip_add))


def reboot_server(server_name, user_name, password):
    logger.info("Rebooting {}".format(server_name))

    cmd = servers_list[server_name]["reboot_cmd"]
    if servers_list[server_name]["reboot_cmd"] == REBOOT_CMD_TO_RUN:
        cmd = servers_list[server_name]["reboot_cmd"].format(ip=server_name, username=user_name, password=password)

    logger.info("Reboot cmd: " + cmd)
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    logger.info("output: " + output)
    if "Cycle" in output:
        logger.info("Sleep for 7 min")
        time.sleep(420)
        return True
    else:
        logger.error("ERROR: Failed to reboot {}".format(server_name))
        return False


def verify_server_is_functional(server_name, user_name, password):
    if not is_device_up(server_name):
        if not reboot_server(server_name, user_name, password):
            return False
        return is_device_up(server_name)
    return True


def main(argv):
    user_name = ''
    password = ''
    list_of_servers = []
    try:
        opts, args = getopt.getopt(argv, "hu:p:s:")
    except getopt.GetoptError:
        logger.error('VerifyServerFunctionality.py -u <username> -p <password> -s <list_of_servers_to_check>\n'
                     '*multiple servers should be separated by ",": -s "<server1>,<server2>,..."')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            logger.error('VerifyServerFunctionality.py -u <username> -p <password> -s <list_of_servers_to_check>\n'
                         '*multiple servers should be separated by ",": -s "<server1>,<server2>,..."')
            sys.exit()
        elif opt == "-u":
            user_name = arg
        elif opt == "-p":
            password = arg
        elif opt == "-s":
            if arg == "all":
                list_of_servers = servers_list.keys()
            else:
                list_of_servers = arg.split(',')

    for server_name in list_of_servers:
        try:
            logger.info("\n\nChecking server {} functionality ({})".format(server_name,
                                                                           servers_list[server_name]['description']))

            is_functional = verify_server_is_functional(server_name, user_name, password)
            logger.info("*** Server {} is functional: {}".format(server_name, is_functional))
        except BaseException as ex:
            logger.error(ex)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
