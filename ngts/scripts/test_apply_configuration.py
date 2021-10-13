#!/usr/bin/env python
import allure
import logging
import pytest
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.constants.constants import SonicConst, InfraConst


logger = logging.getLogger()


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
        SonicGeneralCli.verify_dockers_are_up(dut_engine,
                                              dockers_list=['swss', 'syncd', 'teamd', 'pmon'])
        copy_copp_config(setup_name, dut_engine)
        with allure.step("Apply port_config.ini and config_db.json"):
                SonicGeneralCli.apply_basic_config(topology_obj, dut_engine, cli_object, setup_name,
                                                   platform_params.platform, platform_params.hwsku)
    except Exception as err:
        raise AssertionError(err)


def copy_copp_config(setup_name, engine):
    """
    Copy COPP config from shared location to DUT
    :param setup_name: setup_name fixture
    :param engine: dut engine object
    """
    if setup_name == 'sonic_simx_r-moose-simx-161':
        copp_config_url = '{}{}{}/{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_name,
                                             SonicConst.COPP_CONFIG)
        engine.run_cmd('sudo curl {} -o {}'.format(copp_config_url, SonicConst.SONIC_CONFIG_FOLDER))
