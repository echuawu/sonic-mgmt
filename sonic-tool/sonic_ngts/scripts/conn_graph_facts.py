#!/usr/bin/env python

import lxml.etree as ET
import yaml
import os
import logging
import traceback
import ipaddr as ipaddress
from operator import itemgetter
from itertools import groupby
from collections import defaultdict
from natsort import natsorted
from ansible.module_utils.basic import *
import sys
import time
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

LAB_GRAPHFILE_PATH = 'files/'

class Parse_Lab_Graph():
    """
    Parse the generated lab physical connection graph and insert Ansible fact of the graph
    for deploying fanout switches and dynamically configure vlan mapping to hook up EOS VMs
    and ptf docker for lab testing

    There is a creategraph.py under ansible/files to create the png and dpg like graph file for lab devices from csv file
    The  2 csv files under ansible/files are csv files to list all devices and device links for Sonic testbed
    There is a sonic_server_links.yml file to describe the connections between servers port and Sonic devices
    This module conn_graph_file also parse the server links to have a full root fanout switches template for deployment.
    """

    def __init__(self, xmlfile):
        self.root = ET.parse(xmlfile)
        self.devices = {}
        self.vlanport = {}
        self.vlanrange = {}
        self.links = {}
        self.consolelinks = {}
        self.bmclinks = {}
        self.pdulinks = {}
        self.server = defaultdict(dict)
        self.pngtag = 'PhysicalNetworkGraphDeclaration'
        self.dpgtag = 'DataPlaneGraph'
        self.pcgtag = 'PowerControlGraphDeclaration'
        self.csgtag = 'ConsoleGraphDeclaration'
        self.bmcgtag = 'BmcGraphDeclaration'

    def port_vlanlist(self, vlanrange):
        vlans = []
        for vlanid in list(map(str.strip, vlanrange.split(','))):
            if vlanid.isdigit():
                vlans.append(int(vlanid))
                continue
            elif '-' in vlanid:
                vlanlist = list(map(str.strip, vlanid.split('-')))
                vlans.extend(list(range(int(vlanlist[0]), int(vlanlist[1])+1)))
                continue
            elif vlanid != '':
                raise ValueError('vlan range error "%s"' % vlanrange)
        vlans = sorted(set(vlans))
        return vlans

    def parse_graph(self):
        """
        Parse  the xml graph file
        """
        deviceinfo = {}
        deviceroot = self.root.find(self.pngtag).find('Devices')
        devices = deviceroot.findall('Device')
        if devices is not None:
            for dev in devices:
                attributes = dev.attrib
                hostname = attributes['Hostname']
                if hostname is not None:
                    deviceinfo[hostname] = {}
                    deviceinfo[hostname]["Hostname"] = hostname
                    deviceinfo[hostname]['HwSku'] = attributes.get('HwSku')
                    deviceinfo[hostname]['Type'] = attributes.get('Type')
                    deviceinfo[hostname]['CardType'] = attributes.get('CardType', 'Linecard')
                    deviceinfo[hostname]['HwSkuType'] = attributes.get('HwSkuType', 'predefined')
                    deviceinfo[hostname]['Os'] = attributes.get('Os')
                    self.links[hostname] = {}
        devicel2info = {}
        devicel3s = self.root.find(self.dpgtag).findall('DevicesL3Info')
        devicel2s = self.root.find(self.dpgtag).findall('DevicesL2Info')
        if devicel2s is not None:
            for l2info in devicel2s:
                hostname = l2info.attrib['Hostname']
                if hostname is not None:
                    devicel2info[hostname] = {}
                    vlans = l2info.findall('InterfaceVlan')
                    for vlan in vlans:
                        portname = vlan.attrib['portname']
                        portmode = vlan.attrib['mode']
                        portvlanid = vlan.attrib['vlanids']
                        portvlanlist = self.port_vlanlist(portvlanid)
                        devicel2info[hostname][portname] = {'mode': portmode, 'vlanids': portvlanid, 'vlanlist': portvlanlist}
        if devicel3s is not None:
            for l3info in devicel3s:
                hostname = l3info.attrib['Hostname']
                if hostname is not None:
                    deviceinfo[hostname]["Hostname"] = hostname
                    management_ip = l3info.find('ManagementIPInterface').attrib['Prefix']
                    deviceinfo[hostname]['ManagementIp'] = management_ip
                    mgmtip = ipaddress.IPNetwork(management_ip)
                    deviceinfo[hostname]['mgmtip'] = str(mgmtip.ip)
                    management_gw = str(mgmtip.network+1)
                    deviceinfo[hostname]['ManagementGw'] = management_gw
        allinks = self.root.find(self.pngtag).find('DeviceInterfaceLinks').findall('DeviceInterfaceLink')
        if allinks is not None:
            for link in allinks:
                start_dev = link.attrib['StartDevice']
                end_dev = link.attrib['EndDevice']
                if start_dev:
                    self.links[start_dev][link.attrib['StartPort']] = {'peerdevice':link.attrib['EndDevice'], 'peerport': link.attrib['EndPort'], 'speed': link.attrib['BandWidth']}
                if end_dev:
                    self.links[end_dev][link.attrib['EndPort']] = {'peerdevice': link.attrib['StartDevice'], 'peerport': link.attrib['StartPort'], 'speed': link.attrib['BandWidth']}
        console_root = self.root.find(self.csgtag)
        if console_root:
            devicecsgroot = console_root.find('DevicesConsoleInfo')
            devicescsg = devicecsgroot.findall('DeviceConsoleInfo')
            if devicescsg is not None:
                for dev in devicescsg:
                    attributes = dev.attrib
                    hostname = attributes['Hostname']
                    if hostname is not None:
                        deviceinfo[hostname] = {}
                        deviceinfo[hostname]["Hostname"] = hostname
                        deviceinfo[hostname]['HwSku'] = attributes.get('HwSku')
                        deviceinfo[hostname]['Type'] = attributes.get('Type')
                        deviceinfo[hostname]['Protocol'] = attributes.get('Protocol')
                        deviceinfo[hostname]['Os'] = attributes.get('Os')
                        mgmt_ip = attributes.get('ManagementIp')
                        management_gw = str(ipaddress.IPNetwork(mgmt_ip).network+1)
                        deviceinfo[hostname]['ManagementIp'] = mgmt_ip
                        deviceinfo[hostname]['ManagementGw'] = management_gw
                        self.consolelinks[hostname] = {}
            console_link_root = console_root.find('ConsoleLinksInfo')
            if console_link_root:
                allconsolelinks = console_link_root.findall('ConsoleLinkInfo')
                if allconsolelinks is not None:
                    for consolelink in allconsolelinks:
                        attributes = consolelink.attrib
                        start_dev = attributes.get('StartDevice')
                        start_port = attributes.get('StartPort')
                        end_dev = attributes.get('EndDevice')
                        end_port = 'ConsolePort'
                        console_proxy = attributes.get('Proxy')
                        console_type = attributes.get('Console_type')
                        baud_rate = attributes.get('BaudRate')

                        if start_dev:
                            if start_dev not in self.consolelinks:
                                self.consolelinks.update({start_dev : {}})
                            self.consolelinks[start_dev][start_port] = {
                                'peerdevice': end_dev,
                                'peerport': end_port,
                                'proxy':console_proxy,
                                'type':console_type,
                                'baud_rate': baud_rate
                            }
                        if end_dev:
                            if end_dev not in self.consolelinks:
                                self.consolelinks.update({end_dev : {}})
                            self.consolelinks[end_dev][end_port] = {
                                'peerdevice': start_dev,
                                'peerport': start_port,
                                'proxy':console_proxy,
                                'type':console_type,
                                'baud_rate': baud_rate
                            }
        bmc_root = self.root.find(self.bmcgtag)
        if bmc_root:
            devicebmcgroot = bmc_root.find('DevicesBmcInfo')
            devicesbmcg = devicebmcgroot.findall('DeviceBmcInfo')
            if devicesbmcg is not None:
                for dev in devicesbmcg:
                    attributes = dev.attrib
                    hostname = attributes['Hostname']
                    if hostname is not None:
                        deviceinfo[hostname] = {}
                        deviceinfo[hostname]["Hostname"] = hostname
                        deviceinfo[hostname]['HwSku'] = attributes.get('HwSku')
                        deviceinfo[hostname]['Type'] = attributes.get('Type')
                        deviceinfo[hostname]['Protocol'] = attributes.get('Protocol')
                        deviceinfo[hostname]['Os'] = attributes.get('Os')
                        mgmt_ip = attributes.get('ManagementIp')
                        management_gw = str(ipaddress.IPNetwork(mgmt_ip).network+1)
                        deviceinfo[hostname]['ManagementIp'] = mgmt_ip
                        deviceinfo[hostname]['ManagementGw'] = management_gw
                        self.bmclinks[hostname] = {}
            bmc_link_root = bmc_root.find('BmcLinksInfo')
            if bmc_link_root:
                allbmclinks = bmc_link_root.findall('BmcLinkInfo')
                if allbmclinks is not None:
                    for bmclink in allbmclinks:
                        attributes = bmclink.attrib
                        start_dev = attributes.get('StartDevice')
                        start_port = attributes.get('StartPort')
                        end_dev = attributes.get('EndDevice')
                        end_port = attributes.get('EndPort')
                        bmc_ip = attributes.get("BmcIp")
                        if start_dev:
                            if start_dev not in self.bmclinks:
                                self.bmclinks.update({start_dev : {}})
                            self.bmclinks[start_dev][start_port] = {
                                'peerdevice': end_dev,
                                'peerport': end_port,
                                'bmc_ip': bmc_ip
                            }
                        if end_dev:
                            if end_dev not in self.bmclinks:
                                self.bmclinks.update({end_dev : {}})
                            self.bmclinks[end_dev][end_port] = {
                                'peerdevice': start_dev,
                                'peerport': start_port,
                                'bmc_ip': bmc_ip
                            }

        pdu_root = self.root.find(self.pcgtag)
        if pdu_root:
            devicepcgroot = pdu_root.find('DevicesPowerControlInfo')
            devicespcsg = devicepcgroot.findall('DevicePowerControlInfo')
            if devicespcsg is not None:
                for dev in devicespcsg:
                    hostname = dev.attrib['Hostname']
                    if hostname is not None:
                        deviceinfo[hostname] = {}
                        deviceinfo[hostname]["Hostname"] = hostname
                        hwsku = dev.attrib['HwSku']
                        devtype = dev.attrib['Type']
                        protocol = dev.attrib['Protocol']
                        mgmt_ip = dev.attrib['ManagementIp']
                        deviceinfo[hostname]['HwSku'] = hwsku
                        deviceinfo[hostname]['Type'] = devtype
                        deviceinfo[hostname]['Protocol'] = protocol
                        deviceinfo[hostname]['ManagementIp'] = mgmt_ip
                        self.pdulinks[hostname] = {}
            pdu_link_root = pdu_root.find('PowerControlLinksInfo')
            if pdu_link_root:
                allpdulinks = pdu_link_root.findall('PowerControlLinkInfo')
                if allpdulinks is not None:
                    for pdulink in allpdulinks:
                        start_dev = pdulink.attrib['StartDevice']
                        end_dev = pdulink.attrib['EndDevice']
                        logging.debug("pdulink {}".format(pdulink.attrib))
                        logging.debug("self.pdulinks {}".format(self.pdulinks))
                        if start_dev:
                            if start_dev not in self.pdulinks:
                                self.pdulinks.update({start_dev : {}})
                            self.pdulinks[start_dev][pdulink.attrib['StartPort']] = {'peerdevice':pdulink.attrib['EndDevice'], 'peerport': pdulink.attrib['EndPort']}
                        if end_dev:
                            if end_dev not in self.pdulinks:
                                self.pdulinks.update({end_dev : {}})
                            self.pdulinks[end_dev][pdulink.attrib['EndPort']] = {'peerdevice': pdulink.attrib['StartDevice'], 'peerport': pdulink.attrib['StartPort']}
        self.devices = deviceinfo
        self.vlanport = devicel2info

    def convert_list2range(self, l):
        """
        common module to convert a  list to range for easier vlan configuration generation
        """
        ranges = []
        sl = sorted(set(l))
        for _, g in groupby(enumerate(sl), lambda t: t[0] - t[1]):
            group = list(map(itemgetter(1), g))
            if len(group) == 1:
                ranges.append(str(group[0]))
            else:
                ranges.append(str(group[0])+'-'+str(group[-1]))
        return ranges

    def get_server_links(self):
        return self.server

    def get_host_vlan(self, hostname):
        """
        Calculate dpg vlan data for each link(port) and return a Switch/Device total Vlan range
        """

        if hostname in self.devices and self.devices[hostname]['Type'].lower() == 'devsonic':
            self.vlanport[hostname] = {}
            for port in self.links[hostname]:
                peerdevice = self.links[hostname][port]['peerdevice']
                if self.devices[peerdevice]["Type"].lower() == "devsonic":
                    continue
                peerport = self.links[hostname][port]['peerport']
                peerportmode = self.vlanport[peerdevice][peerport]['mode']
                peervlanids = self.vlanport[peerdevice][peerport]['vlanids']
                peervlanlist = self.vlanport[peerdevice][peerport]['vlanlist']
                self.vlanport[hostname][port] = {'mode': peerportmode, 'vlanids': peervlanids, 'vlanlist': peervlanlist}

        if hostname in self.vlanport:
            dpgvlans = self.vlanport[hostname]
            vlans = []
            for intf in dpgvlans:
                vlans += dpgvlans[intf]['vlanlist']
            self.vlanrange = self.convert_list2range(vlans)
            return {'VlanRange': self.vlanrange, 'VlanList': vlans}

    def get_host_device_info(self, hostname):
        """
        return  the given hostname device info of hwsku and type
        """
        return self.devices.get(hostname)

    def get_host_port_vlans(self, hostname):
        """
        return the given hostname device  vlan port information
        """
        return self.vlanport.get(hostname)

    def get_host_connections(self, hostname):
        """
        return the given hostname device each individual connection
        """
        return self.links.get(hostname)

    def contains_hosts(self, hostnames, part):
        if not part:
            return set(hostnames) <= set(self.devices)
        # It's possible that not all devices are found in connect_graph when using in devutil
        THRESHOLD = 0.8
        count = 0
        for hostname in hostnames:
            if hostname in self.devices.keys():
                count += 1
        return hostnames and (count * 1.0 / len(hostnames) >= THRESHOLD)

    # get the console of a device, if it exists, host is being managed by the returned device
    def get_host_console_info(self, hostname):
        """
        return  the given hostname console info of mgmtip, protocol, hwsku and type
        """
        if hostname in self.devices:
            try:
                ret = self.devices[self.consolelinks[hostname]['ConsolePort']['peerdevice']]
            except KeyError:
                ret = {}
            return ret
        else:
            """
            Please be noted that an empty dict is returned when hostname is not found
            The behavior is different with get_host_vlan. devutils script will check if the returned dict
            is empty to determine if console info exists for given hostname.
            """
            return {}

    # return the list of devices that is managed by host through console
    def get_host_console_link(self, hostname):
        """
        return  the given hostname console link info of console server and port
        """
        if hostname in self.consolelinks:
            return  self.consolelinks[hostname]
        else:
            # Please be noted that an empty dict is returned when hostname is not found
            return {}

    # get the bmc of a device, if it exists, host is being managed by the returned device
    def get_host_bmc_info(self, hostname):
        """
        return  the given hostname bmc info of mgmtip, protocol, hwsku and type
        """
        if hostname in self.devices:
            try:
                # currently we only support end port iDRAC
                ret = self.devices[self.bmclinks[hostname]['iDRAC']['peerdevice']]
            except KeyError:
                ret = {}
            return ret
        else:
            """
            Please be noted that an empty dict is returned when hostname is not found
            The behavior is different with get_host_vlan.
            """
            return {}

    # return the list of devices that is managed by host through bmc
    def get_host_bmc_link(self, hostname):
        """
        return  the given hostname bmc link info of management server and port
        """
        if hostname in self.bmclinks:
            return  self.bmclinks[hostname]
        else:
            # Please be noted that an empty dict is returned when hostname is not found
            return {}

    def get_host_pdu_info(self, hostname):
        """
        return  the given hostname pdu info of mgmtip, protocol, hwsku and type
        """
        if hostname in self.devices:
            ret = {}
            for key in ['PSU1', 'PSU2', 'PSU3', 'PSU4']:
                try:
                    ret.update({key : self.devices[self.pdulinks[hostname][key]['peerdevice']]})
                except KeyError:
                    pass
            return ret
        else:
            # Please be noted that an empty dict is returned when hostname is not found
            return {}

    def get_host_pdu_links(self, hostname):
        """
        return  the given hostname pdu links info of pdu servers and ports
        """
        if hostname in self.pdulinks:
            return  self.pdulinks[hostname]
        else:
            # Please be noted that an empty dict is returned when hostname is not found
            return {}


