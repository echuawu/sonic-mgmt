#!/usr/bin/env python
'''
This file contains Python command example for the ALL ROUTE DUMP module.
Python commands syntax is very similar to the Switch SDK APIs.
You can learn more about each command and its parameters by reading the SwitchX API Reference Manual.

Usage:
sx_api_router_uc_routes_dump_all.py <num of virtual routers to dump>

default virtual routers num is 12
'''
import sys
import errno
import time
import os
from python_sdk_api.sx_api import *
from test_infra_common import *
import argparse

IPV4 = 'ipv4'
IPV6 = 'ipv6'

IP_VERSIONS = [IPV4, IPV6]

ip_dict = {0: 'NONE', 1: 'IPV4', 2: 'IPV6'}
action_dict = {0: 'DROP', 1: 'TRAP', 2: 'FORWARD', 3: 'TRAP_FORWARD', 4: 'SPAN'}
type_dict = {0: 'NEXT_HOP', 1: 'LOCAL', 2: 'IP2ME'}
trap_prio_dict = {0: 'BEST_EFFORT', 1: 'LOW', 2: 'MED', 3: 'HIGH', 4: 'CRITICAL'}

ERR_FILE_LOCATION = '/tmp/python_err_log.txt'
SEC_THRESHOLD_PER_ROUTE = 0.01

file_exist = os.path.isfile(ERR_FILE_LOCATION)
sys.stderr = open(ERR_FILE_LOCATION, 'w')
if not file_exist:
    os.chmod(ERR_FILE_LOCATION, 0o777)

old_stdout = redirect_stdout()
rc, handle = sx_api_open(None)
sys.stdout = os.fdopen(old_stdout, 'w')
if (rc != SX_STATUS_SUCCESS):
    print("Failed to open api handle.\nPlease check that SDK is running.")
    sys.exit(rc)

uc_route_arr = new_sx_uc_route_get_entry_t_arr(64)
network_addr_p = new_sx_ip_prefix_t_p()
network_addr = sx_ip_prefix_t()
data_cnt_p = new_uint32_t_p()
vrid_cnt_p = new_uint32_t_p()
uint32_t_p_assign(vrid_cnt_p, 0)
vrid_key_p = new_sx_router_id_t_p()
sx_router_id_t_p_assign(vrid_key_p, 0)
vrid_key = sx_router_id_t_p_value(vrid_key_p)
rc = sx_api_router_vrid_iter_get(handle, SX_ACCESS_CMD_GET, vrid_key, None, None, vrid_cnt_p)
if rc == SX_STATUS_MODULE_UNINITIALIZED:
    print("The router module is not initialized. Dump is not available.")
    sys.exit(rc)

if rc != SX_STATUS_SUCCESS:
    print("sx_api_router_vrid_iter_get failed, rc = %d" % (rc))
    sys.exit(rc)

vrid_cnt = uint32_t_p_value(vrid_cnt_p)
vrid_list_p = new_sx_router_id_t_arr(vrid_cnt)
rc = sx_api_router_vrid_iter_get(handle, SX_ACCESS_CMD_GET_FIRST, vrid_key, None, vrid_list_p, vrid_cnt_p)
if rc != SX_STATUS_SUCCESS:
    print("sx_api_router_vrid_iter_get failed, rc = %d" % (rc))
    sys.exit(rc)
vrid_cnt = uint32_t_p_value(vrid_cnt_p)


def get_routes_count_of_vrid(vrid, version):
    routes_count = 0
    uint32_t_p_assign(data_cnt_p, 20)
    if version == SX_IP_VERSION_IPV4:
        network_addr.version = SX_IP_VERSION_IPV4
        network_addr.prefix.ipv4.addr.s_addr = 0
    else:
        network_addr.version = SX_IP_VERSION_IPV6
        for i in range(0, 15):
            uint8_t_arr_setitem(network_addr.prefix.ipv6.addr._in6_addr__in6_u._in6_addr___in6_u__u6_addr8, i, 0)

    sx_ip_prefix_t_p_assign(network_addr_p, network_addr)
    rc = sx_api_router_uc_route_get(handle, SX_ACCESS_CMD_GET_FIRST, vrid, network_addr_p, None, uc_route_arr, data_cnt_p)
    data_cnt = uint32_t_p_value(data_cnt_p)
    if rc != SX_STATUS_SUCCESS:
        # check if router module initialize
        if rc == SX_STATUS_MODULE_UNINITIALIZED:
            print("####################################")
            print("# Router is not initialized ")
            print("####################################")
            sys.exit(0)
        sys.exit(rc)

    read_number = 0
    while (data_cnt == 20):
        for i in range(0, data_cnt):
            route = sx_uc_route_get_entry_t_arr_getitem(uc_route_arr, i)
            if route.network_addr.version == version:
                routes_count += 1

        sx_ip_prefix_t_p_assign(network_addr_p, route.network_addr)
        rc = sx_api_router_uc_route_get(handle, SX_ACCESS_CMD_GETNEXT, vrid, network_addr_p, None, uc_route_arr, data_cnt_p)
        if rc != SX_STATUS_SUCCESS:
            print("An error was found in sx_api_router_uc_route_get. rc: %d" % (rc))
            sys.exit(rc)
        data_cnt = uint32_t_p_value(data_cnt_p)
        read_number = read_number + 1

    for i in range(0, data_cnt):
        route = sx_uc_route_get_entry_t_arr_getitem(uc_route_arr, i)
        if route.network_addr.version == version:
            routes_count += 1

    return routes_count


def show_routes_operation_timing(version, initial_number_of_routes, expected_number_of_routes):
    routes_operation_start_time = None
    monitor_start_time = time.time()
    routes_diff = abs(expected_number_of_routes - initial_number_of_routes)
    while ((time.time() - monitor_start_time) < routes_diff * SEC_THRESHOLD_PER_ROUTE):
        routes_count = 0
        for i in range(0, vrid_cnt):
            vrid = sx_router_id_t_arr_getitem(vrid_list_p, i)
            routes_count += get_routes_count_of_vrid(vrid, version)
        if routes_count != initial_number_of_routes and routes_operation_start_time is None:
            routes_operation_start_time = time.time()
        elif routes_count == expected_number_of_routes:
            print(f'Time to execute: {time.time() - routes_operation_start_time}')
            break


def show_routes_count(version):
    routes_count = 0
    for i in range(0, vrid_cnt):
        vrid = sx_router_id_t_arr_getitem(vrid_list_p, i)
        routes_count += get_routes_count_of_vrid(vrid, version)

    if version == SX_IP_VERSION_IPV4:
        print(f'IPv4 UC Routes {routes_count}')
    elif version == SX_IP_VERSION_IPV6:
        print(f'IPv6 UC Routes {routes_count}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ip_version', choices=IP_VERSIONS)
    parser.add_argument('--initial_number_of_routes')
    parser.add_argument('--expected_number_of_routes')
    args = parser.parse_args()
    sx_api_ip_version = SX_IP_VERSION_IPV4 if args.ip_version == IPV4 else SX_IP_VERSION_IPV6
    if args.initial_number_of_routes and args.expected_number_of_routes:
        show_routes_operation_timing(sx_api_ip_version, int(args.initial_number_of_routes),
                                     int(args.expected_number_of_routes))
    else:
        show_routes_count(sx_api_ip_version)

    sx_api_close(handle)
