import logging

from ngts.constants.constants import AutonegCommandConstants
from ngts.tests.nightly.auto_negotition.auto_neg_common import TestAutoNegBase

logger = logging.getLogger()


class TestAutoNegScale(TestAutoNegBase):

    def test_scale(self, cleanup_list):
        """
        The following test checks:
        1) configure the smallest speed, type on all interfaces
        2) configure all advertised speeds, types on all interfaces
        3) enable auto-negotiation
        4) verify speed, type was modified for all ports

        :param cleanup_list: a list of cleanup functions that should be called in the end of the test
        :return: raise assertion error in case of failure
        """
        conf = self.generate_default_conf(self.tested_lb_all_dict)
        ports = self.topology_obj.players_all_ports['dut']
        dut_conf = dict()
        for port in ports:
            dut_conf[port] = conf[port]

        logger.info("Set auto negotiation mode to disabled on ports before test starts")
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, ports,
                                     dut_conf, cleanup_list, mode='disabled')
        logger.info("Get ports default speed settings")
        base_interfaces_speeds = self.cli_objects.dut.interface.get_interfaces_speed(self.engines.dut,
                                                                                     interfaces_list=ports)
        logger.info("configure the smallest speed/type and configure all advertised speeds/types on all interfaces")
        self.configure_ports(self.engines.dut, self.cli_objects.dut, dut_conf, base_interfaces_speeds, cleanup_list)
        logger.info("Check auto negotiation was configured correctly")
        self.verify_auto_neg_configuration(dut_conf, check_adv_parm=False)
        logger.info("Set auto negotiation mode to enabled on all ports")
        self.configure_port_auto_neg(self.engines.dut, self.cli_objects.dut, ports, dut_conf,
                                     cleanup_list, mode='enabled')
        for port, port_conf_dict in dut_conf.items():
            port_conf_dict[AutonegCommandConstants.SPEED] = dut_conf[port]['expected_speed']
            port_conf_dict[AutonegCommandConstants.TYPE] = dut_conf[port]['expected_type']
            port_conf_dict[AutonegCommandConstants.WIDTH] = dut_conf[port]['expected_width']
            port_conf_dict[AutonegCommandConstants.OPER] = "up"
            port_conf_dict[AutonegCommandConstants.ADMIN] = "up"
        logger.info("verify speed, type was modified for all ports")
        self.verify_auto_neg_configuration(dut_conf)
