import os
import pytest
import logging
import random
from retry.api import retry_call
from ngts.tests.nightly.conftest import get_dut_loopbacks, cleanup
from ngts.constants.constants import AutonegCommandConstants, SonicConst
from ngts.helpers.interface_helpers import get_alias_number, get_lb_mutual_speed

logger = logging.getLogger()


# list of tested protocols
FEC_MODE_LIST = [SonicConst.FEC_RS_MODE, SonicConst.FEC_FC_MODE, SonicConst.FEC_NONE_MODE]


@pytest.fixture(autouse=True)
def cleanup_list():
    """
    Fixture to execute cleanup after a test has run
    :return: None
    """
    cleanup_list = []
    logger.info("------------------TEST START HERE------------------")
    yield cleanup_list
    logger.info("------------------TEST TEARDOWN------------------")
    cleanup(cleanup_list)


@pytest.fixture(autouse=False)
def ignore_expected_loganalyzer_reboot_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "..", "..", "..",
                                                               "tools", "loganalyzer",
                                                               "reboot_loganalyzer_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


@pytest.fixture(scope='session')
def pci_conf(engines, cli_objects):
    pci_conf = retry_call(cli_objects.dut.chassis.get_pci_conf, fargs=[engines.dut], tries=6, delay=10)
    return pci_conf


