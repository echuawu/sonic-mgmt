import re
import random
import logging
import pytest
from retry.api import retry_call

from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.tests.nightly.auto_negotition.conftest import convert_speeds_to_mb_format, get_matched_types, \
    get_interface_cable_width
from ngts.tests.nightly.auto_negotition.auto_neg_common import AutoNegBase
from ngts.tests.nightly.conftest import cleanup
from ngts.helpers.interface_helpers import get_lb_mutual_speed
from ngts.constants.constants import AutonegCommandConstants

logger = logging.getLogger()

ALL_CABLE_TYPES = {'CR', 'CR2', 'CR4', 'SR', 'SR2', 'SR4', 'LR',
                   'LR4', 'KR', 'KR2', 'KR4', 'CAUI', 'GMII',
                   'SFI', 'XLAUI', 'CAUI4', 'XAUI', 'XFI'}

INVALID_AUTO_NEG_MODE = r"enable"
INVALID_PORT_ERR_REGEX = r"Invalid\s+port"
INVALID_SPEED_ERR_REGEX = r"Invalid\s+speed\s+specified"
INVALID_AUTO_NEG_MODE_ERR_REGEX = r'Error:\s+Invalid\s+value\s+for\s+"<mode>":\s+invalid choice:' \
                                  r'\s+enable.\s\(choose\s+from\s+enabled,\s+disabled\)'


