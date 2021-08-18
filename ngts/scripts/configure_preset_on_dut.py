import logging
import pytest
import allure
from ngts.constants.constants import SonicConst, InfraConst

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_configure_preset_on_dut(topology_obj, setup_name, platform_params, preset):
    dut_engine = topology_obj.players['dut']['engine']
    cli_object = topology_obj.players['dut']['cli']
    hwsku = platform_params.hwsku
    hostname = cli_object.chassis.get_hostname(dut_engine)
    setup_topo_dir_name = setup_name.replace("_setup", "")
    shared_path = '{}{}{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_topo_dir_name)
    config_db_file = "config_db_{}.json".format(preset)

    with allure.step("Configure preset: {} with HWSKU: {} on switch".format(preset, hwsku)):
        logger.info("Configure preset: {} with HWSKU: {} on switch".format(preset, hwsku))
        command = "sudo sonic-cfggen -H -k {} -p --preset {} > /tmp/config_db.json".format(hwsku, preset)
        dut_engine.run_cmd(command)
        dut_engine.run_cmd("sudo cp /tmp/config_db.json /etc/sonic/config_db.json")

    with allure.step("Update MGMT_INTERFACE on {}".format(config_db_file)):
        logger.info("Update MGMT_INTERFACE on {}".format(config_db_file))
        cli_object.general.update_config_db_metadata_mgmt_ip(dut_engine, setup_topo_dir_name,
                                                             dut_engine.ip, file_name=config_db_file)
    with allure.step("Update METADATA type on {}".format(config_db_file)):
        logger.info("Update METADATA type on {}".format(config_db_file))
        cli_object.general.update_config_db_metadata_router(setup_topo_dir_name, config_db_file)

    with allure.step("Update MGMT_PORT type on {}".format(config_db_file)):
        logger.info("Update MGMT_PORT type on {}".format(config_db_file))
        cli_object.general.update_config_db_metadata_mgmt_port(setup_topo_dir_name, config_db_file)

    with allure.step("Update hostname on {}".format(config_db_file)):
        logger.info("Update hostname on {}".format(config_db_file))
        cli_object.general.update_config_db_hostname(setup_topo_dir_name, hostname, config_db_file)

    with allure.step("Copy the updated {} to switch".format(config_db_file)):
        logger.info("Copy the updated {} to switch".format(config_db_file))
        dut_engine.run_cmd('sudo curl {}/{} -o {}'.format(shared_path, config_db_file,
                                                          SonicConst.CONFIG_DB_JSON_PATH))

    with allure.step("Reboot the switch with the new configuration"):
        logger.info("Reboot the switch with the new configuration")
        dut_engine.reload(['sudo reboot'])
        cli_object.general.verify_dockers_are_up(dut_engine, SonicConst.DOCKERS_LIST)
