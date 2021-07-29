import os
import json
from ngts.constants.constants import SonicConst

LOCAL_CONFIG_DB_PATH = os.path.join('/tmp', SonicConst.CONFIG_DB_JSON)


def save_config_db_json(engine, config_db_json):
    """
    save json to the config_db.json file
    :param engine: ssh engine object
    :param config_db_json: config db content in json format
    :return: None
    """
    with open(LOCAL_CONFIG_DB_PATH, 'w') as f:
        json.dump(config_db_json, f, indent=4)
        # Python JSON dump misses last newline, so add the newline at the end of the file
        f.write("\n")
    engine.copy_file(source_file=LOCAL_CONFIG_DB_PATH, dest_file=SonicConst.CONFIG_DB_JSON,
                     file_system='/tmp', overwrite_file=True, verify_file=False)
    engine.run_cmd('sudo mv {} {}'.format(LOCAL_CONFIG_DB_PATH, SonicConst.CONFIG_DB_JSON_PATH))
    os.remove(LOCAL_CONFIG_DB_PATH)
