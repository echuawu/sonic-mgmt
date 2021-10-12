import logging
import allure
import random
import pytest
from retry.api import retry_call

from ngts.config_templates.ip_config_template import IpConfigTemplate
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.tests.nightly.auto_negotition.conftest import get_speeds_in_Gb_str_format, get_interface_cable_width, \
    get_matched_types, speed_string_to_int_in_mb, convert_speeds_to_mb_format
from ngts.constants.constants import AutonegCommandConstants
from ngts.helpers.interface_helpers import get_alias_number, get_lb_mutual_speed
from ngts.tests.nightly.conftest import compare_actual_and_expected

logger = logging.getLogger()


class AutoNegBase:

    def generate_subset_conf(self, tested_lb_dict):
        """
        :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
        breakout options on all setup ports (including host ports)
        and split mode including host ports i.e, {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...}
        :return: a dictionary of the port auto negotiation custom configuration and expected outcome
        {'Ethernet4': {'Auto-Neg Mode': 'disabled',
                       'Speed': '10G',
                       'Adv Speeds':
                       '100000,10000',
                       'Type': 'CR',
                       'Width': 1,
                       'Adv Types': 'CR,CR4',
                       'expected_speed': '100G',
                       'expected_type': 'CR4',
                       'expected_width': 4},
        'Ethernet8': {'Auto-Neg Mode': 'disabled',
                      'Speed': '10G',
                      'Adv Speeds': '50000,100000,10000',
                      'Type': 'CR',
                      'Width': 1,
                      'Adv Types':
                      'CR,CR2,CR4',
                      'expected_speed': '100G',
                      'expected_type': 'CR4',
                      'expected_width': 4}, ...
        }
        """
        with allure.step('creating custom configuration'):
            conf = dict()
            for split_mode, lb_list in tested_lb_dict.items():
                for lb in lb_list:
                    lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
                    mutual_speed_in_subset = min(lb_mutual_speeds, key=speed_string_to_int_in_mb)
                    all_adv_speeds = []
                    all_adv_types = []
                    for port in lb:
                        adv_speeds = set(random.choices(lb_mutual_speeds,
                                                        k=random.choice(range(1, len(lb_mutual_speeds) + 1))))
                        if mutual_speed_in_subset not in adv_speeds:
                            adv_speeds.add(mutual_speed_in_subset)
                        adv_types = get_matched_types(self.ports_lanes_dict[port], adv_speeds,
                                                      self.interfaces_types_dict)
                        all_adv_speeds.append(adv_speeds)
                        all_adv_types.append(adv_types)
                        speed = mutual_speed_in_subset
                        adv_speeds = convert_speeds_to_mb_format(adv_speeds)
                        interface_type = get_matched_types(self.ports_lanes_dict[port], [speed],
                                                           self.interfaces_types_dict).pop()
                        cable_type = interface_type
                        width = get_interface_cable_width(interface_type)
                        conf[port] = self.build_custom_conf(speed, adv_speeds, cable_type, adv_types, width)
                    expected_speed, expected_type, expected_width = self.get_custom_expected_conf_res(lb[0],
                                                                                                      all_adv_speeds)
                    conf = self.update_custom_expected_conf(conf, lb, expected_speed, expected_type, expected_width)
            logger.debug("Generated subset configuration is: {}".format(conf))
            return conf

    def get_custom_expected_conf_res(self, port, all_adv_speeds):
        expected_speed = max(set.intersection(*all_adv_speeds), key=speed_string_to_int_in_mb)
        matched_types = get_matched_types(self.ports_lanes_dict[port], [expected_speed],
                                          types_dict=self.interfaces_types_dict)
        expected_type = max(matched_types, key=get_interface_cable_width)
        expected_width = get_interface_cable_width(expected_type)
        return expected_speed, expected_type, expected_width

    def build_custom_conf(self, speed, adv_speeds, cable_type, adv_types, width):
        port_custom_conf = {
            AutonegCommandConstants.AUTONEG_MODE: 'disabled',
            AutonegCommandConstants.SPEED: speed,
            AutonegCommandConstants.ADV_SPEED: adv_speeds,
            AutonegCommandConstants.TYPE: cable_type,
            AutonegCommandConstants.WIDTH: width,
            AutonegCommandConstants.ADV_TYPES: self.get_types_in_string_format(adv_types)
        }
        return port_custom_conf

    @staticmethod
    def update_custom_expected_conf(conf, lb, expected_speed, expected_type, expected_width):
        for port in lb:
            conf[port]['expected_speed'] = expected_speed
            conf[port]['expected_type'] = expected_type
            conf[port]['expected_width'] = expected_width
        return conf

    def get_default_expected_conf_res(self, lb, lb_mutual_speeds):
        expected_speed = max(lb_mutual_speeds, key=speed_string_to_int_in_mb)
        matched_types = get_matched_types(self.ports_lanes_dict[lb[0]], [expected_speed],
                                          types_dict=self.interfaces_types_dict)
        expected_interface_type = max(matched_types, key=get_interface_cable_width)
        expected_width = get_interface_cable_width(expected_interface_type)
        return expected_speed, expected_interface_type, expected_width

    @staticmethod
    def build_default_conf(min_speed, min_type, width, expected_speed, expected_type, expected_width):
        port_default_conf = {
            AutonegCommandConstants.AUTONEG_MODE: 'disabled',
            AutonegCommandConstants.SPEED: min_speed,
            AutonegCommandConstants.ADV_SPEED: 'all',
            AutonegCommandConstants.TYPE: min_type,
            AutonegCommandConstants.WIDTH: width,
            AutonegCommandConstants.ADV_TYPES: 'all',
            AutonegCommandConstants.OPER: "up",
            AutonegCommandConstants.ADMIN: "up",
            'expected_speed': expected_speed,
            'expected_type': expected_type,
            'expected_width': expected_width
        }
        return port_default_conf

    @staticmethod
    def update_port_conf(conf, port_list):
        """
        :param conf: current configuration on ports
        :param port_list: list of ports to update
        :return: update conf info to the expected configuration on port when auto neg is enabled
        """
        for port in port_list:
            conf[port][AutonegCommandConstants.SPEED] = conf[port]['expected_speed']
            conf[port][AutonegCommandConstants.TYPE] = conf[port]['expected_type']
            conf[port][AutonegCommandConstants.WIDTH] = conf[port]['expected_width']
            conf[port][AutonegCommandConstants.OPER] = "up"
            conf[port][AutonegCommandConstants.ADMIN] = "up"

    @staticmethod
    def get_loopback_first_second_ports_lists(tested_lb_dict):
        """
        this function returns 2 lists, first list contains the first port in each loopback in tested_lb_dict
        the second list has the second port in each loopback in tested_lb_dict.
        :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
        :return: a list of loopbacks first ports and a list of loopbacks second ports, i.e,
        lb_ports_1_list ['Ethernet48', 'Ethernet12', 'Ethernet20']
        lb_ports_2_list ['Ethernet44', 'Ethernet16', 'Ethernet24']
        """
        lb_ports_1_list, lb_ports_2_list = [], []
        for split_mode, lb_list in tested_lb_dict.items():
            for lb in lb_list:
                lb_ports_1_list.append(lb[0])
                lb_ports_2_list.append(lb[1])
        return lb_ports_1_list, lb_ports_2_list

    def verify_auto_neg_configuration(self, conf, check_adv_parm=True):
        """
        :param conf: a dictionary of the port auto negotiation configuration and expected outcome
        :return:
        """
        with allure.step('Verify speed, advertised speed, type, advertised type, state and width on ports: {}'
                         .format(list(conf.keys()))):
            ports_aliases_dict = self.cli_objects.dut.interface.parse_ports_aliases_on_sonic(self.engines.dut)
            pci_conf = retry_call(self.cli_objects.dut.chassis.get_pci_conf,
                                  fargs=[self.engines.dut], tries=6, delay=10)
            for port, port_conf_dict in conf.items():
                retry_call(self.verify_autoneg_status_cmd_output_for_port, fargs=[self.engines.dut,
                                                                                  self.cli_objects.dut,
                                                                                  port,
                                                                                  port_conf_dict, check_adv_parm],
                           tries=12, delay=10, logger=logger)
                retry_call(self.verify_mlxlink_status_cmd_output_for_port, fargs=[self.engines.dut,
                                                                                  self.cli_objects.dut,
                                                                                  port, port_conf_dict,
                                                                                  ports_aliases_dict, pci_conf],
                           tries=12, delay=10, logger=logger)

    def verify_autoneg_status_cmd_output_for_port(self, dut_engine, cli_object, port, port_conf_dict,
                                                  check_adv_parm=True):
        logger.info("Verify Auto negotiation status based on sonic command")
        sonic_actual_conf = \
            cli_object.interface.parse_show_interfaces_auto_negotiation_status(dut_engine, interface=port)
        self.compare_actual_and_expected_auto_neg_output(expected_conf=port_conf_dict,
                                                         actual_conf=sonic_actual_conf[port],
                                                         check_adv_parm=check_adv_parm)

    def verify_mlxlink_status_cmd_output_for_port(self, dut_engine, cli_object, port, port_conf_dict,
                                                  ports_aliases_dict, pci_conf):
        port_number = get_alias_number(ports_aliases_dict[port])
        logger.info("Verify Auto negotiation status based on mlxlink command")
        mlxlink_actual_conf = cli_object.interface.parse_port_mlxlink_status(dut_engine, pci_conf, port_number)
        self.compare_actual_and_expected_auto_neg_output(expected_conf=port_conf_dict, actual_conf=mlxlink_actual_conf)

    def compare_actual_and_expected_auto_neg_output(self, expected_conf, actual_conf, check_adv_parm=True):
        """
        :return: raise assertion error in case expected and actual configuration don't match
        """
        with allure.step('Compare expected and actual auto neg configuration'):
            logger.debug("expected: {}".format(expected_conf))
            logger.debug("actual: {}".format(actual_conf))
            for key, value in expected_conf.items():
                if key in actual_conf.keys() and key != AutonegCommandConstants.TYPE:
                    actual_conf_value = actual_conf[key]
                    if key == AutonegCommandConstants.ADV_SPEED and check_adv_parm:
                        self.compare_advertised_speeds(value, actual_conf_value)
                    elif key == AutonegCommandConstants.ADV_TYPES and check_adv_parm:
                        self.compare_advertised_types(value, actual_conf_value)
                    elif key not in [AutonegCommandConstants.ADV_SPEED, AutonegCommandConstants.ADV_TYPES]:
                        compare_actual_and_expected(key, value, actual_conf_value)

    @staticmethod
    def compare_advertised_speeds(expected_adv_speed, actual_adv_speed):
        """
        :return:
        """
        if expected_adv_speed != 'all':
            expected_adv_speed = get_speeds_in_Gb_str_format(expected_adv_speed.split(','))
        compare_actual_and_expected(AutonegCommandConstants.ADV_SPEED, expected_adv_speed, actual_adv_speed)

    @staticmethod
    def compare_advertised_types(expected_adv_type, actual_adv_type):
        """
        :return:
        """
        expected_adv_type = expected_adv_type.split(',')
        actual_adv_type = actual_adv_type.split(',')
        compare_actual_and_expected(AutonegCommandConstants.ADV_TYPES, set(expected_adv_type), set(actual_adv_type))

    def set_speed_type_cleanup(self, port, engine, cli_object, base_interfaces_speeds, cleanup_list):
        base_speed = base_interfaces_speeds[port]
        matched_types = get_matched_types(self.ports_lanes_dict[port], [base_speed], self.interfaces_types_dict)
        base_type = max(matched_types, key=get_interface_cable_width)
        cleanup_list.append((cli_object.interface.set_interface_speed, (engine, port, base_speed)))
        cleanup_list.append((cli_object.interface.config_interface_type, (engine, port, base_type)))
        cleanup_list.append((cli_object.interface.config_advertised_speeds, (engine, port, 'all')))
        cleanup_list.append((cli_object.interface.config_advertised_interface_types, (engine, port, 'all')))

    def auto_neg_toggle_peer_checker(self, conf, cleanup_list):
        """
        :param conf: the auto negotiation configuration dictionary to be tested
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        retry_call(self.cli_objects.dut.interface.check_ports_status,
                   fargs=[self.engines.dut, [self.interfaces.dut_ha_1]],
                   tries=18, delay=10, logger=logger)
        dut_interfaces_speeds, ha_interfaces_speeds = retry_call(self.get_peer_ports_speeds,
                                                                 fargs=[],
                                                                 tries=4, delay=10, logger=logger)
        self.disable_auto_neg_on_peer_ports(conf, cleanup_list)
        self.configure_peer_ports(conf, dut_interfaces_speeds, ha_interfaces_speeds, cleanup_list)
        self.toggle_port(self.engines.dut, self.cli_objects.dut, self.interfaces.dut_ha_1, cleanup_list)
        logger.info("Enable auto-negotiation on dut interface {}".format(self.interfaces.dut_ha_1))
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut,
                                     ports_list=[self.interfaces.dut_ha_1], conf=conf,
                                     cleanup_list=cleanup_list, mode='enabled')
        logger.info("Verify speed/type configuration didn't modify while auto neg is off on interface {}"
                    .format(self.interfaces.ha_dut_1))
        self.verify_auto_neg_configuration(conf={self.interfaces.dut_ha_1: conf[self.interfaces.dut_ha_1]})
        logger.info("Enable auto negotiation on host port {}".format(self.interfaces.ha_dut_1))
        self.configure_port_auto_neg(self.engines.ha, self.cli_objects.ha, ports_list=[self.interfaces.ha_dut_1],
                                     conf=conf, cleanup_list=cleanup_list, mode='on')
        self.toggle_port(self.engines.ha, self.cli_objects.ha, self.interfaces.ha_dut_1, cleanup_list)
        logger.info("Check configuration on ports modify when auto neg is enabled on both ports")
        self.update_port_conf(conf, port_list=list(conf.keys()))
        self.verify_auto_neg_configuration(conf={self.interfaces.dut_ha_1: conf[self.interfaces.dut_ha_1]})
        logger.info("Validate with traffic between dut-host ports")
        self.validate_traffic()

    def get_peer_ports_speeds(self):
        logger.info("Get base speed settings on ports: {}".format([self.interfaces.dut_ha_1, self.interfaces.ha_dut_1]))
        dut_interfaces_speeds = \
            self.cli_objects.dut.interface.get_interfaces_speed(self.engines.dut,
                                                                interfaces_list=[self.interfaces.dut_ha_1])
        ha_interfaces_speeds = {self.interfaces.ha_dut_1: dut_interfaces_speeds[self.interfaces.dut_ha_1]}
        return dut_interfaces_speeds, ha_interfaces_speeds

    def disable_auto_neg_on_peer_ports(self, conf, cleanup_list):
        logger.info("Disable auto negotiation on host port {}".format(self.interfaces.ha_dut_1))
        self.configure_port_auto_neg(self.engines.ha, self.cli_objects.ha, ports_list=[self.interfaces.ha_dut_1],
                                     conf=conf, cleanup_list=cleanup_list, mode='off')
        logger.info("Disable auto-negotiation on dut interface {}".format(self.interfaces.dut_ha_1))
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, ports_list=[self.interfaces.dut_ha_1],
                                     conf=conf, cleanup_list=cleanup_list, mode='disabled')

    def configure_peer_ports(self, conf, dut_interfaces_speeds, ha_interfaces_speeds, cleanup_list):
        logger.info("Configure auto negotiation on dut port {}".format(self.interfaces.dut_ha_1))
        self.configure_ports(self.engines.dut, self.cli_objects.dut,
                             conf={self.interfaces.dut_ha_1: conf[self.interfaces.dut_ha_1]},
                             base_interfaces_speeds=dut_interfaces_speeds, cleanup_list=cleanup_list)
        logger.info("Configure auto negotiation on host port {}".format(self.interfaces.ha_dut_1))
        self.configure_ports(self.engines.ha, self.cli_objects.ha,
                             conf={self.interfaces.ha_dut_1: conf[self.interfaces.ha_dut_1]},
                             base_interfaces_speeds=ha_interfaces_speeds, cleanup_list=cleanup_list)

    def toggle_port(self, engine, cli_object, port, cleanup_list):
        logger.info("Toggle port: {}".format(port))
        self.disable_interface(engine, cli_object, port, cleanup_list)
        cli_object.interface.enable_interface(engine, port)

    def set_peer_port_ip_conf(self, cleanup_list):
        """
        set ips on the dut and host ports
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: None
        """
        ip_config_dict = \
            {'dut': [{'iface': self.interfaces.dut_ha_1, 'ips': [('20.20.20.1', '24')]}],
             'ha': [{'iface': self.interfaces.ha_dut_1, 'ips': [('20.20.20.2', '24')]}]}
        cleanup_list.append((IpConfigTemplate.cleanup, (self.topology_obj, ip_config_dict,)))
        IpConfigTemplate.configuration(self.topology_obj, ip_config_dict)

    def validate_traffic(self):
        """
        send ping between dut and host and validate the results
        :return: raise assertion errors in case of validation errors
        """
        with allure.step('send ping from {} to {}'.format(self.interfaces.ha_dut_1, self.interfaces.dut_ha_1)):
            validation = {'sender': 'ha', 'args': {'interface': self.interfaces.ha_dut_1,
                                                   'count': 3, 'dst': '20.20.20.1'}}
            ping = PingChecker(self.topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from {} to {}'.format(self.interfaces.ha_dut_1,
                                                                          self.interfaces.dut_ha_1))
            ping.run_validation()

    @staticmethod
    def disable_interface(engine, cli_object, interface, cleanup_list):
        """
        disable the interface and add interface enabling to cleanup
        :param engine: a ssh connection
        :param cli_object: a cli object
        :param interface: an interface
        :param cleanup_list: a list of cleanup functions that should be called in the end of the test
        :return: None
        """
        logger.info("Disable the interface {}".format(interface))
        cleanup_list.append((cli_object.interface.enable_interface, (engine, interface)))
        cli_object.interface.disable_interface(engine, interface)

    def auto_neg_checker(self, tested_lb_dict, conf, cleanup_list, set_cleanup=True):
        """
        The function does as following:
         1) Configure the auto negotiation configuration on ports(speed, type, advertised speeds, advertised types)
         2) Enable auto negotiation mode on the first port of the loopbacks
         3) Check the speed type configuration didn't change
         while auto negotiation is only enabled on one port in the loopabck.
         4) Enable auto negotiation mode on the second port of the loopbacks
         5) Verify the speed/type change to the expected result
         6) Verify with traffic

        :param tested_lb_dict:  a dictionary of loopback list for each split mode on the dut
        :param conf: a dictionary of the port auto negotiation configuration and expected outcome
        :param cleanup_list: a list of cleanup functions that should be called in the end of the test
        :param set_cleanup:  if True, add cleanup to cleanup list
        :return: raise a assertion error in case validation failed
        """
        with allure.step("Auto negotiation checker"):
            lb_ports_1_list, lb_ports_2_list = self.get_loopback_first_second_ports_lists(tested_lb_dict)
            base_interfaces_speeds = self.cli_objects.dut.interface.get_interfaces_speed(self.engines.dut,
                                                                                         interfaces_list=conf.keys())
            logger.info("Configure auto negotiation configuration on "
                        "ports(speed,type,advertised speeds,advertised types)")
            self.configure_ports(self.engines.dut, self.cli_objects.dut,
                                 conf, base_interfaces_speeds, cleanup_list, set_cleanup=set_cleanup)
            logger.info("Enable auto negotiation mode on the first port of the loopbacks")
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, lb_ports_1_list, conf, cleanup_list)
            logger.info("Check configuration on ports did not modify while auto neg is enabled on one loopback port")
            self.verify_auto_neg_configuration(conf, check_adv_parm=False)
            logger.info("Enable auto negotiation mode on the second port of the loopbacks")
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, lb_ports_2_list, conf, cleanup_list)
            self.update_port_conf(conf, conf.keys())
            logger.info("Verify the speed/type change to expected "
                        "result when auto neg is enabled on both loopback ports")
            self.verify_auto_neg_configuration(conf, check_adv_parm=True)
            # send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, get_loopback_lists(tested_lb_dict))

    @staticmethod
    def get_types_in_string_format(types_list):
        """
        :param types_list: a list/set of types, i.e, {'CR', 'CR4'}
        :return: return a string of types configuration in string list format, i.e,'CR,CR4'
        """
        return ",".join(types_list)

    def configure_ports(self, engine, cli_object, conf, base_interfaces_speeds, cleanup_list, set_cleanup=True):
        """
        configure the ports speed, advertised speed, type and advertised type based on conf dictionary

        :param engine: an ssh connection
        :param cli_object: a cli object of dut
        :param conf: a dictionary of the port auto negotiation default configuration and expected outcome
        :param base_interfaces_speeds: base speed on the ports before test configuration
        and split mode including host ports i.e, {'Ethernet0': ['40GBASE-CR4', '100GBASE-CR4', '25GBASE-CR'], ...}
        :param cleanup_list: a list of cleanup functions that should be called in the end of the test
        :param set_cleanup: if True, add cleanup to cleanup list
        :return: none
        """
        with allure.step('Configuring speed, advertised speed, type and advertised type on ports: {}'
                         .format(list(conf.keys()))):
            for port, port_conf_dict in conf.items():
                if set_cleanup:
                    self.set_speed_type_cleanup(port, engine, cli_object, base_interfaces_speeds, cleanup_list)
                logger.info("Configure speed on {}".format(port))
                cli_object.interface.\
                    set_interface_speed(engine, port, port_conf_dict[AutonegCommandConstants.SPEED])
                logger.info("Configure type on {}".format(port))
                cli_object.interface.\
                    config_interface_type(engine, port, port_conf_dict[AutonegCommandConstants.TYPE])
                logger.info("Configure advertised speeds on {}".format(port))
                cli_object.interface.\
                    config_advertised_speeds(engine, port, port_conf_dict[AutonegCommandConstants.ADV_SPEED])
                logger.info("Configure advertised types on {}".format(port))
                cli_object.interface.\
                    config_advertised_interface_types(engine, port, port_conf_dict[AutonegCommandConstants.ADV_TYPES])

    @staticmethod
    def configure_port_auto_neg(engine, cli_object, ports_list, conf, cleanup_list, mode='enabled'):
        """
        configure the auto neg mode on the port.
        :param engine: a ssh connection
        :param cli_object: cli object of engine
        :param ports_list: a list of ports, i.e,
        :param conf: a dictionary of the port auto negotiation default configuration and expected outcome
        :param cleanup_list: a list of cleanup functions that should be called in the end of the test
        :param mode: a auto negation mode
        :return: none
        """
        with allure.step('configuring auto negotiation mode {} on ports {}'.format(mode, ports_list)):
            for port in ports_list:
                cli_object.interface.config_auto_negotiation_mode(engine, port, mode)
                conf[port][AutonegCommandConstants.AUTONEG_MODE] = mode
                if mode == 'enabled':
                    cleanup_list.append((cli_object.interface.config_auto_negotiation_mode,
                                         (engine, port, 'disabled')))
                if mode == 'off':
                    cleanup_list.append((cli_object.interface.config_auto_negotiation_mode,
                                         (engine, port, 'on')))

    def generate_default_conf(self, tested_lb_dict):
        """
        :param tested_lb_dict: a dictionary of loopback list for each split mode on the dut
        breakout options on all setup ports (including host ports)
        the port cable number and split mode including host port
        :return: a dictionary of the port auto negotiation default configuration and expected outcome
        {'Ethernet52': {'Auto-Neg Mode': 'disabled',
        'Speed': '10G',
        'Adv Speeds': 'all',
        'Type': 'CR',
        'Adv Types': 'all',
        'Oper': 'up',
        'Admin': 'up',
        'expected_speed': '100G',
        'expected_type': 'CR4'}, ...}
        """
        with allure.step('creating default configuration'):
            conf = dict()
            for split_mode, lb_list in tested_lb_dict.items():
                for lb in lb_list:
                    lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
                    min_speed = min(lb_mutual_speeds, key=speed_string_to_int_in_mb)
                    min_type = get_matched_types(self.ports_lanes_dict[lb[0]], [min_speed],
                                                 types_dict=self.interfaces_types_dict).pop()
                    width = get_interface_cable_width(min_type)
                    expected_speed, expected_type, expected_width = self.get_default_expected_conf_res(lb,
                                                                                                       lb_mutual_speeds)
                    for port in lb:
                        conf[port] = self.build_default_conf(min_speed, min_type, width,
                                                             expected_speed, expected_type, expected_width)
            logger.debug("Generated default configuration is: {}".format(conf))
            return conf
