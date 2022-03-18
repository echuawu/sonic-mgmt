#!/usr/bin/env python
import allure
import logging
import pytest
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


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
        dut_engine = topology_obj.players['dut']['engine']
        SonicGeneralCli(engine=dut_engine).verify_dockers_are_up(dockers_list)
    except Exception as err:
        raise AssertionError(err)
