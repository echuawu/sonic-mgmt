import pytest
import logging
from ngts.constants.constants import AutonegCommandConstants
from ngts.tests.nightly.conftest import get_dut_loopbacks
from ngts.tests.nightly.auto_negotition.auto_neg_common import AutoNegBase

logger = logging.getLogger()


@pytest.fixture(autouse=True, scope='session')
def tested_lb_all_dict(topology_obj, interfaces):
    """
    This function return a dictionary with all the switch ports for each split mode.
    :param topology_obj: topology fixture object
    :param interfaces: a dictionary with dut <-> hosts interfaces
    :return: a dictionary with all the switch ports for each split mode., i.e,

    {1: [('Ethernet4', 'Ethernet8'), ('Ethernet36', 'Ethernet40'), ('Ethernet48', 'Ethernet44'),
         ('Ethernet52', 'Ethernet56'), ('Ethernet32', 'enp4s0f0'), ('Ethernet60', 'enp4s0f1'),
         ('Ethernet0', 'enp6s0f0'), ('Ethernet28', 'enp6s0f1')],
    2: [('Ethernet12', 'Ethernet16'), ('Ethernet14', 'Ethernet18')],
    4: [('Ethernet20', 'Ethernet24'), ('Ethernet21', 'Ethernet25'),
        ('Ethernet22', 'Ethernet26'), ('Ethernet23', 'Ethernet27')]}
    """
    tested_lb_dict = {
        1: [],
        2: [(topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1']),
            (topology_obj.ports['dut-lb-splt2-p1-2'], topology_obj.ports['dut-lb-splt2-p2-2'])],
        4: [(topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1']),
            (topology_obj.ports['dut-lb-splt4-p1-2'], topology_obj.ports['dut-lb-splt4-p2-2']),
            (topology_obj.ports['dut-lb-splt4-p1-3'], topology_obj.ports['dut-lb-splt4-p2-3']),
            (topology_obj.ports['dut-lb-splt4-p1-4'], topology_obj.ports['dut-lb-splt4-p2-4'])]
    }
    for lb in get_dut_loopbacks(topology_obj):
        tested_lb_dict[1].append(lb)
    tested_lb_dict[1].append((interfaces.dut_ha_1, interfaces.ha_dut_1))
    tested_lb_dict[1].append((interfaces.dut_ha_2, interfaces.ha_dut_2))
    tested_lb_dict[1].append((interfaces.dut_hb_1, interfaces.hb_dut_1))
    tested_lb_dict[1].append((interfaces.dut_hb_2, interfaces.hb_dut_2))
    return tested_lb_dict


class TestAutoNegScale(AutoNegBase):

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, cli_objects,
              interfaces, ports_lanes_dict,
              split_mode_supported_speeds, interfaces_types_dict,
              platform_params, tested_lb_all_dict):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.cli_objects = cli_objects
        self.tested_lb_all_dict = tested_lb_all_dict
        self.ports_lanes_dict = ports_lanes_dict
        self.split_mode_supported_speeds = split_mode_supported_speeds
        self.interfaces_types_dict = interfaces_types_dict

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
