import allure
import logging
import pytest
import random
import re
import copy
from pprint import pprint
from retry import retry
from deepdiff import DeepDiff
from ngts.constants.constants import InfraConst, SonicConst


logger = logging.getLogger()

BUFFER_PG = "BUFFER_PG"
BUFFER_PORT_EGRESS_PROFILE_LIST = "BUFFER_PORT_EGRESS_PROFILE_LIST"
BUFFER_PORT_INGRESS_PROFILE_LIST = "BUFFER_PORT_INGRESS_PROFILE_LIST"
BUFFER_QUEUE = "BUFFER_QUEUE"
CABLE_LENGTH = "CABLE_LENGTH"
AZURE = "AZURE"
ROCE = "ROCE"
PORT_QOS_MAP = "PORT_QOS_MAP"
QUEUE = "QUEUE"
KEYS_TO_EXTRACT = [BUFFER_PG, BUFFER_PORT_EGRESS_PROFILE_LIST,
                   BUFFER_PORT_INGRESS_PROFILE_LIST, BUFFER_QUEUE,
                   CABLE_LENGTH, PORT_QOS_MAP, QUEUE]


def generate_config_db_without_qos_on_ports(config_db_json, tested_ports, is_doroce_configuration_enabled):
    """
    :param config_db_json: a JSON object of configuration currently on DUT
    :param tested_ports: a list of ports, i.e ['Ethernet4', 'Ethernet8']
    :param is_doroce_configuration_enabled: the flag if doroce is configured
    :return: updated config_db_json without Qos configuration on tested_ports
    """
    regex_template = r"{port}\|\d+-*\d*|{port}$"
    qos_profile_name = ROCE if is_doroce_configuration_enabled else AZURE
    for key_to_extract in KEYS_TO_EXTRACT:
        if key_to_extract == CABLE_LENGTH:
            for port in tested_ports:
                config_db_json[CABLE_LENGTH][qos_profile_name].pop(port)
        else:
            for tested_port in tested_ports:
                keys_to_remove = []
                for key, val in config_db_json[key_to_extract].items():
                    if re.match(regex_template.format(port=tested_port), key):
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    config_db_json[key_to_extract].pop(key)
    return config_db_json


def get_dut_ports(topology_obj):
    return topology_obj.players_all_ports['dut']


@pytest.fixture(autouse=True, scope='session')
def tested_ports(topology_obj):
    """
    Function selects randomly  2 ports, and returns those ports as list.
    :param topology_obj: topology object fixture
    :return: a list of tested ports, i.e, ['Ethernet52', 'Ethernet56']
    """
    tested_ports_list = random.sample(get_dut_ports(topology_obj), k=2)
    return tested_ports_list


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('tests functionality of CLI command "sudo config qos reload --ports"')
def test_qos_reload_ports(topology_obj, engines, cli_objects, setup_name, tested_ports):
    """
    This tests checks the functionality of CLI command "sudo config qos reload --ports",
    the documentation for this command can be found at:
    https://confluence.nvidia.com/display/SW/Design+-+config+qos+reload+--ports

    the test removes qos and buffers configuration from random ports,
    and the checks that the qos and buffers configuration is restored after
    "sudo config qos reload --ports" is configured.

    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param cli_objects: cli_objects fixture
    :param setup_name: setup_name fixture
    :param tested_ports: a list of ports to be tested
    :return: raise assertion error in case of test failure
    """
    dut_engine = engines.dut
    cli_object = cli_objects.dut
    shared_path = '{}{}{}'.format(InfraConst.HTTP_SERVER, InfraConst.MARS_TOPO_FOLDER_PATH, setup_name)
    origin_config_db = cli_object.general.get_config_db()

    with allure.step(f"Generate config_db.json file without Qos configuration for ports: {tested_ports}"):
        logger.info(f"Generate config_db.json file without Qos configuration for ports: {tested_ports}")
        config_db_without_qos_on_ports = \
            generate_config_db_without_qos_on_ports(copy.deepcopy(origin_config_db),
                                                    tested_ports,
                                                    cli_object.doroce.is_doroce_configuration_enabled())

    tested_config_db_file_name = "test_qos_reload_ports_conf.json"
    with allure.step(f"Save config_db.json at {shared_path}/{tested_config_db_file_name}"):
        logger.info(f"Save config_db.json at {shared_path}/{tested_config_db_file_name}")
        cli_object.general.create_extended_config_db_file(setup_name, config_db_without_qos_on_ports,
                                                          file_name=tested_config_db_file_name)

    with allure.step(f"Copy config_db.json to dut"):
        logger.info(f"Copy config_db.json to dut")
        dut_engine.run_cmd(f'sudo curl {shared_path}/{tested_config_db_file_name} -o { SonicConst.CONFIG_DB_JSON_PATH}',
                           validate=True)

    with allure.step(f"Reload the configuration"):
        logger.info(f"Reload the configuration")
        cli_object.general.reload_flow(topology_obj=topology_obj, reload_force=False)

    with allure.step(f"Configure QOS on ports: {tested_ports} with CLI command"):
        logger.info(f"Configure QOS on ports: {tested_ports} with CLI command")
        cli_object.qos.reload_qos(ports_list=tested_ports)

    with allure.step(f"Save configuration on DUT"):
        logger.info(f"Save configuration on DUT")
        cli_object.general.save_configuration()

    compare_config_db_after_qos_reload_ports(cli_object, origin_config_db)

    with allure.step(f"Check ports: {tested_ports} status"):
        logger.info(f"Check ports: {tested_ports} status")
        cli_object.interface.check_ports_status(ports_list=tested_ports, expected_status='up')


@retry(Exception, tries=12, delay=10)
def compare_config_db_after_qos_reload_ports(cli_object, origin_config_db):
    with allure.step(f"Compare the config_db.json after CLI command to origin config_db.json"):
        logger.info(f"Compare the config_db.json after CLI command to origin config_db.json")
        config_db_after_qos_reload_ports = cli_object.general.get_config_db()
        keys_to_compare = KEYS_TO_EXTRACT
        for key in keys_to_compare:
            with allure.step(f"Compare key {key} after CLI command to origin config_db.json"):
                expected_dict = origin_config_db[key]
                actual_dict = config_db_after_qos_reload_ports[key]
                ddiff = DeepDiff(actual_dict, expected_dict)
                assert not ddiff, f"Test expected QoS configuration to be restored with CLI, " \
                                  f"but config_db.json for key: {key} is different: {pprint(ddiff)}"
