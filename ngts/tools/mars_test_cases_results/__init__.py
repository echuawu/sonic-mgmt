#!/ngts_venv/bin/python

import os
import json
import logging
import subprocess

from datetime import datetime
from ngts.constants.constants import CliType, DbConstants

logger = logging.getLogger()
ALLURE_REPORT_URL = 'allure_report_url'
SESSION_ID = "session_id"
SETUP_NAME = "setup_name"
MARS_KEY_ID = "mars_key_id"
ALLURE_URL = "allure_url"
DUMP_INFO = "dump_info"
TEST_INSERTED_TIME = "test_inserted_time"
NAME = "name"
RESULT = "result"
SKIP_REASON = "skip_reason"
SKYNET = "skynet"


def pytest_addoption(parser):
    parser.addoption("--disable_exporting_results_to_mars_db", action="store_true", default=False,
                     help="Disable exporting cases results to MARS SQL database")


def create_metadata_dir(session_id, cli_type):
    """
    Create directory for test artifacts in shared location
    :param setup_name: name of the setup
    :param session_id: MARS session id
    :param suffix_path_name: End part of the directory name
    :param cli_type: the type of cli, wether its NVUE or SONIC
    :return: created directory path
    """

    folder_path = DbConstants.CLI_TYPE_PATH_MAPPING.get(cli_type)
    folder_path = os.path.join(folder_path, session_id)
    logger.info("Create folder: {} if it doesn't exist".format(folder_path))
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    logger.info("Created folder - {}".format(folder_path))
    return folder_path


def create_test_record(session_id, setup_name, mars_key_id, test_name, result, skipreason, allure_url,
                       dump_info, test_inserted_time):
    test_record = {}
    test_record.update({SESSION_ID: session_id})
    test_record.update({SETUP_NAME: setup_name})
    test_record.update({MARS_KEY_ID: mars_key_id})
    test_record.update({NAME: test_name})
    test_record.update({RESULT: result})
    test_record.update({SKIP_REASON: skipreason})
    test_record.update({ALLURE_URL: allure_url})
    test_record.update({DUMP_INFO: dump_info})
    test_record.update({TEST_INSERTED_TIME: test_inserted_time})
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
        if hasattr(session.config.option, SETUP_NAME):
            session.config.cache.set(SETUP_NAME, session.config.getoption(SETUP_NAME))
        if hasattr(session.config.option, SKYNET):
            session.config.cache.set(SKYNET, session.config.getoption(SKYNET))


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if config.getoption("disable_exporting_results_to_mars_db"):
        logger.info("Export MARS cases result to SQL database is disabled")
        return

    json_obj = []
    report_url = config.cache.get(ALLURE_REPORT_URL, None)
    session_id = config.cache.get(SESSION_ID, None)
    setup_name = config.cache.get(SETUP_NAME, None)
    mars_key_id = config.cache.get(MARS_KEY_ID, None)
    skynet = config.cache.get(SKYNET, None)
    cli_type = SKYNET if skynet else config.cache.get('CLI_TYPE', CliType.SONIC)
    if valid_tests_data(report_url, session_id, mars_key_id):
        tests_results, tests_skipreason = parse_tests_results(terminalreporter)
        for test_case_name, test_result in tests_results.items():
            now = datetime.now()
            test_inserted_time = now.strftime("%m/%d/%Y %H:%M:%S")
            dump_info = prepare_dump_dest_path(test_case_name, session_id)
            json_obj.append(create_test_record(session_id,
                                               setup_name,
                                               mars_key_id,
                                               test_case_name,
                                               test_result,
                                               tests_skipreason[test_case_name],
                                               report_url,
                                               dump_info,
                                               test_inserted_time))
        logger.debug("Tests results to be exported to SQL DB: {}".format(json_obj))
        dump_json_to_file(json_obj, session_id, mars_key_id, cli_type)
        export_data(session_id, mars_key_id, cli_type)


def dump_json_to_file(json_obj, session_id, mars_key_id, cli_type):
    folder_path = create_metadata_dir(session_id, cli_type)
    json_file_path = os.path.join(folder_path, "{}_mars_sql_data.json".format(mars_key_id))
    logger.info("Dump json test results to file")
    with open(json_file_path, 'w') as f:
        json.dump(json_obj, f)
    logger.info("Result were saved at file: {}".format(json_file_path))


