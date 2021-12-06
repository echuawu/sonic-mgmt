#!/usr/bin/env python
import allure
import logging
import pytest
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@pytest.mark.reboot_reload
@pytest.mark.disable_loganalyzer
@allure.title('Apply Sonic Basic Configuration')
def test_apply_basic_conf(topology_obj, setup_name, platform_params):
    """
    This script will apply basic configuration on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform_params: platform_params fixture
    :return: raise assertion error in case of script failure
    """
    try:
        dut_engine = topology_obj.players['dut']['engine']
        cli_object = topology_obj.players['dut']['cli']
        with allure.step("Apply port_config.ini and config_db.json"):
                SonicGeneralCli.apply_basic_config(topology_obj, dut_engine, cli_object, setup_name, platform_params)
    except Exception as err:
        raise AssertionError(err)
