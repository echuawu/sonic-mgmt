import logging
import pytest
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli, ConfigDbJsonConst, InfraConst, SonicConst

logger = logging.getLogger()


@pytest.fixture(scope='function')
def shutdown_ifaces(request):
    """
    Method for get interfaces on the switch required shutdown, i.e. "Ethernet0,Ethernet2"
    :param request: pytest buildin
    :return: interfaces on the switch required shutdown, i.e. "Ethernet0,Ethernet2"
    """
    return request.config.getoption('--shutdown_ifaces')


@pytest.fixture(scope='function')
def preset(request):
    """
    Method for get the configuration setting required on the switch
    :param request: pytest buildin
    :return: the configuration setting required on the switch, i.e. "l2"
    """
    return request.config.getoption('--preset')


@pytest.mark.disable_loganalyzer
def test_shutdown_interfaces_on_dut(topology_obj, setup_name, shutdown_ifaces, preset):
    dut_engine = topology_obj.players['dut']['engine']
    cli_object = topology_obj.players['dut']['cli']
    if shutdown_ifaces != "None":
        interfaces_list = shutdown_ifaces.split(",")
        setup_topo_dir_name = setup_name.replace("_setup", "")
        shared_path = '{}{}'.format(InfraConst.HTTP_SERVER_MARS_TOPO_FOLDER_PATH, setup_topo_dir_name)
        config_db_file = "config_db_{}.json".format(preset)
        config_db_json = SonicGeneralCli.get_config_db(dut_engine)
        for interface in interfaces_list:
            config_db_json[ConfigDbJsonConst.PORT][interface][ConfigDbJsonConst.ADMIN_STATUS] = "down"
        SonicGeneralCli.create_extended_config_db_file(setup_topo_dir_name, config_db_json, file_name=config_db_file)
        dut_engine.run_cmd('sudo curl {}/{} -o {}'.format(shared_path, config_db_file,
                                                          SonicConst.CONFIG_DB_JSON_PATH))
        all_dut_ports = cli_object.interface.parse_ports_aliases_on_sonic(dut_engine).keys()
        ports_expected_to_be_up = set(all_dut_ports).difference(interfaces_list)
        cli_object.general.reload_flow(dut_engine, ports_list=ports_expected_to_be_up, topology_obj=topology_obj)
        cli_object.general.check_link_state(dut_engine, ifaces=interfaces_list, expected_status="down")