def export_data(session_id, mars_key_id, cli_type):
    export_data_cmd = "/ngts_venv/bin/python /root/mars/workspace/sonic-mgmt/ngts/scripts/export_test_json_to_mars_db.py" \
                      " --session_id={SESSION_ID} --mars_key_id={MARS_KEY_ID} --cli_type={CLI_TYPE} --log-level=INFO "\
        .format(SESSION_ID=session_id, MARS_KEY_ID=mars_key_id, CLI_TYPE=cli_type)
    try:
        logger.info("Exporting json tests data with command:\n{}".format(export_data_cmd))
        subprocess.check_output(export_data_cmd, shell=True)
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
    tests_skipreason = {}
    stats_keys = ['skipped', 'passed', 'failed', 'error']
    for key in stats_keys:
        for test_obj in terminalreporter.stats.get(key, []):
            skipreason = ""
            result = test_obj.outcome
            if key == "skipped":
                result, skipreason = get_skip_type_reason(test_obj)
            tests_results.update({test_obj.nodeid: result})
            tests_skipreason.update({test_obj.nodeid: skipreason})
    return tests_results, tests_skipreason


def get_skip_type_reason(test_obj):

    skipped_flavors = {
        "skipped_rm": ["https://redmine.mellanox.com"],
        "skipped_github": ["https://github.com"],
        "skipped_branch": ["release"],
        "skipped_platform": ["platform", "asic_type"],
        "skipped_topo": ["topo_name", "topo_type", "test requires topology in Mark"]
    }

    _, _, skipreason = test_obj.longrepr
    logger.debug("The skip reason for {} is : {}".format(test_obj.nodeid, skipreason))
    if skipreason.startswith("Skipped: "):
        skipreason = skipreason[9:].replace("'", "")

    skipped_flavor = get_updated_skipped_type(test_obj.outcome, skipped_flavors, skipreason)
    logger.debug("The skip type for {} is : {}".format(test_obj.nodeid, skipped_flavor))
    return skipped_flavor, str(skipreason)


def get_updated_skipped_type(skipped_type, skipped_flavors, skipreason):
    """
    Check if it is one of the defined skip flavor based on the skipreason.
    :param skipped_type: defined skip type
    :param skipped_flavors: the skipped flavor dict.
    :param skipreason: the skip reason
    :return: skip flavor.
    """
    for skipped_flavor, skipreason_keys in skipped_flavors.items():
        for skipreason_key in skipreason_keys:
            if skipreason_key in skipreason:
                return skipped_flavor
    return skipped_type


def prepare_dump_dest_path(test_case_full_name, session_id):
    """
    Prepare the dump of failed test.
    For CI and nightly regression the path is different.
        Nightly dump: the dump will be inside tar file of all the mars session.
                    In this case will be provided session tar file path(the tar will be generated at the end of
                    Mars session) and path to test dump inside this tar file.
        CI: the dump file will not compressed to tar file. Providing  the path to dump file
    :param test_case_full_name: test case full name, tests/push_build_tests/system/test_cpu_ram_hdd_usage.py::
                                                        TestCpuRamHddUsage::test_cpu_usage'
    :param session_id: mars session_id
    :return: string with dump info
        Example:
            In case of CI: '/path/to/dump'
            Regular Mars session: 'mars_tar_file: /path/to/tar_file,
                                   dump_path_in_mars_tar_file':'path/to/dump/into/tar_file'
    """
    dump_dest_info = ''
    test_case_name = test_case_full_name.split('::')[-1]
    dump_dest = os.environ.get(test_case_name, None)
    if dump_dest:
        # in CI run, one of parameters is 'LOG_FOLDER' for dump files.
        # this parameter doesn't contain the 'cases_dumps' directory
        if 'cases_dumps' not in dump_dest:
            dump_dest_info = dump_dest
        else:
            tar_path, dump_file_name = dump_dest.split('cases_dumps')
            tar_file = '{}{}.tgz'.format(tar_path, session_id)
            path_in_tar_file = 'cases_dumps{}'.format(dump_file_name)
            dump_dest_info = 'mars_tar_file: {}, dump_path_in_mars_tar_file: {}'.format(tar_file, path_in_tar_file)
    return dump_dest_info
