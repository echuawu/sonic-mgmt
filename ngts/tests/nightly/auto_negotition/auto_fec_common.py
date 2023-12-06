import pytest
import logging
import allure
from retry.api import retry_call
from ngts.constants.constants import AutonegCommandConstants, SonicConst, LinuxConsts
from ngts.tests.nightly.conftest import compare_actual_and_expected
from ngts.tests.push_build_tests.L2.lldp.test_lldp import verify_lldp_neighbor_info_for_sonic_port

logger = logging.getLogger()


class TestAutoFecBase:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects, chip_type, fec_modes_speed_support,
              platform_params, dut_ports_interconnects, dut_ports_number_dict, is_simx):
        self.topology_obj = topology_obj
        self.engines = engines
        self.cli_objects = cli_objects
        self.fec_modes_speed_support = fec_modes_speed_support
        self.pci_conf = self.cli_objects.dut.chassis.get_pci_conf()
        self.dut_ports_interconnects = dut_ports_interconnects
        self.dut_ports_number_dict = dut_ports_number_dict
        self.is_simx = is_simx
        self.dut_mac = self.cli_objects.dut.mac.get_mac_address_for_interface("eth0")
        self.dut_hostname = self.cli_objects.dut.chassis.get_hostname()

    def auto_fec_checker(self, tested_lb_dict, conf, lldp_checker=True):
        """
        The function does as following:
         1) Calculate what the expected fec mode should be based on the port current speed/type
         2) Verify the fec change to the expected result

        :param tested_lb_dict:  a dictionary of loopback list for each split mode on the dut
        {1: [('Ethernet52', 'Ethernet56')],
        2: [('Ethernet12', 'Ethernet16')],
        4: [('Ethernet20', 'Ethernet24')]}
        :param conf: a dictionary of the port auto negotiation configuration and expected outcome
        :return: raise a assertion error in case validation failed
        """
        with allure.step("Auto Fec checker"):
            logger.info(f'Verify Fec mode on ports: {list(conf.keys())}')
            fec_verification_conf = self.get_fec_verification_conf(tested_lb_dict, conf)
            self.verify_fec_configuration(fec_verification_conf, lldp_checker)

    def get_fec_verification_conf(self, tested_lb_dict, conf):
        """
        Calculate what the expected fec mode should be based on the port current speed/type
        :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
        {1: [('Ethernet52', 'Ethernet56')],
        2: [('Ethernet12', 'Ethernet16')],
        4: [('Ethernet20', 'Ethernet24')]}
        :param conf: a dictionary of the port auto negotiation configuration and expected outcome
        :return: dictionary of expected fec mode for ports, i.e,
        {'Ethernet4': {'FEC Oper': 'rs'},...}
        """
        fec_verification_conf = {}
        for port, port_conf_dict in conf.items():
            expected_speed = port_conf_dict['expected_speed']
            expected_type = port_conf_dict['expected_type']
            port_split_mode = self.get_port_split_mode(tested_lb_dict, port)
            expected_fec = self.get_port_expected_fec_mode(expected_speed, expected_type, port_split_mode)
            fec_verification_conf[port] = {
                AutonegCommandConstants.FEC_OPER: expected_fec
            }
        return fec_verification_conf

    def get_port_expected_fec_mode(self, expected_speed, expected_type, port_split_mode):
        """
        Calculate what the expected fec mode should be based on the port current speed/type
        :param expected_speed: i.e, 200G
        :param expected_type: i.e, CR4
        :param port_split_mode: i.e, 1
        :return: the expected fec mode based on parameters, i.e, rs
        """
        expected_fec = None
        for fec in SonicConst.FEC_MODE_LIST:
            speed_type_dict = self.fec_modes_speed_support[fec][port_split_mode]
            type_list = speed_type_dict.get(expected_speed)
            if type_list:
                if expected_type in type_list:
                    expected_fec = fec
                    break
        assert expected_fec, f"Didn't find expected fec for speed {expected_speed}, " \
                             f"type {expected_type}, split mode {port_split_mode}"
        return expected_fec

    @staticmethod
    def get_port_split_mode(tested_lb_dict, port):
        for split_mode, lb_list in tested_lb_dict.items():
            for lb in lb_list:
                if port in lb:
                    return split_mode

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
                    retry_call(self.verify_mlxlink_fec_status_for_port, fargs=[port, port_conf_dict],
                               tries=6, delay=10, logger=logger)
                if lldp_checker:
                    retry_call(self.verify_interfaces_status_on_lldp_table, fargs=[port],
                               tries=4, delay=10, logger=logger)

    def verify_mlxlink_fec_status_for_port(self, port, port_conf_dict):
        port_number = self.dut_ports_number_dict[port]
        with allure.step('Verify FEC configuration on port: {} with mlxlink command'.format(port)):
            logger.info('Verify FEC configuration on port: {} with mlxlink command'.format(port))
            mlxlink_actual_conf = self.cli_objects.dut.interface.parse_port_mlxlink_status(self.pci_conf,
                                                                                           port_number)
            self.compare_actual_and_expected_fec_output(expected_conf=port_conf_dict, actual_conf=mlxlink_actual_conf)

    def verify_interfaces_status_cmd_output_for_port(self, port, port_conf_dict):
        with allure.step('Verify FEC configuration on port: {} with show interfaces command'.format(port)):
            logger.info('Verify FEC configuration on port: {} with show interfaces command'.format(port))
            interface_status_actual_conf = self.cli_objects.dut.interface.parse_interfaces_fec_status()[port]
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

    def configure_auto_fec(self, ports):
        for port in ports:
            self.cli_objects.dut.interface.configure_interface_fec(port, LinuxConsts.FEC_AUTO_MODE)