@pytest.fixture(scope='session')
def fec_capability_for_dut_ports(topology_obj, engines, cli_objects, interfaces,
                                 tested_lb_dict, tested_lb_dict_for_bug_2705016_flow):
    logger.info("Getting ports fec capabilities")
    fec_capability_for_dut_ports_dict = {}
    ports = get_tested_lb_dict_tested_ports(tested_lb_dict)
    ports += get_tested_lb_dict_tested_ports(tested_lb_dict_for_bug_2705016_flow)
    ports += [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
    for port in ports:
        fec_capability_for_dut_ports_dict[port] = \
            cli_objects.dut.interface.get_interface_supported_fec_modes(engines.dut, port)
    logger.debug("ports fec capabilities: {}".format(fec_capability_for_dut_ports_dict))
    return fec_capability_for_dut_ports_dict


@pytest.fixture(autouse=True, scope='session')
def tested_lb_dict(topology_obj, split_mode_supported_speeds):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback list for each split mode on the dut
    {1: [('Ethernet52', 'Ethernet56')],
    2: [('Ethernet12', 'Ethernet16')],
    4: [('Ethernet20', 'Ethernet24')]}
    """
    lb_list_in_split_mode_1 = random.sample(get_dut_loopbacks(topology_obj), k=3)
    split_2_lb = (topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1'])
    split_4_lb = (topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1'])
    tested_lb_dict = {
        1: {
            SonicConst.FEC_RS_MODE: [lb_list_in_split_mode_1[0]],
            SonicConst.FEC_FC_MODE: [lb_list_in_split_mode_1[1]],
            SonicConst.FEC_NONE_MODE: [lb_list_in_split_mode_1[2]],
        },
        2: {
            random.choice(FEC_MODE_LIST): [split_2_lb]
        }
    }
    mutual_speeds = get_lb_mutual_speed(split_4_lb, 4, split_mode_supported_speeds)
    if mutual_speeds:
        tested_lb_dict[4] = {random.choice(FEC_MODE_LIST): [split_4_lb]}
    return tested_lb_dict


@pytest.fixture(autouse=True, scope='session')
def tested_lb_dict_for_bug_2705016_flow(topology_obj, split_mode_supported_speeds):
    """
    :param topology_obj: topology object fixture
    :return: a dictionary of loopback list for each split mode on the dut
    {1: [('Ethernet52', 'Ethernet56')],
    2: [('Ethernet12', 'Ethernet16')],
    4: [('Ethernet20', 'Ethernet24')]}
    """
    modes_checked_in_bug_2705016_flow = [SonicConst.FEC_RS_MODE, SonicConst.FEC_NONE_MODE]
    lb_list_in_split_mode_1 = random.sample(get_dut_loopbacks(topology_obj), k=4)
    split_2_lb = (topology_obj.ports['dut-lb-splt2-p1-1'], topology_obj.ports['dut-lb-splt2-p2-1'])
    split_4_lb = (topology_obj.ports['dut-lb-splt4-p1-1'], topology_obj.ports['dut-lb-splt4-p2-1'])
    tested_lb_dict = {
        1: {
            SonicConst.FEC_RS_MODE: [lb_list_in_split_mode_1[0], lb_list_in_split_mode_1[1]],
            SonicConst.FEC_NONE_MODE: [lb_list_in_split_mode_1[2], lb_list_in_split_mode_1[3]],
        },
        2: {
            random.choice(modes_checked_in_bug_2705016_flow): [split_2_lb]
        }
    }
    mutual_speeds = get_lb_mutual_speed(split_4_lb, 4, split_mode_supported_speeds)
    if mutual_speeds:
        tested_lb_dict[4] = {random.choice(modes_checked_in_bug_2705016_flow): [split_4_lb]}
    return tested_lb_dict


@pytest.fixture(autouse=True, scope='session')
def tested_dut_to_host_conn(topology_obj, engines, interfaces, cli_objects):
    tested_conn_dict = {
        SonicConst.FEC_NONE_MODE: {"dut_port": interfaces.dut_ha_1,
                                   "host_port": interfaces.ha_dut_1,
                                   "cli": cli_objects.ha,
                                   "engine": engines.ha,
                                   'host': 'ha'
                                   },
        SonicConst.FEC_FC_MODE: {"dut_port": interfaces.dut_ha_2,
                                 "host_port": interfaces.ha_dut_2,
                                 "cli": cli_objects.ha,
                                 "engine": engines.ha,
                                 'host': 'ha'
                                 },
        SonicConst.FEC_RS_MODE: {"dut_port": interfaces.dut_hb_1,
                                 "host_port": interfaces.hb_dut_1,
                                 "cli": cli_objects.hb,
                                 "engine": engines.hb,
                                 'host': 'hb'
                                 }
                        }
    return tested_conn_dict


@pytest.fixture(autouse=True, scope='session')
def dut_ports_number_dict(topology_obj, engines, cli_objects):
    dut_ports_number_dict = {}
    ports = topology_obj.players_all_ports['dut']
    ports_aliases_dict = cli_objects.dut.interface.parse_ports_aliases_on_sonic(engines.dut)
    for port in ports:
        dut_ports_number_dict[port] = get_alias_number(ports_aliases_dict[port])
    return dut_ports_number_dict


@pytest.fixture(autouse=True, scope='session')
def dut_ports_default_speeds_configuration(topology_obj, engines, cli_objects):
    ports = topology_obj.players_all_ports['dut']
    return cli_objects.dut.interface.get_interfaces_speed(engines.dut, interfaces_list=ports)


@pytest.fixture(autouse=True, scope='session')
def dut_ports_default_mlxlink_configuration(topology_obj, engines, cli_objects, interfaces, tested_lb_dict,
                                            tested_lb_dict_for_bug_2705016_flow, pci_conf, dut_ports_number_dict):
    logger.info("Getting port basic fec configuration")
    dut_ports_basic_mlxlink_dict = {}

    ports = get_tested_lb_dict_tested_ports(tested_lb_dict)
    ports += get_tested_lb_dict_tested_ports(tested_lb_dict_for_bug_2705016_flow)
    ports += [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
    for port in ports:
        port_number = dut_ports_number_dict[port]
        mlxlink_conf = retry_call(cli_objects.dut.interface.parse_port_mlxlink_status,
                                  fargs=[engines.dut, pci_conf, port_number],
                                  tries=6, delay=10, logger=logger)
        port_fec_mode = mlxlink_conf[AutonegCommandConstants.FEC]
        port_width_mode = int(mlxlink_conf[AutonegCommandConstants.WIDTH])
        dut_ports_basic_mlxlink_dict[port] = {
            AutonegCommandConstants.FEC: port_fec_mode,
            AutonegCommandConstants.TYPE: "CR{}".format(port_width_mode if port_width_mode > 1 else "")
        }
    logger.debug("port basic fec configuration: {}".format(dut_ports_basic_mlxlink_dict))
    return dut_ports_basic_mlxlink_dict


def get_tested_lb_dict_tested_ports(tested_lb_dict):
    tested_ports_list = []
    for split_mode, fec_mode_tested_lb_dict in tested_lb_dict.items():
        for fec_mode, lb_list in fec_mode_tested_lb_dict.items():
            for lb in lb_list:
                for port in lb:
                    tested_ports_list.append(port)
    return tested_ports_list


def get_lb_mutual_fec_modes(lb, fec_capability_for_dut_ports):
    port_supported_fec_modes = []
    for port in lb:
        port_supported_fec_modes.append(set(fec_capability_for_dut_ports[port]))
    return list(set.intersection(*port_supported_fec_modes))