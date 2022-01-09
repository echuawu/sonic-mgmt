import allure
import pytest
from retry.api import retry_call
import re

from ngts.tests.nightly.dynamic_port_breakout.conftest import get_mutual_breakout_modes, \
    is_splittable, set_dpb_conf, verify_port_speed, cleanup


class TestDPBOnAllPorts:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines,
              cli_objects, ports_breakout_modes,
              dut_ports_default_speeds_configuration):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = cli_objects.dut
        self.ports_breakout_modes = ports_breakout_modes
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
            with allure.step(f'Configure breakout mode: {max_breakout_mode} on all splittable ports: {ports_list}'):
                self.validate_split_all_splittable_ports(max_breakout_mode, ports_list, cleanup_list)
            with allure.step(f'Cleanup breakout configuration from all ports'):
                cleanup(cleanup_list)
            with allure.step(f'Verify interfaces {ports_list} are in up state after breakout is removed'):
                retry_call(self.cli_object.interface.check_ports_status,
                           fargs=[self.dut_engine, ports_list],
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

    def validate_split_all_splittable_ports(self, breakout_mode, ports_list, cleanup_list):
        """
        executing breakout on all the ports and validating the ports state after the breakout.
        :param ports_list: a list of ports, i.e. ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40']
        :param breakout_mode: i.e. '4x50G[40G,25G,10G,1G]'
        :return:
        """
        breakout_ports_conf = set_dpb_conf(self.dut_engine, self.cli_object,
                                           self.ports_breakout_modes,
                                           conf={breakout_mode: ports_list},
                                           cleanup_list=cleanup_list,
                                           original_speed_conf=self.dut_ports_default_speeds_configuration)
        verify_port_speed(self.dut_engine, self.cli_object, breakout_ports_conf)
        with allure.step(f'Verify interfaces {ports_list} are in up state'):
            retry_call(self.cli_object.interface.check_ports_status,
                       fargs=[self.dut_engine, ports_list],
                       tries=3, delay=10)
