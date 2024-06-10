import errno
import sys
import colorsys
import argparse
import importlib

from python_sdk_api.sx_api import *
from threading import Thread


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

    rc = sx_api_fdb_learn_mode_set(handle, 0, SX_FDB_LEARN_MODE_DONT_LEARN)
    if (rc != SX_STATUS_SUCCESS):
        print(("sx_api_port_loopback_filter_set failed [rc=%d]" % (rc)))
        sys.exit(rc)
    print(("sx_api_fdb_learn_mode_set swid 0 lean_mode disable, rc: %d " % (rc)))


if __name__ == "__main__":
    main()
