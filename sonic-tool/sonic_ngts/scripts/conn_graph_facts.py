#!/usr/bin/env python
from ansible.module_utils.basic import *
import traceback
import os
import sys
from retry.api import retry_call

sys.path.append('{}/../ansible/library'.format(os.path.abspath(os.curdir)))
from minigraph_facts import get_config_db_json_from_hostname, get_dut_ports

'''
---
module: conn_graph_facts
author: Petro Pikh (petrop@nvidia.com)
short_description: Module(emulates) which replaces original file ansible/library/conn_graph_facts.py
description: Instead of retrieve conn_graph_facts facts for a device from lab_connection_graph.xml - this module 
    creating stub with data which are required by tests.
    As module argument we got hostname - using this hostname we find setup_name then we read config_db.json
    for specific setup and create dictionary with data(example below)

Example of data which returned by this module:
"ansible_facts": {
"device_pdu_links": {"r-tigris-22": {}}, 
"device_vlan_list": {"r-tigris-22": {}}, 
"device_vlan_range": {"r-tigris-22": {}}, 
"device_vlan_map_list": {"r-tigris-22": {}}, 
"device_console_info": {"r-tigris-22": {}}, 
"device_conn": {"r-tigris-22": {"Ethernet8": {"peerdevice": "stub_device", "speed": "100000", "peerport": "stub_port"}, 
                                "Ethernet0": {"peerdevice": "stub_device", "speed": "25000", "peerport": "stub_port"}, 
                                ......
                                "Ethernet88": {"peerdevice": "stub_device", "speed": "100000", "peerport": "stub_port"}, 
                                "Ethernet252": {"peerdevice": "stub_device", "speed": "25000", "peerport": "stub_port"}}
                                }, 
"device_info": {"r-tigris-22": {}}, 
"device_console_link": {"r-tigris-22": {}}, 
"device_pdu_info": {"r-tigris-22": {}}, 
"device_port_vlans": {"r-tigris-22": {}}
}
'''


def build_results(hostnames):
    """
    Build dictionary with data which should be returned by ansible module
    """
    device_info = {}
    device_conn = {}
    device_port_vlans = {}
    device_vlan_range = {}
    device_vlan_list = {}
    device_vlan_map_list = {}
    device_console_info = {}
    device_console_link = {}
    device_pdu_info = {}
    device_pdu_links = {}

    for hostname in hostnames:
        config_db = retry_call(get_config_db_json_from_hostname, fargs=[hostname], tries=5, delay=6, logger=None)
        all_dut_ports = get_dut_ports(config_db)

        device_info[hostname] = {}
        device_conn[hostname] = {}
        device_port_vlans[hostname] = {}
        device_vlan_range[hostname] = {}
        device_vlan_list[hostname] = {}
        device_vlan_map_list[hostname] = {}
        device_console_info[hostname] = {}
        device_console_link[hostname] = {}
        device_pdu_info[hostname] = {}
        device_pdu_links[hostname] = {}

        for port_name in all_dut_ports.keys():
            speed = config_db['PORT'][port_name]['speed']
            port_info_dict = {port_name: {'peerdevice': 'stub_device', 'speed': speed, 'peerport': 'stub_port'}}
            device_conn[hostname].update(port_info_dict)

    results = {k: v for k, v in locals().items()
               if (k.startswith("device_") and v)}

    return results


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=False),
            hosts=dict(required=False, type='list'),
            filename=dict(required=False),
            filepath=dict(required=False),
            anchor=dict(required=False, type='list'),
            ignore_errors=dict(required=False, type='bool', default=False),
        ),
        mutually_exclusive=[['host', 'hosts', 'anchor']],
        supports_check_mode=True
    )
    m_args = module.params

    if m_args['hosts']:
        hostnames = m_args['hosts']
    elif m_args['host']:
        hostnames = [m_args['host']]
    else:
        # return the whole graph
        hostnames = []

    try:
        results = build_results(hostnames)
        module.exit_json(ansible_facts=results)
    except (IOError, OSError) as e:
        module.fail_json(msg="Can not get info about connections, error: {}, traceback: {}".format(e, traceback.format_exc()))
    except Exception as e:
        module.fail_json(msg=traceback.format_exc())


if __name__ == "__main__":
    main()
