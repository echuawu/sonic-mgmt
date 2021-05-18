#!/usr/bin/env python
'''
This file contains Python script for triggering SDK health event
'''
import sys

from python_sdk_api.sx_api import *
import argparse

######################################################
#    defines
######################################################
SWID = 0
DEVICE_ID = 1

ERR_FILE_LOCATION = '/tmp/python_err_log.txt'
parser = argparse.ArgumentParser(description='This example demonstrats how to register, \
                                              activate and handle SDK health events',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--device_id', default=1, type=lambda x: int(x, 0), help='The device id on which the health example will run')
args = parser.parse_args()

def trigger():

    print("[+] opening sdk")
    rc, handle = sx_api_open(None)
    print(("sx_api_open handle:0x%x , rc %d " % (handle, rc)))
    if (rc != SX_STATUS_SUCCESS):
        print("Failed to open api handle.\nPlease check that SDK is running.")
        return (rc)

    print("--------------- HOST IFC OPEN------------------------------")
    fd_p = new_sx_fd_t_p()
    rc = sx_api_host_ifc_open(handle, fd_p)
    if rc != SX_STATUS_SUCCESS:
        print(("sx_api_host_ifc_open failed rc %d" % rc))
        return (rc)
    fd = sx_fd_t_p_value(fd_p)
    print(("sx_api_host_ifc_open,fd = %d rc=%d] " % (fd.fd, rc)))

    # trigger a test event which will activate the handler
    sx_dbg_test_params_p = new_sx_dbg_test_params_t_p()
    sx_dbg_test_params_p.dev_id = args.device_id
    sx_dbg_test_params_p.test_type = SX_DBG_TEST_FW_FATAL_EVENT_E
    rc = sx_api_fw_dbg_test(handle, sx_dbg_test_params_p)
    if rc != SX_STATUS_SUCCESS:
        print(("sx_api_fw_dbg_test failed rc %d" % rc))
        return (rc)
    delete_sx_dbg_test_params_t_p(sx_dbg_test_params_p)

    print("[+] close host ifc recv fd")
    rc = sx_api_host_ifc_close(handle, fd_p)
    delete_sx_fd_t_p(fd_p)
    if rc != SX_STATUS_SUCCESS:
        print(("sys.exit with error, rc %d" % rc))
        return (rc)

    print("[+] close sdk")
    rc = sx_api_close(handle)
    if rc != SX_STATUS_SUCCESS:
        print(("sys.exit with error, rc %d" % rc))
        return (rc)
    return (rc)


################################################################################
#                             Main                                             #
################################################################################
if __name__ == "__main__":
    trigger()
