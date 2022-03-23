import os
import tarfile
import json
import re
import logging
import errno
from ngts.constants.constants import SonicConst
from ngts.helpers.config_db_utils import save_config_db_json

logger = logging.getLogger()


def get_platform_json(engine_dut, cli_object, fail_if_doesnt_exist=True):
    """
    return a json object of the platform.json file of your setup dut platform
    :param engine_dut: ssh connection to dut
    :param cli_object: cli_object of dut
    :param fail_if_doesnt_exist: if true, raise assertion error in case platform.json doesn't exist,
    if false return an empty dict
    :return: a Json Object of the platform.json file, i.e,
    {'interfaces':
     {'Ethernet0': {'index': '1,1,1,1',
                    'lanes': '0,1,2,3',
                    'breakout_modes': {'1x100G[50G,40G,25G,10G]': ['etp1'],
                                       '2x50G[40G,25G,10G]': ['etp1a', 'etp1b'],
                                       '4x25G[10G]': ['etp1a', 'etp1b', 'etp1c', 'etp1d']}}
     , ...}
    """
    platform_json = {}
    platform = cli_object.chassis.get_platform()
    platform_path = SonicConst.PLATFORM_JSON_PATH.format(PLATFORM=platform)
    platform_detailed_info_output = engine_dut.run_cmd("cat {} ; echo".format(platform_path), print_output=False)
    if re.search('No such file or directory', platform_detailed_info_output):
        if fail_if_doesnt_exist:
            raise AssertionError("no platform.json was found,\n error: {}".format(platform_detailed_info_output))
        else:
            logger.warning("File {} was not found on this version".format(platform_path))
            return platform_json
    platform_json = json.loads(platform_detailed_info_output)
    return platform_json


def get_config_db(engine_dut):
    config_db_json = engine_dut.run_cmd('cat {} ; echo'.format(SonicConst.CONFIG_DB_JSON_PATH), print_output=False)
    return json.loads(config_db_json)


def remove_key_from_config_db(engine_dut, key):
    """
    remove the content of the key from the config_db.json file
    :param engine_dut: ssh engine object
    :param key: key value to specify what should be removed
    :return: the content removed
    """
    config_db_json = get_config_db(engine_dut)
    if key not in config_db_json:
        return {}
    value = config_db_json.pop(key)
    save_config_db_json(engine_dut, config_db_json)
    return value


def add_content_to_config_db(engine_dut, content, key):
    """
    add content to the config_db.json file
    :param engine_dut: ssh engine object
    :param content: add the content to the config db file
    :return: None
    """
    config_db_json = get_config_db(engine_dut)
    config_db_json[key] = content
    save_config_db_json(engine_dut, config_db_json)


def extract_fw_data(fw_pkg_path):
    """
    Extract fw data from updated-fw.tar.gz file
    :param fw_pkg_path: the path to tar.gz file (like /auto/sw_system_project/sonic/platform_fw/updated-fw.tar.gz)
    :return: fw_data in dictionary
    """
    try:
        os.mkdir("/tmp/firmware")
    except OSError as e:
        # if already exists, thats fine
        if not e.errno == errno.EEXIST:
            raise AssertionError(f"Problem in creating temporary directory: /tmp/firmware. \n{e}")
    with tarfile.open(fw_pkg_path, "r:gz") as f:
        f.extractall("/tmp/firmware/")
        with open('/tmp/firmware/firmware.json', 'r') as fw:
            fw_data = json.load(fw)
            return fw_data
