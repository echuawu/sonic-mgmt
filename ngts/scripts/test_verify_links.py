#!/usr/bin/env python
import logging
import pytest
logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_verify_links_up(topology_obj):
    """
    This script will verify that all the links are up on the dut.
    :param topology_obj: topology object fixture
    :return: raise assertion error in case of script failure
    """
    try:
        cli_object = topology_obj.players['dut']['cli']
        expected_ports_list = topology_obj.players_all_ports['dut']
        cli_object.interface.check_link_state(expected_ports_list)

    except Exception as err:
        raise AssertionError(err)
