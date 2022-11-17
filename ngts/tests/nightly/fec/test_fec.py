import pytest
import logging
import random
import allure
import re
from retry import retry
from retry.api import retry_call

from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.tests.nightly.conftest import reboot_reload_random, cleanup, compare_actual_and_expected, save_configuration
from ngts.constants.constants import AutonegCommandConstants, SonicConst, \
    LinuxConsts
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.tests.nightly.fec.conftest import get_tested_lb_dict_tested_ports
from ngts.helpers.interface_helpers import get_lb_mutual_speed
from ngts.tests.push_build_tests.L2.lldp.test_lldp import verify_lldp_neighbor_info_for_sonic_port


logger = logging.getLogger()


class TestFec:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, interfaces, engines, cli_objects,
              tested_lb_dict, tested_lb_dict_for_bug_2705016_flow, pci_conf,
              fec_capability_for_dut_ports, dut_ports_number_dict,
              split_mode_supported_speeds, tested_dut_to_host_conn, fec_modes_speed_support,
              dut_ports_default_speeds_configuration, dut_ports_default_mlxlink_configuration, chip_type,
              platform_params, dut_ports_interconnects, is_simx):
        self.topology_obj = topology_obj
        self.chip_type = chip_type
        self.platform_params = platform_params
        self.dut_ports_interconnects = dut_ports_interconnects
        self.interfaces = interfaces
        self.engines = engines
        self.is_simx = is_simx
        self.cli_objects = cli_objects
        self.dut_mac = self.cli_objects.dut.mac.get_mac_address_for_interface("eth0")
        self.dut_hostname = self.cli_objects.dut.chassis.get_hostname()
        self.tested_lb_dict = tested_lb_dict
        self.tested_lb_dict_for_bug_2705016_flow = tested_lb_dict_for_bug_2705016_flow
        self.tested_dut_to_host_conn = tested_dut_to_host_conn
        self.pci_conf = pci_conf
        self.fec_capability_for_dut_ports = fec_capability_for_dut_ports
        self.dut_ports_number_dict = dut_ports_number_dict
        self.split_mode_supported_speeds = split_mode_supported_speeds
        self.fec_modes_speed_support = fec_modes_speed_support
        # For Cleanup
        self.dut_ports_basic_speeds_configuration = dut_ports_default_speeds_configuration
        self.dut_ports_basic_mlxlink_configuration = dut_ports_default_mlxlink_configuration

    @pytest.mark.reboot_reload
    def test_fec_capabilities_loopback_ports(self, cleanup_list, skip_if_active_optical_cable):
        with allure.step("Configure and verify FEC with all speed options on dut loopbacks"):
            logger.info("Configure and verify FEC with all speed options on dut loopbacks")
            dut_lb_conf = self.check_all_speeds_with_fec(self.tested_lb_dict, cleanup_list)

        tested_ports = list(dut_lb_conf.keys())
        reboot_reload_random(self.topology_obj, self.engines.dut, self.cli_objects.dut,
                             tested_ports, cleanup_list, simx=self.is_simx)

        with allure.step("Verify FEC on dut loopbacks"):
            self.verify_fec_configuration(dut_lb_conf)

        with allure.step("Cleaning FEC configuration and verify port state was restored"):
            logger.info("Cleanup Configuration")
            cleanup(cleanup_list)
            self.update_conf(dut_lb_conf)

        with allure.step("Verify FEC on dut loopbacks"):
            logger.info("Verify FEC on dut loopbacks returned to default configuration")
            self.verify_fec_configuration(dut_lb_conf)

    @pytest.mark.reboot_reload
    def test_fec_capabilities_hosts_ports(self, cleanup_list, skip_if_active_optical_cable):

        with allure.step("Configure IP on dut - host connectivities for traffic validation"):
            logger.info("Configure IP on dut - host connectivities for traffic validation")
            ip_conf = self.set_peer_port_ip_conf(cleanup_list)

        with allure.step("Configure FEC on host - dut connectivities"):
            logger.info("Configure FEC on host - dut connectivities")
            self.configure_fec_mode_on_host(cleanup_list)

        with allure.step("Configure and verify FEC with all speed options on dut - host ports"):
            logger.info("Configure and verify FEC with all speed options on dut - host ports")
            dut_host_conf = self.check_all_speeds_with_fec_on_host_ports(ip_conf, cleanup_list)

        tested_ports = list(dut_host_conf.keys())
        reboot_reload_random(self.topology_obj, self.engines.dut, self.cli_objects.dut, tested_ports,
                             cleanup_list, simx=self.is_simx)

        with allure.step("Verify FEC on dut - host connectivities"):
            logger.info("Verify FEC on dut - host connectivities")
            self.verify_fec_configuration(dut_host_conf, lldp_checker=False)
            if not self.is_simx:
                logger.info("Verify FEC on host - dut connectivities")
                self.verify_fec_configuration_on_host(dut_host_conf)

        with allure.step("Verify traffic on dut - host connectivities"):
            self.validate_traffic(ip_conf)

        with allure.step("Cleaning FEC configuration and verify port state was restored"):
            logger.info("Cleanup Configuration")
            cleanup(cleanup_list)
            self.update_conf(dut_host_conf)

        with allure.step("Verify FEC on dut - host connectivities"):
            logger.info("Verify FEC on dut - host connectivities returned to default configuration")
            self.verify_fec_configuration(dut_host_conf, lldp_checker=False)
            if not self.is_simx:
                logger.info("Verify FEC on host - dut connectivities returned to default configuration")
                self.verify_fec_configuration_on_host(dut_host_conf)

    def test_negative_fec(self, cleanup_list, skip_if_active_optical_cable):
        split_mode = 1
        conf = {}
        dut_host_port = self.interfaces.dut_ha_1
        host_dut_port = self.interfaces.ha_dut_1
        port_supported_fec_modes = self.fec_capability_for_dut_ports[dut_host_port]
        mode_to_configure_on_host = random.choice(port_supported_fec_modes)
        modes_to_configure_on_dut = set(port_supported_fec_modes)
        modes_to_configure_on_dut.remove(mode_to_configure_on_host)

        self.configure_fec_mode_on_host_port(mode_to_configure_on_host,
                                             self.cli_objects.ha,
                                             self.engines.ha,
                                             self.interfaces.ha_dut_1,
                                             cleanup_list)

        for fec_mode in modes_to_configure_on_dut:
            with allure.step("Configure mismatched FEC mode: {} on dut port: {}".format(fec_mode, dut_host_port)):
                self.configure_fec_on_dut_host_port(conf, fec_mode, split_mode,
                                                    dut_host_port, host_dut_port, cleanup_list)
                conf[dut_host_port][AutonegCommandConstants.OPER] = "down"

            with allure.step("Verify link is down with mismatched FEC modes"):
                retry_call(self.verify_interfaces_status_cmd_output_for_port, fargs=[dut_host_port,
                                                                                     conf[dut_host_port]],
                           tries=3, delay=5, logger=logger)

        with allure.step("Configure matched FEC mode: {} on dut port: {}".format(mode_to_configure_on_host,
                                                                                 dut_host_port)):
            self.configure_fec_on_dut_host_port(conf, mode_to_configure_on_host,
                                                split_mode, dut_host_port, host_dut_port,
                                                cleanup_list)

        with allure.step("Verify FEC on dut - host connectivity is UP after correct FEC configuration"):
            self.verify_fec_configuration(conf, lldp_checker=False)
            retry_call(self.verify_fec_configuration_on_host_port,
                       fargs=[conf[dut_host_port], self.cli_objects.ha, self.interfaces.ha_dut_1],
                       tries=6, delay=10, logger=logger)

    def test_fec_bug_2705016(self, cli_objects, cleanup_list, skip_if_active_optical_cable):
        reboot_type = 'warm-reboot'
        tested_ports = get_tested_lb_dict_tested_ports(self.tested_lb_dict_for_bug_2705016_flow)
        ports_for_toggle_flow, ports_for_disable_enable_flow = \
            self.get_ports_for_test_flow(self.tested_lb_dict_for_bug_2705016_flow)
        logger.info("Ports to be disabled before warm-reboot and then enabled: {}"
                    .format(ports_for_disable_enable_flow))
        logger.info("Ports to be toggled after warm-reboot: {}"
                    .format(ports_for_toggle_flow))

        with allure.step("Configure FEC mode on ports: {}".format(tested_ports)):
            conf = self.configure_fec(self.tested_lb_dict_for_bug_2705016_flow,
                                      cleanup_list)

        self.verify_fec_configuration(conf)

        with allure.step("Disable ports: {}".format(ports_for_disable_enable_flow)):
            self.disable_ports(ports_for_disable_enable_flow, cleanup_list)

        with allure.step("Save configuration and warm reboot"):
            save_configuration(self.engines.dut, self.cli_objects.dut, cleanup_list)
            self.cli_objects.dut.general.safe_reboot_flow(topology_obj=self.topology_obj, reboot_type=reboot_type)
            cli_objects.dut.general.verify_dockers_are_up(SonicConst.DOCKERS_LIST)

        with allure.step("Toggle ports: {}".format(ports_for_toggle_flow)):
            self.toggle_ports(ports_for_toggle_flow, cleanup_list)

        with allure.step("Enable ports: {}".format(ports_for_disable_enable_flow)):
            self.enable_ports(ports_for_disable_enable_flow)

        with allure.step("Verify ports: {} are up".format(tested_ports)):
            cli_objects.dut.interface.check_link_state(tested_ports)

        self.verify_fec_configuration(conf)

    @staticmethod
    def get_ports_for_test_flow(tested_lb_dict_for_bug_2705016_flow):
        ports_for_toggle_flow, ports_for_disable_enable_flow = [], []
        for split_mode, fec_mode_tested_lb_dict in tested_lb_dict_for_bug_2705016_flow.items():
            for fec_mode, lb_list in fec_mode_tested_lb_dict.items():
                if len(lb_list) == 1:
                    random_list = random.choice([ports_for_toggle_flow, ports_for_disable_enable_flow])
                    random_list += lb_list[0]
                else:
                    ports_for_toggle_flow += lb_list[0]
                    ports_for_disable_enable_flow += lb_list[1]
        return ports_for_toggle_flow, ports_for_disable_enable_flow

    def toggle_ports(self, ports, cleanup_list):
        logger.info("Toggle ports: {}".format(ports))
        for port in ports:
            self.toggle_port(port, cleanup_list)

    def disable_ports(self, ports, cleanup_list):
        logger.info("Disable ports: {}".format(ports))
        for port in ports:
            cleanup_list.append((self.cli_objects.dut.interface.enable_interface, (port,)))
            self.cli_objects.dut.interface.disable_interface(port,)

    def enable_ports(self, ports):
        logger.info("Enable ports: {}".format(ports))
        for port in ports:
            self.cli_objects.dut.interface.enable_interface(port)

    def toggle_port(self, port, cleanup_list):
        logger.info("Toggle port: {}".format(port))
        cleanup_list.append((self.cli_objects.dut.interface.enable_interface, (port,)))
        self.cli_objects.dut.interface.disable_interface(port)
        self.cli_objects.dut.interface.enable_interface(port)

    def set_peer_port_ip_conf(self, cleanup_list):
        """
        set ips on the dut and host ports
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: None
        """
        ip_conf = {}
        ip_template = '{ip_prefix}.{ip_prefix}.{ip_prefix}.{ip_index}'
        ip_index = 1
        ip_prefix = 20
        for fec_mode, tested_dut_host_conn_dict in self.tested_dut_to_host_conn.items():
            ip_config_dict = dict()
            dst_ip = ip_template.format(ip_prefix=ip_prefix, ip_index=ip_index)
            ip_config_dict['dut'] = [{'iface': tested_dut_host_conn_dict["dut_port"],
                                      'ips': [(dst_ip, '24')]}]
            ip_index += 1
            ip_config_dict[tested_dut_host_conn_dict['host']] = [{'iface': tested_dut_host_conn_dict["host_port"],
                                                                  'ips': [(ip_template.format(ip_prefix=ip_prefix,
                                                                                              ip_index=ip_index),
                                                                           '24')]}]
            ip_index += 1
            ip_prefix += 10
            ip_conf[tested_dut_host_conn_dict["dut_port"]] = {
                "sender": tested_dut_host_conn_dict['host'],
                "src": tested_dut_host_conn_dict["host_port"],
                "dst": tested_dut_host_conn_dict["dut_port"],
                "dst_ip": dst_ip
            }
            cleanup_list.append((IpConfigTemplate.cleanup, (self.topology_obj, ip_config_dict,)))
            IpConfigTemplate.configuration(self.topology_obj, ip_config_dict)
        return ip_conf

    def configure_fec(self, tested_lb_dict, cleanup_list):
        conf = {}
        for split_mode, fec_mode_tested_lb_dict in tested_lb_dict.items():
            for fec_mode, lb_list in fec_mode_tested_lb_dict.items():
                for lb in lb_list:
                    speed = self.get_lb_speed_conf_for_fec_mode(lb, split_mode, fec_mode, self.fec_modes_speed_support)
                    interface_type = random.choice(self.fec_modes_speed_support[fec_mode][split_mode][speed])
                    for port in lb:
                        self.update_port_fec_conf_dict(conf, port, speed, fec_mode, interface_type, cleanup_list)
        return conf

    def check_all_speeds_with_fec(self, tested_lb_dict, cleanup_list):
        conf = {}
        for split_mode, fec_mode_tested_lb_dict in tested_lb_dict.items():
            for fec_mode, lb_list in fec_mode_tested_lb_dict.items():
                dut_lb_conf = {}
                lb = lb_list.pop()
                speed_options = self.get_lb_speeds_option_for_fec_mode(lb, split_mode,
                                                                       fec_mode, self.fec_modes_speed_support)
                random.shuffle(speed_options)
                for speed in speed_options:
                    with allure.step(f"Configure FEC mode: {fec_mode} with speed: {speed} on loopback: {lb}"):
                        self.configure_fec_speed_on_ports(dut_lb_conf, lb, split_mode, speed, fec_mode, cleanup_list)
                    with allure.step(f"Verify FEC mode: {fec_mode} with speed: {speed} on loopback: {lb}"):
                        self.verify_fec_configuration(dut_lb_conf)
                conf.update(dut_lb_conf)
                self.set_cleanup_of_latest_config(lb, cleanup_list)
        return conf

    def configure_fec_speed_on_ports(self, dut_lb_conf, ports, split_mode, speed, fec_mode, cleanup_list):
        interface_type = random.choice(self.fec_modes_speed_support[fec_mode][split_mode][speed])
        for port in ports:
            self.update_port_fec_conf_dict(dut_lb_conf, port, speed,
                                           fec_mode, interface_type,
                                           cleanup_list, set_cleanup=False)

    def set_cleanup_of_latest_config(self, lb, cleanup_list):
        for port in lb:
            self.set_speed_fec_cleanup(port, cleanup_list)

    def get_lb_speed_conf_for_fec_mode(self, lb, split_mode, fec_mode, fec_modes_speed_support):
        mutual_speeds_option = self.get_lb_speeds_option_for_fec_mode(lb, split_mode, fec_mode, fec_modes_speed_support)
        speed = random.choice(mutual_speeds_option)
        return speed

    def get_lb_speeds_option_for_fec_mode(self, lb, split_mode, fec_mode, fec_modes_speed_support):
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
        fec_mode_supported_speeds = set(fec_modes_speed_support[fec_mode][split_mode].keys())
        mutual_speeds_option = list(fec_mode_supported_speeds.intersection(lb_mutual_speeds))
        return mutual_speeds_option

    def configure_fec_on_dut_host_ports(self, cleanup_list):
        conf = {}
        split_mode = 1
        for fec_mode, tested_dut_host_conn_dict in self.tested_dut_to_host_conn.items():
            dut_host_port = tested_dut_host_conn_dict["dut_port"]
            host_dut_port = tested_dut_host_conn_dict["host_port"]
            self.configure_fec_on_dut_host_port(conf, fec_mode, split_mode, dut_host_port, host_dut_port, cleanup_list)
        return conf

    def check_all_speeds_with_fec_on_host_ports(self, ip_conf, cleanup_list):
        conf = {}
        split_mode = 1
        for fec_mode, tested_dut_host_conn_dict in self.tested_dut_to_host_conn.items():
            dut_host_port = tested_dut_host_conn_dict["dut_port"]
            host_dut_port = tested_dut_host_conn_dict["host_port"]
            dut_host_conf = {}
            speed_options = self.get_dut_host_port_speeds_option_for_fec_mode(fec_mode, split_mode,
                                                                              dut_host_port, host_dut_port)
            random.shuffle(speed_options)
            for speed in speed_options:
                self.configure_and_verify_fec_speed_on_hosts_ports(tested_dut_host_conn_dict, dut_host_conf, ip_conf,
                                                                   split_mode, speed, fec_mode, cleanup_list)
            self.set_cleanup_of_latest_config([dut_host_port], cleanup_list)
            conf.update(dut_host_conf)
        return conf

    def configure_and_verify_fec_speed_on_hosts_ports(self, tested_dut_host_conn_dict, dut_host_conf, ip_conf,
                                                      split_mode, speed, fec_mode, cleanup_list):
        dut_host_port = tested_dut_host_conn_dict["dut_port"]
        host_dut_port = tested_dut_host_conn_dict["host_port"]
        cli_object = tested_dut_host_conn_dict["cli"]
        engine = tested_dut_host_conn_dict["engine"]
        with allure.step(f"Configure FEC mode: {fec_mode} with speed: {speed} on dut host port: {dut_host_port}"):
            logger.info(f"Configure FEC mode: {fec_mode} with speed: {speed} on dut host port: {dut_host_port}")
            self.configure_fec_speed_on_ports(dut_host_conf, [dut_host_port], split_mode, speed, fec_mode, cleanup_list)
        with allure.step(f"Verify FEC mode: {fec_mode} with speed: {speed} on dut host port: {dut_host_port}"):
            logger.info(f"Verify FEC mode: {fec_mode} with speed: {speed} on dut host port: {dut_host_port}")
            self.verify_fec_configuration(dut_host_conf, lldp_checker=False)
        if not self.is_simx:
            with allure.step(f"Verify FEC mode: {fec_mode} with speed: {speed} on host dut port: {host_dut_port}"):
                logger.info(f"Verify FEC mode: {fec_mode} with speed: {speed} on host dut port: {host_dut_port}")
                self.verify_fec_configuration_on_host_port(dut_host_conf[dut_host_port], cli_object, host_dut_port)
        with allure.step("Verify traffic on dut - host connectivity"):
            traffic_validation = ip_conf[dut_host_port]
            retry_call(
                self.validate_traffic_on_dut_host_ports,
                fargs=[traffic_validation],
                tries=3,
                delay=5,
                logger=logger,
            )

    def get_dut_host_port_speeds_option_for_fec_mode(self, fec_mode, split_mode, dut_host_port, host_dut_port):
        fec_mode_supported_speeds = set(self.fec_modes_speed_support[fec_mode][split_mode].keys())
        ports_supported_speeds = get_lb_mutual_speed([dut_host_port, host_dut_port], split_mode,
                                                     self.split_mode_supported_speeds)
        if self.is_simx:
            ports_supported_speeds = list(self.split_mode_supported_speeds[dut_host_port][split_mode])
        mutual_speeds_option = list(fec_mode_supported_speeds.intersection(ports_supported_speeds))
        return mutual_speeds_option

    def configure_fec_on_dut_host_port(self, conf, fec_mode, split_mode, dut_host_port, host_dut_port, cleanup_list):
        mutual_speeds_option = self.get_dut_host_port_speeds_option_for_fec_mode(fec_mode, split_mode,
                                                                                 dut_host_port, host_dut_port)
        speed = random.choice(mutual_speeds_option)
        interface_type = random.choice(self.fec_modes_speed_support[fec_mode][split_mode][speed])
        self.update_port_fec_conf_dict(conf, dut_host_port, speed, fec_mode, interface_type, cleanup_list)

    def configure_fec_mode_on_host(self, cleanup_list):
        for fec_mode, tested_dut_host_conn_dict in self.tested_dut_to_host_conn.items():
            self.configure_fec_mode_on_host_port(fec_mode,
                                                 cli_object=tested_dut_host_conn_dict["cli"],
                                                 engine=tested_dut_host_conn_dict["engine"],
                                                 interface=tested_dut_host_conn_dict["host_port"],
                                                 cleanup_list=cleanup_list)

    @staticmethod
    def configure_fec_mode_on_host_port(fec_mode, cli_object, engine, interface, cleanup_list):
        logger.info("Configure FEC mode: {} on host port: {} on host: {}".format(fec_mode,
                                                                                 interface,
                                                                                 engine.ip))
        with allure.step("Configure FEC mode: {} on host port: {} on host: {}".format(fec_mode,
                                                                                      interface,
                                                                                      engine.ip)):
            cleanup_list.append((cli_object.interface.configure_interface_fec, (interface,
                                                                                LinuxConsts.FEC_AUTO_MODE)))
            cli_object.interface.configure_interface_fec(interface, fec_option=fec_mode)

    def verify_fec_configuration_on_host(self, conf):
        for fec_mode, tested_dut_host_conn_dict in self.tested_dut_to_host_conn.items():
            cli_object = tested_dut_host_conn_dict["cli"]
            engine = tested_dut_host_conn_dict["engine"]
            interface = tested_dut_host_conn_dict["host_port"]
            dut_port = tested_dut_host_conn_dict["dut_port"]
            expected_conf = conf[dut_port]
            self.verify_fec_configuration_on_host_port(expected_conf, cli_object, interface)

    @retry(Exception, tries=6, delay=10)
    def verify_fec_configuration_on_host_port(self, expected_conf, cli_object, interface):
        actual_speed = cli_object.interface.parse_show_interface_ethtool_status(interface)["speed"]
        actual_fec_mode = cli_object.interface.parse_interface_fec(interface)[LinuxConsts.ACTIVE_FEC]
        actual_host_port_conf = {
            AutonegCommandConstants.SPEED: actual_speed,
            AutonegCommandConstants.FEC: actual_fec_mode
        }
        self.compare_actual_and_expected_fec_output(expected_conf=expected_conf, actual_conf=actual_host_port_conf)

    def validate_traffic(self, ip_conf):
        """
        send ping between dut and host and validate the results
        :param ip_conf: ip_conf
        :return: raise assertion errors in case of validation errors
        """
        for dut_host_port, traffic_validation in ip_conf.items():
            self.validate_traffic_on_dut_host_ports(traffic_validation)

    def validate_traffic_on_dut_host_ports(self, traffic_validation):
        with allure.step('send ping from {} to {}'.format(traffic_validation["src"],
                                                          traffic_validation["dst"])):
            validation = {'sender': traffic_validation["sender"],
                          'args': {'interface': traffic_validation["src"],
                                   'count': 3,
                                   'dst': traffic_validation["dst_ip"]}}
            ping = PingChecker(self.topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from {} to {}'.format(traffic_validation["src"],
                                                                          traffic_validation["dst"]))
            ping.run_validation()

    def update_port_fec_conf_dict(self, conf, port, speed, tested_fec_mode,
                                  interface_type, cleanup_list, set_cleanup=True):
        if set_cleanup:
            self.set_speed_fec_cleanup(port, cleanup_list)
        self.cli_objects.dut.interface.config_interface_type(port, 'none')
        self.cli_objects.dut.interface.set_interface_speed(port, speed)
        self.cli_objects.dut.interface.config_interface_type(port, interface_type)
        self.cli_objects.dut.interface.configure_interface_fec(port, tested_fec_mode)
        conf[port] = {AutonegCommandConstants.SPEED: speed,
                      AutonegCommandConstants.FEC: tested_fec_mode,
                      AutonegCommandConstants.WIDTH: self.get_interface_width(interface_type),
                      AutonegCommandConstants.ADMIN: 'up',
                      AutonegCommandConstants.OPER: 'up'
                      }

    @staticmethod
    def get_interface_width(interface_type):
        """
        :param interface_type: a interface type string 'CR'
        :return: int width  value, i.e, '1'
        more examples,
        'CR' -> 1
        'CR2' -> 2
        'CR4' -> 4
        """
        match = re.search(r"\w+(\d+)", interface_type)
        if match:
            width = match.group(1)
            return int(width)
        else:
            return 1

    def set_speed_fec_cleanup(self, port, cleanup_list):
        base_speed = self.dut_ports_basic_speeds_configuration[port]
        base_fec = self.dut_ports_basic_mlxlink_configuration[port][AutonegCommandConstants.FEC]
        base_interface_type = self.dut_ports_basic_mlxlink_configuration[port][AutonegCommandConstants.TYPE]
        cleanup_list.append((self.cli_objects.dut.interface.config_interface_type, (port,
                                                                                    'none')))
        cleanup_list.append((self.cli_objects.dut.interface.set_interface_speed, (port, base_speed)))
        cleanup_list.append((self.cli_objects.dut.interface.config_interface_type, (port,
                                                                                    base_interface_type)))
        cleanup_list.append((self.cli_objects.dut.interface.configure_interface_fec, (port, base_fec)))

    def update_conf(self, conf):
        for port, port_conf in conf.items():
            base_speed = self.dut_ports_basic_speeds_configuration[port]
            base_fec = self.dut_ports_basic_mlxlink_configuration[port][AutonegCommandConstants.FEC]
            base_width = \
                self.get_interface_width(self.dut_ports_basic_mlxlink_configuration[port][AutonegCommandConstants.TYPE])
            conf[port][AutonegCommandConstants.SPEED] = base_speed
            conf[port][AutonegCommandConstants.FEC] = base_fec
            conf[port][AutonegCommandConstants.WIDTH] = base_width

    def verify_fec_configuration(self, conf, lldp_checker=True):
        """
        :param conf: a dictionary of the port auto negotiation configuration and expected outcome
        :param lldp_checker: True if the fec validation should check lldp info for port,
        False when fec validation is done on dut-host ports
        :return: raise Assertion error in case the configuration doesn't match the actual state on the switch
        """
        with allure.step('Verify FEC configuration on ports: {}'.format(list(conf.keys()))):
            for port, port_conf_dict in conf.items():
                retry_call(self.verify_interfaces_status_cmd_output_for_port, fargs=[port, port_conf_dict],
                           tries=20, delay=10, logger=logger)
                if not self.is_simx:
                    retry_call(self.verify_mlxlink_status_cmd_output_for_port, fargs=[port, port_conf_dict],
                               tries=6, delay=10, logger=logger)
                if lldp_checker:
                    retry_call(self.verify_interfaces_status_on_lldp_table, fargs=[port],
                               tries=4, delay=10, logger=logger)

    def verify_mlxlink_status_cmd_output_for_port(self, port, port_conf_dict):
        port_number = self.dut_ports_number_dict[port]
        with allure.step('Verify FEC configuration on port: {} with mlxlink command'.format(port)):
            logger.info('Verify FEC configuration on port: {} with mlxlink command'.format(port))
            mlxlink_actual_conf = self.cli_objects.dut.interface.parse_port_mlxlink_status(self.pci_conf,
                                                                                           port_number)
            self.compare_actual_and_expected_fec_output(expected_conf=port_conf_dict, actual_conf=mlxlink_actual_conf)

    def verify_interfaces_status_cmd_output_for_port(self, port, port_conf_dict):
        with allure.step('Verify FEC configuration on port: {} with show interfaces command'.format(port)):
            logger.info('Verify FEC configuration on port: {} with show interfaces command'.format(port))
            interface_status_actual_conf = self.cli_objects.dut.interface.parse_interfaces_status()[port]
            self.compare_actual_and_expected_fec_output(expected_conf=port_conf_dict,
                                                        actual_conf=interface_status_actual_conf)

    def verify_interfaces_status_on_lldp_table(self, port):
        with allure.step(f'Verify LLDP neighbor info on port: {port} with show lldp neighbor command'):
            logger.info(f'Verify LLDP neighbor info on port: {port} with show lldp neighbor command')
            lldp_info = self.cli_objects.dut.lldp.parse_lldp_info_for_specific_interface(port)
            port_neighbor = self.dut_ports_interconnects[port]
            verify_lldp_neighbor_info_for_sonic_port(port, lldp_info, self.dut_hostname, self.dut_mac, port_neighbor)

    @staticmethod
    def compare_actual_and_expected_fec_output(expected_conf, actual_conf):
        """
        :param expected_conf:
        :param actual_conf:
        :return: raise assertion error in case expected and actual configuration don't match
        """
        with allure.step('Compare expected and actual fec configuration'):
            logger.debug("expected: {}".format(expected_conf))
            logger.debug("actual: {}".format(actual_conf))
            for key, value in expected_conf.items():
                if key in actual_conf.keys():
                    actual_conf_value = actual_conf[key]
                    compare_actual_and_expected(key, value, actual_conf_value)
