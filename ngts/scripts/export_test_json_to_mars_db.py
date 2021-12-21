#!/ngts_venv/bin/python
import os
import sys
import json
import argparse
import logging
import time

path = os.path.abspath(__file__)
sonic_mgmt_path = path.split('/ngts/')[0]
sys.path.append(sonic_mgmt_path)

from ngts.tools.mars_test_cases_results.Write_to_db import MarsConnectDB  # noqa: E402
from ngts.tools.mars_test_cases_results.mars_json_handler import JsonHandler  # noqa: E402
from ngts.constants.constants import InfraConst  # noqa: E402

sys.path.append(sonic_mgmt_path + "/sonic-tool")
from sonic_ngts.infra.mars.mars import get_mars_session_resource  # noqa: E402

logger = logging.getLogger()


def set_logger(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')


def init_parser():
    description = ('Functionality of the script: \n'
                   'Exporting json information located at {}.\n'
                   'for test with mars_key_id and session_id, which are arguments provided to the scrip.\n'.format(InfraConst.METADATA_PATH))

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--mars_key_id', dest='mars_key_id', default=None, help='test mars key id, e.g. 1.0.0.1.3.4.7')
    parser.add_argument('--session_id', dest='session_id', default=None, help='session id, e.g. 123456')
    parser.add_argument('-l', '--log-level', dest='log_level', default=logging.INFO, help='log verbosity')
    args, unknown = parser.parse_known_args()

    if unknown:
        raise Exception("unknown argument(s): {}".format(unknown))
    return args


def write_json_into_mars_db(json_file_path):
    write_db = MarsConnectDB()
    with open(json_file_path, 'r') as f:
        json_data = json.load(f)
        json_handler = JsonHandler(json_data)
        write_db.write_json_to_db(json_handler.all_data)


def export_json_to_mars_db(session_id, mars_key_id):
    json_file_path = os.path.join(InfraConst.METADATA_PATH, session_id, "{}_mars_sql_data.json".format(mars_key_id))
    if os.path.exists(json_file_path):
        if is_mars_session_still_running(session_id):
            logger.info('Exporting json data at file: {} to MARS SQL DB'.format(json_file_path))
            write_json_into_mars_db(json_file_path)
            logger.info("Data was exported successfully!")
    else:
        logger.warning("Json file: {} doesn't exist - No data was exported".format(json_file_path))


def is_mars_session_still_running(session_id):
    """
    Check that MARS session is running. In case when we can not get session status - assume that session is running
    :param session_id: session id, e.g. 123456
    :return: True if mars session is still running
    """
    is_running = False
    try:
        session_status = get_mars_session_resource(session_id).find("STATUS").text
        if 'Running' in session_status:
            is_running = True
    except Exception as err:
        logger.error('Can not get MARS session status, assume that session is running. Got error: {}'.format(err))
        is_running = True

    return is_running


if __name__ == "__main__":
    args = init_parser()
    set_logger(args.log_level)
    export_json_to_mars_db(args.session_id, args.mars_key_id)
