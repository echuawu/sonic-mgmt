import logging
import allure
import pytest
from copy import deepcopy
from ngts.tests.nightly.auto_negotition.conftest import get_interface_cable_width, \
    get_matched_types
from ngts.constants.constants import AutonegCommandConstants
from ngts.tests.nightly.auto_negotition.auto_neg_common import AutoNegBase
from ngts.tests.nightly.conftest import reboot_reload_random

logger = logging.getLogger()


class TestAutoNeg(AutoNegBase):

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects,
              interfaces, tested_lb_dict, tested_dut_host_lb_dict, ports_lanes_dict,
              split_mode_supported_speeds, interfaces_types_dict, platform_params):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.cli_objects = cli_objects
        self.tested_lb_dict = tested_lb_dict
        self.tested_dut_host_lb_dict = tested_dut_host_lb_dict
        self.ports_lanes_dict = ports_lanes_dict
        self.split_mode_supported_speeds = split_mode_supported_speeds
        self.interfaces_types_dict = interfaces_types_dict

    def test_auto_neg_conf(self, cleanup_list, ignore_expected_loganalyzer_reboot_exceptions):
        """
        check 1#:
        This test case will set on loopbacks with/without splits,
        Then will set all advertised-speeds and all advertised-types on loopbacks.
        Enable auto-negotiation and validate speed/type configuration is as expected.

        check 2#:
        set custom advertised-speeds/advertised-types on loopbacks.
        Enable auto-negotiation and validate speed/type configuration is as expected.

        check 3#:
        save configuration and reload/warm reboot switch

        check 4#:
        validate speed/type configuration is as expected.

        check 5#:
        disable auto negotiation and validate the configuration return to previous setting.

        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        with allure.step("Check default auto neg configuration"):
            conf = self.generate_default_conf(self.tested_lb_dict)
            logger.info("Checking default configuration: {}".format(conf))

            logger.info("Set auto negotiation mode to disabled on ports before test starts")
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, conf.keys(),
                                         conf, cleanup_list, mode='disabled')

            logger.info("Enable auto-negotiation with default settings and"
                        " validate speed/type configuration is as expected.")

            self.auto_neg_checker(self.tested_lb_dict, conf, cleanup_list)

            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut,
                                         conf.keys(), conf, cleanup_list, mode='disabled')

        with allure.step("Check custom auto neg configuration"):
            conf = self.generate_subset_conf(self.tested_lb_dict)
            logger.info("Checking custom configuration: {}".format(conf))
            conf_backup = deepcopy(conf)
            logger.info("Enable auto-negotiation with custom settings and "
                        "validate speed/type configuration is as expected.")
            self.auto_neg_checker(self.tested_lb_dict, conf, cleanup_list, set_cleanup=False)

        with allure.step("Randomly reboot/reload"):
            reboot_reload_random(self.topology_obj, self.engines.dut, self.cli_objects.dut, conf.keys(), cleanup_list)

        with allure.step("Verify configuration persist after reboot/reload"):
            logger.info("validate speed/type configuration is as expected after reload/reboot")
            self.verify_auto_neg_configuration(conf)

        with allure.step("Disable auto neg and verify port returns to previous configuration"):
            logger.info("Disable auto negotiation and validate the configuration return to previous setting.")
            self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, conf.keys(),
                                         conf, cleanup_list, mode='disabled')
            self.verify_auto_neg_configuration(conf_backup)

    def test_auto_neg_toggle_peer_port(self, cleanup_list):
        """
        configuring default/costume auto neg on the dut port connected to host
        while toggling a port connected to the host
        Validating auto neg behavior is not affected by the ports being toggled.
        validating with host-dut traffic.

        :param cleanup_list:  a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        with allure.step("Generate configurations for test"):
            def_conf = self.generate_default_conf(self.tested_dut_host_lb_dict)
            sub_conf = self.generate_subset_conf(self.tested_dut_host_lb_dict)
            self.modify_conf_for_toggle_peer(self.interfaces.dut_ha_1, sub_conf, def_conf)

        with allure.step("Set ip configuration for future traffic validations"):
            self.set_peer_port_ip_conf(cleanup_list)

        with allure.step("Check default configuration"):
            logger.info("Checking default configuration: {}".format(def_conf))
            self.auto_neg_toggle_peer_checker(def_conf, cleanup_list)

        with allure.step("Check custom configuration"):
            logger.info("Checking custom configuration: {}".format(sub_conf))
            self.auto_neg_toggle_peer_checker(sub_conf, cleanup_list)

    def modify_conf_for_toggle_peer(self, dut_peer_port, sub_conf, def_conf):
        """
        This function modify the default and subset configuration because in order to
        configure adv-speed on a linux port the only configuration is with hex values,
        i.e. "ethtool -s eth0 advertise 0x1020" and also doesn't support configuration of any subset of speeds.

        Hence, the test only configure adv speeds/type on the dut port and doesn't modify the linux port.
        So the faction modify the expected speed,type,width
        result to what it would be if the configuration is made only on the dut
        and the linux port has the default settings.

        if sub_conf:

        {'Ethernet32': {'Auto-Neg Mode': 'disabled',
        'Speed': '10G',
        'Adv Speeds': '100000,40000,10000',
        'Type': 'CR',
        'Width': 1,
        'Adv Types': 'CR,CR4',
        'expected_speed': '40G', -> will be changed to 100G
        'expected_type': 'CR4',
        'expected_width': 4},
        'enp130s0f0': {'Auto-Neg Mode': 'disabled',
        'Speed': '10G',
        'Adv Speeds': '40000,10000', -> is all
        'Type': 'CR',
        'Width': 1,
        'Adv Types': 'CR,CR4', -> is all
        'expected_speed': '40G', -> will be changed to 100G
        'expected_type': 'CR4',
        'expected_width': 4}}
        """
        peer_port_speed = max(sub_conf[dut_peer_port][AutonegCommandConstants.ADV_SPEED].split(','),
                              key=lambda speed_as_str: int(speed_as_str))
        expected_speed = "{}G".format(int(int(peer_port_speed) / 1000))
        matched_types = get_matched_types(self.ports_lanes_dict[dut_peer_port], [expected_speed],
                                          types_dict=self.interfaces_types_dict)
        expected_interface_type = max(matched_types, key=get_interface_cable_width)

        width = get_interface_cable_width(expected_interface_type)
        for port, port_conf_dict in sub_conf.items():
            sub_conf[port]['expected_speed'] = expected_speed
            sub_conf[port]['expected_type'] = expected_interface_type
            sub_conf[port]['expected_width'] = width
