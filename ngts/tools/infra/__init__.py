import pytest
import pathlib
import os
import sys
import logging
import json
import re

from ngts.constants.constants import InfraConst, PytestConst

logger = logging.getLogger()
DEVICE_PLATFORM_INFO_PATH = os.path.join(os.path.dirname(__file__), '../../common/device_platform_info.json')
INVENTORY_FILE_PATH = os.path.join(os.path.dirname(__file__), '../../../ansible/inventory')


@pytest.fixture(scope='session', autouse=True)
def session_id(request):
    """
    Get MARS session id from environment variables
    :return: session id
    """
    session_id = request.config.getoption('--session_id')
    if not session_id:
        session_id = ''
    logger.info("SESSION_ID = '{}'".format(session_id))
    os.environ[InfraConst.ENV_SESSION_ID] = session_id
    return session_id


@pytest.fixture(scope='session', autouse=True)
def dumps_folder(setup_name, session_id, topology_obj):
    """
    Get test artifact folder from environment variables or create according to setup parameters.
    Relies on 'session_id' fixture.
    :return: dumps folder
    """
    env_log_folder = os.environ.get(InfraConst.ENV_LOG_FOLDER)
    if not env_log_folder:  # default value is empty string, defined in steps file
        env_log_folder = create_result_dir(setup_name, session_id, InfraConst.CASES_DUMPS_DIR, topology_obj)
        os.environ[InfraConst.ENV_LOG_FOLDER] = env_log_folder
    return env_log_folder


@pytest.fixture(scope='session')
def log_folder(setup_name, session_id, topology_obj):
    """
    Get test artifact folder from environment variables or create according to setup parameters.
    Relies on 'session_id' fixture.
    :return: log folder
    """
    env_log_folder = os.environ.get(InfraConst.ENV_LOG_FOLDER)
    if not env_log_folder:  # default value is empty string, defined in steps file
        env_log_folder = create_result_dir(setup_name, session_id, InfraConst.CASES_SYSLOG_DIR, topology_obj)
    return env_log_folder


def create_result_dir(setup_name, session_id, suffix_path_name, topology_obj):
    """
    Create directory for test artifacts in shared location
    :param setup_name: name of the setup
    :param session_id: MARS session id
    :param suffix_path_name: End part of the directory name
    :return: created directory path
    """
    player_info = topology_obj.players['dut']
    if player_info['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE'] == "NVUE":
        folder_path = '/'.join([InfraConst.NVOS_REGRESSION_SHARED_RESULTS_DIR, setup_name, session_id, suffix_path_name])
    else:
        folder_path = '/'.join([InfraConst.REGRESSION_SHARED_RESULTS_DIR, setup_name, session_id, suffix_path_name])
    logger.info("Create folder: {} if it doesn't exist".format(folder_path))
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    logger.info("Created folder - {}".format(folder_path))
    return folder_path


def get_platform_info(topology_obj):
    hostname = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
    platform_info = get_platform_info_from_file(hostname)
    if not platform_info:
        platform_info = get_platform_info_from_noga(topology_obj)
        update_platform_info_files(hostname, platform_info)
    return platform_info


def get_platform_info_from_file(hostname):
    with open(DEVICE_PLATFORM_INFO_PATH, 'r') as platform_info_f:
        platform_info = json.load(platform_info_f)
    return platform_info.get(hostname, None)


def get_platform_info_from_noga(topology_obj):
    switch_attributes = topology_obj.players['dut']['attributes'].noga_query_data['attributes']
    devinfo = get_devinfo(switch_attributes)
    try:
        show_platform_summary_dict = json.loads(devinfo)
    except json.decoder.JSONDecodeError:
        err_msg = 'NOGA Attribute Devdescription is empty! Fetched data: {}' \
                  ' It should look like: {"hwsku":"ACS-MSN3700","platform":' \
                  '"x86_64-mlnx_msn3700-r0"}'.format(devinfo)
        raise Exception(err_msg)
    return show_platform_summary_dict


def update_platform_info_files(hostname, platform_params, update_inventory=False):
    platform_params = {k.lower(): v for k, v in platform_params.items()}
    platform_params = {"_".join(k.split()): v for k, v in platform_params.items()}
    if "asic" in platform_params:
        value = platform_params.pop("asic")
        platform_params["asic_type"] = value
    with open(DEVICE_PLATFORM_INFO_PATH, "r") as platform_info_f:
        data = json.load(platform_info_f)
    data.update({hostname: platform_params})
    with open(DEVICE_PLATFORM_INFO_PATH, "w") as platform_info_f:
        json.dump(data, platform_info_f)

    if update_inventory:
        pattern = r"({}.*sonic_hwsku=)(\S*)".format(hostname)
        replacement = r"\1{}".format(platform_params["hwsku"])
        with open(INVENTORY_FILE_PATH, "r") as inventory_file:
            inventory_data = inventory_file.read()
            inventory_data = re.sub(pattern, replacement, inventory_data)
        with open(INVENTORY_FILE_PATH, "w") as inventory_file:
            inventory_file.write(inventory_data)


def get_devinfo(switch_attributes):
    next_key = 'BF Switch' if is_sonic_dpu(switch_attributes) else 'Specific'
    return switch_attributes[next_key]['devdescription']


def is_sonic_dpu(switch_attributes):
    return 'BF Switch' in switch_attributes


def is_test_skipped(request, test_name):
    is_test_should_skip = False
    found_test_in_test_items = False
    for test_item in request.session.items:
        if test_item.name == test_name:
            found_test_in_test_items = True
            for marker in test_item.own_markers:
                if marker.name == 'skip':
                    is_test_should_skip = True
                    break
        if is_test_should_skip:
            break

    if not found_test_in_test_items:
        is_test_should_skip = True

    return is_test_should_skip


def is_deploy_run():

    is_deploy_test_run = False
    for item in sys.argv:
        if PytestConst.DEPLOY_TEST_FILE_NAME in item:
            is_deploy_test_run = True
            break

    return is_deploy_test_run


def update_sys_path_by_community_plugins_path():
    path = os.path.abspath(__file__)
    sonic_mgmt_path = path.split('/ngts/')[0]
    community_plugins_path = '/tests/common'
    full_path_to_community_plugins = sonic_mgmt_path + community_plugins_path
    if full_path_to_community_plugins not in sys.path:
        sys.path.append(full_path_to_community_plugins)
