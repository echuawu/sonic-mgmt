import allure
import pytest
from retry.api import retry_call
from ngts.tests.nightly.dynamic_port_breakout.conftest import set_dpb_conf, cleanup, set_ip_conf_for_ping, \
    send_ping_and_verify_results
from ngts.tests.nightly.dynamic_port_breakout.test_dpb_introp import verify_ifaces_speed_and_status


class TestDPBSpeed:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines,
              cli_objects, ports_breakout_modes,
              dut_ports_default_speeds_configuration, tested_modes_lb_conf):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = cli_objects.dut
        self.ports_breakout_modes = ports_breakout_modes
        self.dut_ports_default_speeds_configuration = dut_ports_default_speeds_configuration
        self.tested_modes_lb_conf = tested_modes_lb_conf

    @allure.title('Dynamic Port Breakout speed configuration')
    def test_speeds_on_dpb(self, cleanup_list):
        """
        Set breakout modes and Check for every speed configuration:
            Verify configuration.
            Verify the link-state.
            Verify with traffic (disabled as ping on loopback is not functional)
        :param cleanup_list: a list of functions for test cleanup
        :return: Raise warning if test fail
        """
        for breakout_mode, lb in self.tested_modes_lb_conf.items():
            with allure.step(f'Configure breakout mode {breakout_mode} on ports: {lb}'):
                breakout_ports_conf = self.configure_breakout(breakout_mode, lb, cleanup_list)
                ports_ip_conf = set_ip_conf_for_ping(self.topology_obj, cleanup_list, [lb])
                for speed_option in self.get_mutual_speeds_option(breakout_mode, lb):
                    self.configure_speed_on_breakout_ports(breakout_ports_conf, speed_option)
                    verify_ifaces_speed_and_status(self.cli_object, self.dut_engine, breakout_ports_conf)
                    send_ping_and_verify_results(self.topology_obj, self.dut_engine, cleanup_list, [lb], ports_ip_conf)
                with allure.step(f'Cleanup breakout configuration from {lb}'):
                    cleanup(cleanup_list)
                with allure.step(f'Verify interfaces {lb} are in up state after breakout is removed'):
                    retry_call(self.cli_object.interface.check_ports_status,
                               fargs=[self.dut_engine, lb],
                               tries=3, delay=10)

    def configure_breakout(self, breakout_mode, lb, cleanup_list):
        conf = {breakout_mode: lb}
        breakout_ports_conf = set_dpb_conf(self.dut_engine, self.cli_object,
                                           self.ports_breakout_modes,
                                           cleanup_list=cleanup_list,
                                           conf=conf,
                                           original_speed_conf=self.dut_ports_default_speeds_configuration)
        return breakout_ports_conf

    def configure_speed_on_breakout_ports(self, breakout_ports_conf, speed_option):
        interfaces_list = list(breakout_ports_conf.keys())
        with allure.step(f'Configure speed {speed_option} on ports: {interfaces_list}'):
            for port in interfaces_list:
                breakout_ports_conf.update({port: speed_option})
            self.cli_object.interface.set_interfaces_speed(self.dut_engine, breakout_ports_conf)

    def get_mutual_speeds_option(self, breakout_mode, ports_list):
        """
        :param ports_list: a list of ports, i.e. ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40']
        :return: a list of breakout modes supported by all the ports on the list
        """
        speeds_option_sets = []
        for port in ports_list:
            speeds_option_sets.append(set(self.ports_breakout_modes[port]['speeds_by_modes'][breakout_mode]))
        return set.intersection(*speeds_option_sets)
