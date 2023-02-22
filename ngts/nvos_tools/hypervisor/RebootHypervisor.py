#!/usr/bin/python

import sys
import getopt
import os
import time

REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {ip} -U {username} -P {password} chassis power cycle"


def main(argv):
    ip_list = []
    user_name = ''
    password = ''
    try:
        opts, args = getopt.getopt(argv, "hi:u:p:")
    except getopt.GetoptError:
        print('RebootHypervisor.py -ip <ip_address> -u <username> -p <password>\n'
              '*multiple ip addresses should be separated by ",": -i "<ip_add1>,<ip_add2>,..."')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('RebootHypervisor.py -ip <ip_address> -u <username> -p <password>\n'
                  '*multiple ip addresses should be separated by ",": -i "<ip_add1>,<ip_add2>,..."')
            sys.exit()
        elif opt == "-i":
            ip_list = arg.split(',')
        elif opt == "-u":
            user_name = arg
        elif opt == "-p":
            password = arg

    if not ip_list or not user_name or not password:
        print('RebootHypervisor.py -ip <ip_address> -u <username> -p <password>\n'
              '*multiple ip addresses should be separated by ",": -i "<ip_add1>,<ip_add2>,..."')
        sys.exit(1)

    for ip_add in ip_list:
        print("--- Rebooting '{}'".format(ip_add))
        cmd = REBOOT_CMD_TO_RUN.format(ip=ip_add, username=user_name, password=password)
        print("cmd: {}".format(cmd))
        os.system(cmd)
        print("Sleep for 3 min")
        time.sleep(180)
        print("Reboot completed for '{}'".format(ip_add))


if __name__ == "__main__":
    main(sys.argv[1:])