def build_results(lab_graph, hostnames):
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

    logs = []
    logs.append('{} Getting conn_facts'.format(time.ctime()))
    for hostname in hostnames:
        logs.append('{} Getting conn_facts for host: {}'.format(time.ctime(), hostname))
        config_db = retry_call(get_config_db_json_from_hostname, fargs=[hostname, logs], tries=5, delay=6, logger=None)
        logs.append('{} Have config_db.json, going to get ports info'.format(time.ctime()))
        all_dut_ports = get_dut_ports(config_db, logs)

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
        logs.append('{} Finished getting info for DUT: {}'.format(time.ctime(), hostname))
        device_pdu_info[hostname] = lab_graph.get_host_pdu_info(hostname)
        device_pdu_links[hostname] = lab_graph.get_host_pdu_links(hostname)
    results = {k: v for k, v in locals().items()
               if (k.startswith("device_") and v)}

    logs.append('{} Have results dict'.format(time.ctime()))
    results['logs'] = logs

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
        if m_args['filepath']:
            global LAB_GRAPHFILE_PATH
            LAB_GRAPHFILE_PATH = m_args['filepath']

        if m_args['filename']:
            filename = os.path.join(LAB_GRAPHFILE_PATH, m_args['filename'])
            lab_graph = Parse_Lab_Graph(filename)
            lab_graph.parse_graph()

        # early return for the whole graph or empty graph file(vtestbed)
        if (
                not hostnames or
                not lab_graph.devices and not lab_graph.links and not lab_graph.vlanport
        ):
            results = {
                'device_info': lab_graph.devices,
                'device_conn': lab_graph.links,
                'device_port_vlans': lab_graph.vlanport,
            }
            module.exit_json(ansible_facts=results)
        results = build_results(lab_graph, hostnames)
        module.exit_json(ansible_facts=results)
    except (IOError, OSError) as e:
        module.fail_json(msg="Can not get info about connections, error: {}, traceback: {}".format(e, traceback.format_exc()))
    except Exception as e:
        module.fail_json(msg=traceback.format_exc())


if __name__ == "__main__":
    main()
