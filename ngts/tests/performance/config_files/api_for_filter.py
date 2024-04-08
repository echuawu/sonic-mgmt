import errno
import sys
import colorsys
import argparse
import importlib

from python_sdk_api.sx_api import *
from threading import Thread


def auto_int(x):
    return int(x, 0)


parser = argparse.ArgumentParser(description='Port loopback')
parser.add_argument('--log_port', default=0x10001, type=auto_int, help='Logical port ID')
parser.add_argument('--mode', default=SX_LOOPBACK_FILTER_MODE_DISABLED, type=str, help='Filter Mode')
args = parser.parse_args()


def main():
    print(" ---- Init Test Flow  ---- ")
    print("[+] Open sdk")
    SWID = 0
    DEVICE_ID = 1
    rc, handle = sx_api_open(None)
    print(("sx_api_open handle:0x%x , rc %d " % (handle, rc)))
    if (rc != SX_STATUS_SUCCESS):
        print("Failed to open api handle.\nPlease check that SDK is running.")
        sys.exit(rc)

    print("[+] Set Loopback filter ")
    logport = args.log_port
    mode = args.mode
    rc = sx_api_port_loopback_filter_set(handle, logport, mode)
    if (rc != SX_STATUS_SUCCESS):
        print(("sx_api_port_loopback_filter_set failed [rc=%d]" % (rc)))
        sys.exit(rc)
    print(("sx_api_port_loopback_filter_set log_port 0x%x type %s, rc %d " % (logport, mode, rc)))


if __name__ == "__main__":
    main()
