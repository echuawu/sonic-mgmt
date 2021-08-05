#!/ngts_venv/bin/python

import os
import json
import logging

from ngts.constants.constants import InfraConst

logger = logging.getLogger()
ALLURE_REPORT_URL = 'allure_report_url'
SESSION_ID = "session_id"
MARS_KEY_ID = "mars_key_id"
ALLURE_URL = "allure_url"
NAME = "name"
RESULT = "result"


def create_metadata_dir(session_id):
    """
    Create directory for test artifacts in shared location
    :param setup_name: name of the setup
    :param session_id: MARS session id
    :param suffix_path_name: End part of the directory name
    :return: created directory path
    """
    folder_path = os.path.join(InfraConst.METADATA_PATH, session_id)
    logger.info("Create folder: {} if it doesn't exist".format(folder_path))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    logger.info("Created folder - {}".format(folder_path))
    return folder_path


def create_test_record(session_id, mars_key_id, test_name, result, allure_url):
    test_record = {}
    test_record.update({SESSION_ID: session_id})
    test_record.update({MARS_KEY_ID: mars_key_id})
    test_record.update({NAME: test_name})
    test_record.update({RESULT: result})
    test_record.update({ALLURE_URL: allure_url})
    return test_record


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook which are executed after all tests before exist from program
    :param session: pytest buildin
    :param exitstatus: pytest buildin
    """
    if not session.config.getoption("--collectonly"):
        session_id = session.config.option.session_id
        mars_key_id = session.config.option.mars_key_id
        session.config.cache.set(SESSION_ID, session_id)
        session.config.cache.set(MARS_KEY_ID, mars_key_id)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    json_obj = []
    report_url = config.cache.get(ALLURE_REPORT_URL, None)
    session_id = config.cache.get(SESSION_ID, None)
    mars_key_id = config.cache.get(MARS_KEY_ID, None)
    if valid_tests_data(report_url, session_id, mars_key_id):
        tests_results = parse_tests_results(terminalreporter)
        for test_case_name, test_result in tests_results.items():
            json_obj.append(create_test_record(session_id,
                                               mars_key_id,
                                               test_case_name,
                                               test_result,
                                               report_url))
        logger.debug("Tests results to be exported to SQL DB: {}".format(json_obj))
        dump_json_to_file(json_obj, session_id, mars_key_id)
        export_data(session_id, mars_key_id)


def dump_json_to_file(json_obj, session_id, mars_key_id):
    folder_path = create_metadata_dir(session_id)
    json_file_path = os.path.join(folder_path, "{}_mars_sql_data.json".format(mars_key_id))
    logger.info("Damp json test results to file")
    with open(json_file_path, 'w') as f:
        json.dump(json_obj, f)
    logger.info("Result were saved at file: {}".format(json_file_path))


def export_data(session_id, mars_key_id):
    export_data_cmd = "/ngts_venv/bin/python /root/mars/workspace/sonic-mgmt/ngts/scripts/export_test_json_to_mars_db.py" \
                      " --session_id={SESSION_ID} --mars_key_id={MARS_KEY_ID} --log-level=INFO ".format(SESSION_ID=session_id,
                                                                                                        MARS_KEY_ID=mars_key_id)
    try:
        logger.info("Exporting json tests data with command:\n{}".format(export_data_cmd))
        os.popen(export_data_cmd)
    except Exception as e:
        logger.warning("Error: {} has occured, test data might not be exported".format(e))


def valid_tests_data(report_url, session_id, mars_key_id):
    """
    This function return true only if the tests run as part of mars regression and have valid mars key id and session id.
    :param report_url: url of allure report of test
    :param session_id: session id, i.e 1234567
    :param mars_key_id: mars key id, i.e 0.1.1.1.1.3.4.5
    :return: True, if all the parameters mention above are not None
    """
    return report_url and session_id and mars_key_id


def parse_tests_results(terminalreporter):
    """
    return a dict with the parsed tests name and their results
    :param terminalreporter: a pytest plugin
    :return: a dictionary with all the tests that run and their results
    {'tests/push_build_tests/L2/fdb/test_fdb.py::test_push_gate_fdb': 'passed'}
    """
    tests_results = {}
    stats_keys = ['skipped', 'passed', 'failed', 'error']
    for key in stats_keys:
        for test_obj in terminalreporter.stats.get(key, []):
            tests_results.update({test_obj.nodeid: test_obj.outcome})
    return tests_results
