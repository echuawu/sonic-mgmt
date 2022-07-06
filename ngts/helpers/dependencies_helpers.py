import allure
import random
import pytest
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.constants.constants import IpIfaceAddrConst


class DependenciesBase:
    """
    This class can be used to configure a set of features on
    a list of ports in order to test some other feature capability.

    currently the class supports the following dependencies:
    * port channel
    * vlan
    * ip

    The assumption is that the setup init state has no dependencies configured.
    See the class usage on sonic-mgmt/ngts/tests/nightly/dynamic_port_breakout/test_dpb_introp.py
    """
    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = cli_objects.dut

    def set_dependencies(self, dependency_list, ports_list, cleanup_list):
        """
        configure the dependencies list on provided ports list
        :param dependency_list: a list of features i.e. ['vlan', 'portchannel']
        :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
        :return:  a dictionary with the ports configured dependencies information
        for example,
        {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
        'Ethernet216': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0002'},...}

        """
        conf = {"vlan": self.set_vlan_dependency,
                "portchannel": self.set_port_channel_dependency,
                "ip": self.set_ip_dependency
                }
        ports_dependencies = {port: {} for port in ports_list}
        for dependency in dependency_list:
            conf[dependency](self.topology_obj, ports_list, ports_dependencies, cleanup_list, dependency_list)
        return ports_dependencies

    @staticmethod
    def set_vlan_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list, dependency_list):
        """
        configure vlan dependency on all the ports in ports_list and update the configuration
        in the dictionary ports_dependencies.
        :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
        :param ports_dependencies: a dictionary with the ports configured dependencies information
        for example,
        {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
        :return: None
        """
        vlan_num = random.choice(range(2, 4094 - len(ports_list)))
        vlan_mode = random.choice(['access', 'trunk'])
        vlan_conf = []
        for port in ports_list:
            vlan_members = []
            vlan_member = port
            if 'portchannel' in dependency_list:
                vlan_member = ports_dependencies[port]["portchannel"]
            vlan_members.append({vlan_member: vlan_mode})
            vlan_conf.append({'vlan_id': vlan_num, 'vlan_members': vlan_members})
            ports_dependencies[port].update({'vlan': f'Vlan{vlan_num}'})
            vlan_num = vlan_num + 1
        vlan_config_dict = {'dut': vlan_conf}
        VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
        cleanup_list.append((VlanConfigTemplate.cleanup, (topology_obj, vlan_config_dict,)))

    @staticmethod
    def set_port_channel_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list, dependency_list):
        """
        configure port-channel dependency on all the ports in ports_list and update the configuration
        in the dictionary ports_dependencies.
        :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
        :param ports_dependencies: a dictionary with the ports configured dependencies information
        for example,
        {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
        :return: None
        """
        lag_lacp_config_dict = {'dut': []}
        for index, port in enumerate(ports_list):
            pc_idx = str(index + 1).zfill(4)
            port_channel_name = f'PortChannel{pc_idx}'
            lag_lacp_config_dict['dut'].append({'type': 'lacp',
                                                'name': port_channel_name,
                                                'members': [port]})
            ports_dependencies[port].update({"portchannel": port_channel_name})
        LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
        cleanup_list.append((LagLacpConfigTemplate.cleanup, (topology_obj, lag_lacp_config_dict,)))

    @staticmethod
    def set_ip_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list, dependency_list=[]):
        """
        configure ip dependency on all the ports in ports_list and update the configuration
        in the dictionary ports_dependencies.
        :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
        :param ports_dependencies: a dictionary with the ports configured dependencies information
        for example,
        {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1},
        :return: None
        """
        ip_config_dict = {'dut': []}
        idx = 1
        for port in ports_list:
            ip_member = port
            if 'vlan' in dependency_list:
                ip_member = ports_dependencies[port]['vlan']
                vlan_config_dict = {'dut': [{'vlan_id': ip_member, 'vlan_members': []}]}
                cleanup_list.append((VlanConfigTemplate.cleanup, (topology_obj, vlan_config_dict,)))
            elif 'portchannel' in dependency_list:
                ip_member = ports_dependencies[port]['portchannel']
                lag_lacp_config_dict = {'dut': [{'type': 'lacp',
                                                 'name': ip_member,
                                                 'members': [port]}]}
                cleanup_list.append((LagLacpConfigTemplate.cleanup, (topology_obj, lag_lacp_config_dict,)))
            ip = rf'{idx}0.0.0.{idx}'
            ip_config_dict['dut'].append({'iface': ip_member, 'ips': [(ip, IpIfaceAddrConst.IPV4_MASK_24)]})
            ports_dependencies[port].update({'ip': ip})
            idx += 1
        IpConfigTemplate.configuration(topology_obj, ip_config_dict)
        cleanup_list.append((IpConfigTemplate.cleanup, (topology_obj, ip_config_dict,)))

    def verify_no_dependencies_on_ports(self, dependency_list, ports_dependencies):
        """
        verify all dependencies were removed from ports after breakout
        :param dependency_list:  a list of features i.e. ['vlan', 'portchannel']
        :param ports_dependencies:  a dictionary with the ports configured dependencies information
        for example,
        {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
        'Ethernet216': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0002'},...}
        :return: raise assertion error in case dependency was not removed
        """
        conf = {"vlan": self.verify_no_vlan_on_ports,
                "portchannel": self.verify_no_port_channel_on_ports,
                "ip": self.verify_no_ip_on_ports
                }
        for dependency in dependency_list:
            conf[dependency](ports_dependencies)

    def verify_no_vlan_on_ports(self, ports_dependencies):
        """
        :param ports_dependencies: a dictionary with the ports configured dependencies information
         i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
        :return: raise assertion error in case dependency still exist on port
        """
        ports_w_dependencies_list = list(ports_dependencies.keys())
        with allure.step(f'verify no vlan configuration on ports: {ports_w_dependencies_list}'):
            vlan_expected_info = []
            show_vlan_config_pattern = r"Vlan{vid}\s+{vid}\s+{member}"
            for port, port_dependency in ports_dependencies.items():
                vlan_id = port_dependency["vlan"]
                vlan_expected_info.append((show_vlan_config_pattern.format(vid=vlan_id, member=port), False))
            vlan_info = self.cli_object.vlan.show_vlan_config()
            verify_show_cmd(vlan_info, vlan_expected_info)

    def verify_no_port_channel_on_ports(self, ports_dependencies):
        """
        :param ports_dependencies: a dictionary with the ports configured dependencies information
         i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
        :return: raise assertion error in case dependency still exist on port
        """
        ports_w_dependencies_list = list(ports_dependencies.keys())
        with allure.step(f'verify no port channel configuration on ports: {ports_w_dependencies_list}'):
            port_channel_expected_info = []
            show_port_channel_config_pattern = r"{PORTCHANNEL}.*{PORT}"
            for port, port_dependency in ports_dependencies.items():
                port_channel_name = port_dependency["portchannel"]
                port_channel_expected_info.append((show_port_channel_config_pattern.
                                                   format(PORTCHANNEL=port_channel_name, PORT=port), False))
            port_channel_info = self.cli_object.lag.show_interfaces_port_channel()
            verify_show_cmd(port_channel_info, port_channel_expected_info)

    def verify_no_ip_on_ports(self, ports_dependencies):
        """
        :param ports_dependencies: a dictionary with the ports configured dependencies information
         i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
        :return: raise assertion error in case dependency still exist on port
        """
        ports_w_dependencies_list = list(ports_dependencies.keys())
        with allure.step(f'verify no ip configuration on ports: {ports_w_dependencies_list}'):
            ip_expected_info = []
            show_ip_config_pattern = r"{port}/s+{ip}"
            for port, port_dependency in ports_dependencies.items():
                ip = port_dependency["ip"]
                ip_expected_info.append((show_ip_config_pattern.format(port=port, ip=ip), False))
            ip_info = self.cli_object.ip.show_ip_interfaces()
            verify_show_cmd(ip_info, ip_expected_info)
