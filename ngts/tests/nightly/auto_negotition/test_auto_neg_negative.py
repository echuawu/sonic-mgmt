import random
import logging
import pytest
import allure
from retry.api import retry_call

from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.tests.nightly.auto_negotition.conftest import convert_speeds_to_mb_format, get_matched_types, \
    get_interface_cable_width
from ngts.tests.nightly.auto_negotition.auto_neg_common import TestAutoNegBase
from ngts.tests.nightly.conftest import cleanup
from ngts.helpers.interface_helpers import get_lb_mutual_speed
from ngts.constants.constants import AutonegCommandConstants

logger = logging.getLogger()

ALL_CABLE_TYPES = {'CR', 'CR2', 'CR4', 'SR', 'SR2', 'SR4', 'LR',
                   'LR4', 'KR', 'KR2', 'KR4', 'CAUI', 'GMII',
                   'SFI', 'XLAUI', 'CAUI4', 'XAUI', 'XFI'}

INVALID_SPEED = '30G'
INVALID_INTERFACE_NAME = "EthernetX"
INVALID_AUTO_NEG_MODE = "enable"
INVALID_PORT_ERR_REGEX = r"Invalid\s+port"
INVALID_SPEED_ERR_REGEX = r"Invalid\s+speed\s+specified"
INVALID_AUTO_NEG_MODE_ERR_REGEX = r'Error:\s+Invalid\s+value\s+for\s+"<mode>":\s+invalid choice:' \
                                  r'\s+enable.\s\(choose\s+from\s+enabled,\s+disabled\)'


