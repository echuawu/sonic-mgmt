import allure
import pytest
import logging
from retry.api import retry_call
import re

from ngts.tests.nightly.dynamic_port_breakout.conftest import get_mutual_breakout_modes, \
    is_splittable, set_dpb_conf, verify_ifaces_speed_and_status
from ngts.helpers.interface_helpers import speed_string_to_int_in_mb
from ngts.tests.nightly.conftest import cleanup

logger = logging.getLogger()


class TestDPBOnAllPorts:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, interfaces,
              cli_objects, ports_breakout_modes, split_mode_supported_speeds,
              dut_ports_default_speeds_configuration, dut_ports_interconnects):
        self.topology_obj = topology_obj
        self.interfaces = interfaces
        self.dut_engine = engines.dut
        self.cli_object = cli_objects.dut
        self.ports_breakout_modes = ports_breakout_modes
        self.dut_ports_interconnects = dut_ports_interconnects
        self.split_mode_supported_speeds = split_mode_supported_speeds
        self.dut_ports_default_speeds_configuration = dut_ports_default_speeds_configuration

    @allure.title('Dynamic Port Breakout on all ports')
    def test_dpb_on_all_ports(self, cleanup_list):
        """
        This test case will set every possible breakout mode on all the ports,
        then verify that unsplittable ports were not split and splittable ports were.
        configuration was updated as expected, and check link-state.
        :return: raise assertion error if expected output is not matched
        """
        try:
            ports_list = self.get_splittable_ports_list()
            breakout_modes = get_mutual_breakout_modes(self.ports_breakout_modes, ports_list)
            max_breakout_mode = self.get_max_breakout_mode(breakout_modes)
            with allure.step(f'Configure breakout mode: {max_breakout_mode} on all splittable ports'):
                logger.info(f'Configure breakout mode: {max_breakout_mode} on all splittable ports')
                self.validate_split_all_splittable_ports(max_breakout_mode, ports_list, cleanup_list)
            with allure.step(f'Cleanup breakout configuration from all ports'):
                logger.info(f'Cleanup breakout configuration from all ports')
                cleanup(cleanup_list)
            with allure.step(f'Verify interfaces {ports_list} are in up state after breakout is removed'):
                logger.info(f'Verify interfaces {ports_list} are in up state after breakout is removed')
                retry_call(self.cli_object.interface.check_ports_status,
                           fargs=[ports_list],
                           tries=3, delay=10)
        except Exception as e:
            raise e

    def get_splittable_ports_list(self):
        """
        :return: a list of ports on dut which support split breakout mode,and aren't already split
        """
        splittable_ports = []
        for port_alias, port_name in self.topology_obj.ports.items():
            if port_alias.startswith("dut") and "splt" not in port_alias and \
                    is_splittable(self.ports_breakout_modes, port_name):
                splittable_ports.append(port_name)
        return splittable_ports

    @staticmethod
    def get_max_breakout_mode(breakout_modes):
        """
        :param breakout_modes: list of breakout modes  ['4x50G[40G,25G,10G,1G]', '2x100G[50G,40G,25G,10G,1G]']
        :return: the max breakout mode supported on dut from list of breakout modes
        """
        breakout_mode_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        breakout_modes_filtered = list(filter(lambda breakout_mode:
                                              re.search(breakout_mode_pattern,
                                                        breakout_mode), breakout_modes))
        breakout_mode_pattern_capture_breakout_number = r"(\d)x\d+G\[[\d*G,]*\]|(\d)x\d+G"
        max_breakout_mode = max(breakout_modes_filtered, key=lambda breakout_mode:
                                int(re.search(breakout_mode_pattern_capture_breakout_number,
                                              breakout_mode).group(1)))
        return max_breakout_mode

    def validate_split_all_splittable_ports(self, breakout_mode, splitable_ports_list, cleanup_list):
        """
        executing breakout on all the ports and validating the ports state after the breakout.
        :param splitable_ports_list: a list of ports, i.e. ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40']
        :param breakout_mode: i.e. '4x50G[40G,25G,10G,1G]'
        :return: none, raise exception in case validation of ports fail
        """
        breakout_ports_conf_for_all_tested_ports = {}
        splittable_ports_connected_to_hosts = self.get_splittable_ports_connected_to_hosts(splitable_ports_list)
        splittable_ports_connected_as_lb = \
            self.get_splittable_ports_connected_as_lb(splitable_ports_list, splittable_ports_connected_to_hosts)

        breakout_ports_conf_for_all_tested_ports.update(
            self.set_dpb_on_ports_connected_to_hosts(splittable_ports_connected_to_hosts, breakout_mode, cleanup_list))
        breakout_ports_conf_for_all_tested_ports.update(
            self.set_dpb_on_ports_connected_as_lb(splittable_ports_connected_as_lb, breakout_mode, cleanup_list))

        verify_ifaces_speed_and_status(self.cli_object, self.dut_engine, breakout_ports_conf_for_all_tested_ports)

    def get_splittable_ports_connected_to_hosts(self, ports_list):
        """
        :param ports_list: a list of ports that can be split,
        i.e, ['Ethernet0', 'Ethernet4', 'Ethernet8']
        :return: a subset of the ports_list which includes only the ports that connected to host,
        i.e ['Ethernet0']
        """
        ports_connected_to_hosts = [self.interfaces.dut_ha_1, self.interfaces.dut_ha_2,
                                    self.interfaces.dut_hb_1, self.interfaces.dut_hb_2]
        splittable_ports_connected_to_hosts = list(set(ports_list).intersection(ports_connected_to_hosts))
        return splittable_ports_connected_to_hosts

    def get_splittable_ports_connected_as_lb(self, splitable_ports_list, splittable_ports_connected_to_hosts):
        """
        :param splitable_ports_list: a list of ports that can be split
        :param splittable_ports_connected_to_hosts: a list of ports that can be split and are connected to host
        :return: a list of ports that are connected as loopback and both loopback ports are on the list
        """
        splittable_ports_connected_as_lb = \
            list(set(splitable_ports_list).difference(splittable_ports_connected_to_hosts))
        for port in splittable_ports_connected_as_lb:
            port_lb_neighbor = self.dut_ports_interconnects[port]
            if port_lb_neighbor not in splittable_ports_connected_as_lb:
                splittable_ports_connected_as_lb.remove(port)
        return splittable_ports_connected_as_lb

    def set_dpb_on_ports_connected_to_hosts(self, splittable_ports_connected_to_hosts, breakout_mode, cleanup_list):
        """

        :param splittable_ports_connected_to_hosts: a list of ports that connected to host and can be split
        ['Ethernet0', 'Ethernet60']
        :param breakout_mode: breakout mode to configure on them, i.e 4x50G[10G,25G]
        :param cleanup_list: a list of functions for cleanup
        :return: a dictionary with ports status after breakout
        i.e,
        {'Ethernet0': '50G', 'Ethernet60': '50G'}
        """
        breakout_ports_conf = {}

        with allure.step(f'Configure breakout mode: {breakout_mode} on '
                         f'all splittable ports connected to hosts: {splittable_ports_connected_to_hosts}'):
            for port_connected_to_host in splittable_ports_connected_to_hosts:
                breakout_ports_conf.update(
                    self.set_dpb_on_port_connected_to_host(port_connected_to_host, breakout_mode, cleanup_list))
        return breakout_ports_conf

    def set_dpb_on_ports_connected_as_lb(self, splittable_ports_connected_as_lb, breakout_mode, cleanup_list):
        """
        :param splittable_ports_connected_as_lb: a list of ports that connected as lb and can be split
        ['Ethernet4', 'Ethernet8']
        :param breakout_mode: breakout mode to configure on them, i.e 4x50G[10G,25G]
        :param cleanup_list: a list of functions for cleanup
        :return: a dictionary with ports status after breakout
        i.e,
        {'Ethernet4': '50G', 'Ethernet5': '50G', 'Ethernet6': '50G','Ethernet7': '50G', .. }
        """
        with allure.step(f'Configure breakout mode: {breakout_mode} on '
                         f'all splittable ports connected as loopback: {splittable_ports_connected_as_lb}'):
            ports_connected_as_lb_breakout_ports_conf = \
                set_dpb_conf(self.dut_engine, self.cli_object, self.ports_breakout_modes,
                             conf={breakout_mode: splittable_ports_connected_as_lb},
                             cleanup_list=cleanup_list,
                             original_speed_conf=self.dut_ports_default_speeds_configuration)
        return ports_connected_as_lb_breakout_ports_conf

    def set_dpb_on_port_connected_to_host(self, port_connected_to_host, breakout_mode, cleanup_list):
        """
        :param port_connected_to_host: i.e, Ethernet0
        :param breakout_mode: i.e 4x50G[10G,25G]
        :param cleanup_list: a list of functions for cleanup
        :return: a dictionary with port status after breakout
        i.e,
        {'Ethernet0': '50G'}
        """
        with allure.step(f'Configure breakout mode: {breakout_mode} on '
                         f'splittable port connected to hosts: {port_connected_to_host}'):
            breakout_ports_conf = set_dpb_conf(self.dut_engine, self.cli_object,
                                               self.ports_breakout_modes,
                                               conf={breakout_mode: [port_connected_to_host]},
                                               cleanup_list=cleanup_list,
                                               original_speed_conf=self.dut_ports_default_speeds_configuration)
        self.set_supported_speed_on_ports_connected_to_hosts_with_dpb(port_connected_to_host, breakout_mode,
                                                                      breakout_ports_conf)
        return {port_connected_to_host: breakout_ports_conf[port_connected_to_host]}

    def set_supported_speed_on_ports_connected_to_hosts_with_dpb(self, port_connected_to_host, breakout_mode,
                                                                 breakout_ports_conf):
        """
        :param port_connected_to_host: i.e, Ethernet0
        :param breakout_mode: i.e 4x50G[10G,25G]
        :param breakout_ports_conf: a dictionary with port status after breakout
        i.e,
        {'Ethernet0': '50G', 'Ethernet1': '50G', 'Ethernet2': '50G','Ethernet3': '50G'}
        :return: none, set speed on breakout ports to minimum speed supported on breakout ports and update the
        new speed in the breakout_ports_conf dict
        """
        breakout_port_supported_speeds = \
            self.ports_breakout_modes[port_connected_to_host]['speeds_by_modes'][breakout_mode]
        min_breakout_port_supported_speeds = min(breakout_port_supported_speeds,
                                                 key=lambda speed_as_string: speed_string_to_int_in_mb(speed_as_string))
        for breakout_port, speed_conf in breakout_ports_conf.items():
            breakout_ports_conf[breakout_port] = min_breakout_port_supported_speeds
        breakout_ports_interfaces = list(breakout_ports_conf.keys())
        with allure.step(f'set speed {min_breakout_port_supported_speeds} on ports {breakout_ports_interfaces}'):
            self.cli_object.interface.set_interfaces_speed(breakout_ports_conf)
