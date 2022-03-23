#!/usr/bin/env python
import allure
import logging
import pytest


logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
@allure.title('Verify dockers are up on DUT')
def test_verify_dockers_are_up(topology_obj, dockers_list):
    """
    This script will verify dockers are up  on the dut.
    :param topology_obj: topology object fixture
    :return: raise assertion error in case of script failure
    """
    try:
        cli_obj = topology_obj.players['dut']['cli']
        cli_obj.general.verify_dockers_are_up(dockers_list)
    except Exception as err:
        raise AssertionError(err)