class TestAutoNegNegative(AutoNegBase):

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects,
              interfaces, tested_lb_dict, ports_lanes_dict,
              split_mode_supported_speeds, interfaces_types_dict, platform_params):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.cli_objects = cli_objects
        self.tested_lb_dict = tested_lb_dict
        self.ports_lanes_dict = ports_lanes_dict
        self.split_mode_supported_speeds = split_mode_supported_speeds
        self.interfaces_types_dict = interfaces_types_dict
        self.ports_aliases_dict = self.cli_objects.dut.interface.parse_ports_aliases_on_sonic(self.engines.dut)
        self.pci_conf = retry_call(self.cli_objects.dut.chassis.get_pci_conf, fargs=[self.engines.dut],
                                   tries=6, delay=10)

    def test_negative_config_interface_autoneg(self):
        """
        Test command "config interface autoneg <interface_name> <mode>".
        Verify the command return error if given invalid interface

        :return: raise assertion error in case of failure
        """
        logger.info("Verify the command return error if given invalid auto neg mode.")
        output = \
            self.cli_objects.dut.interface.config_auto_negotiation_mode(self.engines.dut, self.interfaces.dut_ha_1,
                                                                        INVALID_AUTO_NEG_MODE)
        verify_show_cmd(output, [(INVALID_AUTO_NEG_MODE_ERR_REGEX, True)])

        logger.info("Verify the command return error if given invalid interface_name")
        output = \
            self.cli_objects.dut.interface.config_auto_negotiation_mode(self.engines.dut,
                                                                        self.get_invalid_interface(self.topology_obj),
                                                                        "enabled")

        verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])

    @staticmethod
    def get_invalid_interface(topology_obj):
        """
        :param topology_obj: a topology fixture
        :return: an interface that does not exist on dut, i.e, Ethernet61
        """
        ports = topology_obj.players_all_ports['dut']
        port_num = list(map(lambda port: int(re.search(r"Ethernet(\d+)", port).group(1)), ports))
        max_port = max(port_num)
        return "Ethernet{}".format(max_port + 1)

    def test_negative_config_advertised_speeds(self, ignore_auto_neg_expected_loganalyzer_exceptions, cleanup_list):
        """
        Test command config interface advertised-speeds <interface_name> <speed_list>.
        Verify the command return error if given invalid interface name or speed list.
        Verify auto-negotiation fails in case of mismatch advertised speeds list,
        meaning the port should not change speed because ports advertised different speeds.
        port should remain in up state even if the auto negotiation failed.

        :param  ignore_auto_neg_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        split_mode = 2
        first_lb = 0
        lb = self.tested_lb_dict[split_mode][first_lb]
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)

        logger.info("Verify the command return error if given invalid speed list")
        invalid_speed = self.get_invalid_speed(lb[0], lb_mutual_speeds, self.split_mode_supported_speeds)
        output = self.cli_objects.dut.interface.config_advertised_speeds(self.engines.dut, lb[0], invalid_speed)
        verify_show_cmd(output, [(INVALID_SPEED_ERR_REGEX, True)])

        logger.info("Verify the command return error if given invalid interface name")
        output = self.cli_objects.dut.interface.config_advertised_speeds(self.engines.dut,
                                                                         self.get_invalid_interface(self.topology_obj),
                                                                         "all")
        verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])

        logger.info("Verify auto-negotiation fails in case of mismatch advertised speeds")
        conf = self.get_mismatch_speed_conf(split_mode, lb, lb_mutual_speeds)
        self.verify_auto_neg_failure_scenario(lb, conf, cleanup_list)

    def get_mismatch_speed_conf(self, split_mode, lb, lb_mutual_speeds):
        rand_idx = random.choice(range(1, len(lb_mutual_speeds)))
        port_1_adv_speed, port_2_adv_speed = [lb_mutual_speeds[0:rand_idx], lb_mutual_speeds[rand_idx:]]
        tested_lb_dict = {split_mode: [lb]}
        conf = self.generate_default_conf(tested_lb_dict)
        conf[lb[0]][AutonegCommandConstants.ADV_SPEED] = convert_speeds_to_mb_format(port_1_adv_speed)
        conf[lb[1]][AutonegCommandConstants.ADV_SPEED] = convert_speeds_to_mb_format(port_2_adv_speed)
        return conf

    def verify_auto_neg_failure_scenario(self, lb, conf, cleanup_list):
        logger.info("Set auto negotiation mode to disabled on ports")
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, lb, conf, cleanup_list, mode='disabled')
        base_interfaces_speeds = self.cli_objects.dut.interface.get_interfaces_speed(self.engines.dut,
                                                                                     interfaces_list=conf.keys())
        logger.info("Configure mismatch auto neg values")
        self.configure_ports(self.engines.dut, self.cli_objects.dut, conf, base_interfaces_speeds, cleanup_list)
        logger.info("Check ports are up while auto neg is disabled")
        retry_call(self.cli_objects.dut.interface.check_ports_status, fargs=[self.engines.dut, lb], tries=3, delay=10,
                   logger=logger)
        logger.info("Enable auto neg on ports: {} and verify ports are down due to mismatch".format(lb))
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, ports_list=lb, conf=conf,
                                     cleanup_list=cleanup_list, mode='enabled')
        retry_call(self.cli_objects.dut.interface.check_ports_status, fargs=[self.engines.dut, lb, 'down'],
                   tries=6, delay=10, logger=logger)
        logger.info("Cleanup mismatch configuration and validate ports are up")
        cleanup(cleanup_list)
        retry_call(self.cli_objects.dut.interface.check_ports_status, fargs=[self.engines.dut, lb],
                   tries=6, delay=10, logger=logger)

    @staticmethod
    def get_invalid_speed(port, supported_speeds, split_mode_supported_speeds):
        """
        :param port: an interface on dut , i.e, Ethernet60
        :param supported_speeds: a list of port supported speeds
        :param split_mode_supported_speeds: a dictionary with available speed for each breakout mode on all setup ports
        :return: a list of speeds which are not supported by the port, i.e,
        """
        return convert_speeds_to_mb_format(set(split_mode_supported_speeds[port][1]).difference(supported_speeds))

    def test_negative_config_interface_type(self):
        """
        Test command "config interface type <interface_name> <interface_type>".
        Verify the command return error if given invalid interface name.

        the port cable number and split mode including host port
        :return: raise assertion error in case of failure
        """
        logger.info("Verify the command return error if given invalid interface name")
        types_supported_on_dut = []
        for supported_types_dict in self.interfaces_types_dict.values():
            types_supported_on_dut += supported_types_dict.keys()
        output = self.cli_objects.dut.interface.config_interface_type(self.engines.dut,
                                                                      self.get_invalid_interface(self.topology_obj),
                                                                      random.choice(types_supported_on_dut))
        verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])

    def test_negative_config_advertised_types(self, ignore_auto_neg_expected_loganalyzer_exceptions, cleanup_list):
        """
        Test command config interface advertised-types <interface_name> <interface_type_list>.
        Verify the command return error if given invalid interface name.
        verify auto-negotiation fails in case of mismatch advertised list.

        :param  ignore_auto_neg_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        split_mode = random.choice([2, 1])
        first_lb = 0
        lb = self.tested_lb_dict[split_mode][first_lb]
        logger.info("Verify the command return error if given invalid interface name")
        output = self.cli_objects.dut.interface.config_advertised_interface_types(self.engines.dut,
                                                                                  self.get_invalid_interface(
                                                                                      self.topology_obj),
                                                                                  "all")
        verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
        lb_mutual_types = get_matched_types(self.ports_lanes_dict[lb[0]], lb_mutual_speeds,
                                            types_dict=self.interfaces_types_dict)
        conf = self.get_mismatch_type_conf(split_mode, lb, list(lb_mutual_types))
        logger.info("verify auto-negotiation fails in case of mismatch advertised types")
        self.verify_auto_neg_failure_scenario(lb, conf, cleanup_list)

    def get_mismatch_type_conf(self, split_mode, lb, lb_mutual_types):
        rand_idx = random.choice(range(1, len(lb_mutual_types)))
        port_1_adv_type, port_2_adv_type = [lb_mutual_types[0:rand_idx], lb_mutual_types[rand_idx:]]
        tested_lb_dict = {split_mode: [lb]}
        conf = self.generate_default_conf(tested_lb_dict)
        conf[lb[0]][AutonegCommandConstants.ADV_TYPES] = ",".join(port_1_adv_type)
        conf[lb[1]][AutonegCommandConstants.ADV_TYPES] = ",".join(port_2_adv_type)
        return conf

    def test_negative_advertised_speed_type_mismatch(self, expected_auto_neg_loganalyzer_exceptions,
                                                     ignore_auto_neg_expected_loganalyzer_exceptions,
                                                     cleanup_list):
        """
        Verify error in log when configuring mismatch type and speed, like 'CR4' and '10G',
        Verify port state is up when speed and type doesn't match,
        and configuration is not applied because of SAI recognize it as invalid configuration.

        :param ignore_auto_neg_expected_loganalyzer_exceptions: expand the logger analyzer errors before the test run
        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        split_mode = 1
        first_lb = 0
        lb = self.tested_lb_dict[split_mode][first_lb]
        tested_lb_dict = {1: [lb]}
        conf = self.get_mismatch_speed_type_conf(lb, split_mode, tested_lb_dict)
        logger.info("verify auto-negotiation fails in case of mismatch advertised types and speeds")
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, conf.keys(),
                                     conf, cleanup_list, mode='disabled')
        self.auto_neg_checker(tested_lb_dict, conf, cleanup_list)

    def get_mismatch_speed_type_conf(self, lb, split_mode, tested_lb_dict):
        """
        return configuration with mismatch type and speed, like 'CR4' and '10G',
        and configuration is not applied because of SAI recognize it as invalid configuration.
        so the expected spped, type and width should be the default values configured
        :param lb: a tuple of ports, i.e ('Ethernet4', 'Ethernet8')
        :param split_mode: the port split mode, i.e, 1/2/4
        :param tested_lb_dict: the tested lb dict, i.e, {1: [lb]}
        :return: a dictionary with auto neg configuration for the ports
        """
        conf = self.generate_default_conf(tested_lb_dict)
        conf_min_speed = conf[lb[0]][AutonegCommandConstants.SPEED]
        min_speed_matched_type = get_matched_types(self.ports_lanes_dict[lb[0]], [conf_min_speed],
                                                   types_dict=self.interfaces_types_dict).pop()
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
        lb_mutual_types = get_matched_types(self.ports_lanes_dict[lb[0]], lb_mutual_speeds,
                                            types_dict=self.interfaces_types_dict)
        max_type = max(lb_mutual_types, key=get_interface_cable_width)
        if min_speed_matched_type == max_type:
            pytest.skip("This test is not supported")
        conf[lb[0]][AutonegCommandConstants.ADV_SPEED] = \
            convert_speeds_to_mb_format([conf[lb[0]][AutonegCommandConstants.SPEED]])
        conf[lb[0]][AutonegCommandConstants.ADV_TYPES] = max_type
        for port, port_conf_dir in conf.items():
            conf[port]['expected_speed'] = conf[port][AutonegCommandConstants.SPEED]
            conf[port]['expected_type'] = conf[port][AutonegCommandConstants.TYPE]
            conf[port]['expected_width'] = conf[port][AutonegCommandConstants.WIDTH]
        return conf