class TestAutoNegNegative(TestAutoNegBase):

    def test_negative_config_interface_autoneg(self):
        """
        Test command "config interface autoneg <interface_name> <mode>".
        Verify the command return error if given invalid interface

        :return: raise assertion error in case of failure
        """
        with allure.step("Verify the command return error if given invalid auto neg mode"):
            logger.info("Verify the command return error if given invalid auto neg mode.")
            output = \
                self.cli_objects.dut.interface.config_auto_negotiation_mode(self.engines.dut, self.interfaces.dut_ha_1,
                                                                            INVALID_AUTO_NEG_MODE)
            verify_show_cmd(output, [(INVALID_AUTO_NEG_MODE_ERR_REGEX, True)])

        with allure.step("Verify the command return error if given invalid interface_name"):
            logger.info("Verify the command return error if given invalid interface_name")
            output = \
                self.cli_objects.dut.interface.config_auto_negotiation_mode(self.engines.dut,
                                                                            INVALID_INTERFACE_NAME,
                                                                            "enabled")

            verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])

    def test_negative_config_advertised_speeds(self, cleanup_list, skip_if_active_optical_cable):
        """
        Test command config interface advertised-speeds <interface_name> <speed_list>.
        Verify the command return error if given invalid interface name or speed list.
        Verify auto-negotiation fails in case of mismatch advertised speeds list,
        meaning the port should not change speed because ports advertised different speeds.
        port should remain in up state even if the auto negotiation failed.

        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        split_mode = 2
        if not self.tested_lb_dict.get(split_mode):
            pytest.skip("Test is skipped because the test could only run on loopback that is split,"
                        " the dut does not have such loopback")
        first_lb = 0
        lb = self.tested_lb_dict[split_mode][first_lb]
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
        with allure.step("Verify the command return error if given invalid speed list"):
            logger.info("Verify the command return error if given invalid speed list")
            output = self.cli_objects.dut.interface.config_advertised_speeds(self.engines.dut, lb[0], INVALID_SPEED)
            verify_show_cmd(output, [(INVALID_SPEED_ERR_REGEX, True)])
        with allure.step("Verify the command return error if given invalid interface name"):
            logger.info("Verify the command return error if given invalid interface name")
            output = self.cli_objects.dut.interface.config_advertised_speeds(self.engines.dut,
                                                                             INVALID_INTERFACE_NAME,
                                                                             "all")
            verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])
        with allure.step("Verify auto-negotiation fails in case of mismatch advertised speeds"):
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
        base_interfaces_speeds = self.cli_objects.dut.interface.get_interfaces_speed(self.engines.dut,
                                                                                     interfaces_list=conf.keys())
        with allure.step("Set auto negotiation mode to disabled on ports"):
            logger.info("Set auto negotiation mode to disabled on ports")
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, lb, conf,
                                         cleanup_list, mode='disabled')
        with allure.step("Configure mismatch auto neg values"):
            logger.info("Configure mismatch auto neg values")
            self.configure_ports(self.engines.dut, self.cli_objects.dut, conf, base_interfaces_speeds, cleanup_list)
        with allure.step("Check ports are up while auto neg is disabled"):
            logger.info("Check ports are up while auto neg is disabled")
            retry_call(self.cli_objects.dut.interface.check_ports_status,
                       fargs=[self.engines.dut, lb], tries=3, delay=10,
                       logger=logger)
        with allure.step("Enable auto neg on ports: {}".format(lb)):
            logger.info("Enable auto neg on ports: {}".format(lb))
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, ports_list=lb, conf=conf,
                                         cleanup_list=cleanup_list, mode='enabled')
        with allure.step("verify ports are down due to mismatch"):
            logger.info("verify ports are down due to mismatch")
            retry_call(self.cli_objects.dut.interface.check_ports_status, fargs=[self.engines.dut, lb, 'down'],
                       tries=6, delay=10, logger=logger)
        with allure.step("Cleanup mismatch configuration and validate ports are up"):
            logger.info("Cleanup mismatch configuration and validate ports are up")
            cleanup(cleanup_list)
            retry_call(self.cli_objects.dut.interface.check_ports_status, fargs=[self.engines.dut, lb],
                       tries=6, delay=10, logger=logger)

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
                                                                      INVALID_INTERFACE_NAME,
                                                                      random.choice(types_supported_on_dut))
        verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])

    def test_negative_config_advertised_types(self, cleanup_list, skip_if_active_optical_cable):
        """
        Test command config interface advertised-types <interface_name> <interface_type_list>.
        Verify the command return error if given invalid interface name.
        verify auto-negotiation fails in case of mismatch advertised list.

        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        possible_split_modes = [1, 2] if self.tested_lb_dict.get(2) else [1]
        split_mode = random.choice(possible_split_modes)
        first_lb = 0
        lb = self.tested_lb_dict[split_mode][first_lb]
        with allure.step("Verify the command return error if given invalid interface name"):
            logger.info("Verify the command return error if given invalid interface name")
            output = self.cli_objects.dut.interface.config_advertised_interface_types(self.engines.dut,
                                                                                      INVALID_INTERFACE_NAME,
                                                                                      "all")
            verify_show_cmd(output, [(INVALID_PORT_ERR_REGEX, True)])
        lb_mutual_speeds = get_lb_mutual_speed(lb, split_mode, self.split_mode_supported_speeds)
        lb_mutual_types = get_matched_types(self.ports_lanes_dict[lb[0]], lb_mutual_speeds,
                                            types_dict=self.interfaces_types_dict)
        conf = self.get_mismatch_type_conf(split_mode, lb, list(lb_mutual_types))
        with allure.step("verify auto-negotiation fails in case of mismatch advertised types"):
            logger.info("verify auto-negotiation fails in case of mismatch advertised types")
            self.verify_auto_neg_failure_scenario(lb, conf, cleanup_list)

    def get_mismatch_type_conf(self, split_mode, lb, lb_mutual_types):
        if len(lb_mutual_types) <= 1:
            pytest.skip(f"This test is not supported because lb {lb} doesn't support more than 1 interface type, "
                        f"supported interfaces type on lb are: {lb_mutual_types}")
        rand_idx = random.choice(range(1, len(lb_mutual_types)))
        port_1_adv_type, port_2_adv_type = [lb_mutual_types[0:rand_idx], lb_mutual_types[rand_idx:]]
        tested_lb_dict = {split_mode: [lb]}
        conf = self.generate_default_conf(tested_lb_dict)
        conf[lb[0]][AutonegCommandConstants.ADV_TYPES] = ",".join(port_1_adv_type)
        conf[lb[1]][AutonegCommandConstants.ADV_TYPES] = ",".join(port_2_adv_type)
        return conf

    def test_negative_advertised_speed_type_mismatch(self, expected_auto_neg_loganalyzer_exceptions,
                                                     cleanup_list, skip_if_active_optical_cable):
        """
        Verify error in log when configuring mismatch type and speed, like 'CR4' and '10G',
        Verify port state is up when speed and type doesn't match,
        and configuration is not applied because of SAI recognize it as invalid configuration.

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
