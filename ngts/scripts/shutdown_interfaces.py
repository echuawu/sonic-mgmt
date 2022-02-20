import logging
import pytest
import allure
from ngts.cli_wrappers.sonic.sonic_general_clis import InfraConst, SonicConst

logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
def test_shutdown_interfaces_on_dut(topology_obj, setup_name, preset):

    dut_engine = topology_obj.players['dut']['engine']
    cli_object = topology_obj.players['dut']['cli']
    ports_status = cli_object.interface.parse_interfaces_status(dut_engine)
    shutdown_ifaces = [port for port, port_status_dict in ports_status.items() if port_status_dict['Oper'] == 'down']
    ports_expected_to_be_up = [port for port, port_status_dict in ports_status.items()
                               if port_status_dict['Oper'] == 'up']
    if shutdown_ifaces:
        setup_topo_dir_name = setup_name.replace("_setup", "")
        shared_path = '{}{}'.format(InfraConst.HTTP_SERVER_MARS_TOPO_FOLDER_PATH, setup_topo_dir_name)
        config_db_file = "config_db_{}.json".format(preset)

        with allure.step("Set interfaces {} as down in config db file: {}".format(shutdown_ifaces, config_db_file)):
            for interface in shutdown_ifaces:
                cli_object.interface.disable_interface(dut_engine, interface)
            cli_object.general.save_configuration(dut_engine)
            config_db_json = cli_object.general.get_config_db(dut_engine)
            cli_object.general.create_extended_config_db_file(setup_topo_dir_name, config_db_json,
                                                              file_name=config_db_file)

        with allure.step("Load {} to switch".format(config_db_file)):
            dut_engine.run_cmd('sudo curl {}/{} -o {}'.format(shared_path, config_db_file,
                                                              SonicConst.CONFIG_DB_JSON_PATH))

        with allure.step("Reboot the switch with the new configuration and check ports status"):
            cli_object.general.reload_flow(dut_engine, ports_list=ports_expected_to_be_up, topology_obj=topology_obj)
            cli_object.general.check_link_state(dut_engine, ifaces=shutdown_ifaces, expected_status="down")
