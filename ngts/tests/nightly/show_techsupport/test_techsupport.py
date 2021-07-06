import allure
import os
import pytest
import time
import re
import logging
import tarfile

logger = logging.getLogger(__name__)

SUCCESS_CODE = 0

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
FILES_DIR = os.path.join(BASE_DIR, 'files')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')


@pytest.fixture(autouse=True)
def ignore_techsupport_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "log_analyzer_techsupport_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


def test_techsupport_mellanox_sdk_dump(engines, loganalyzer):
    duthost = engines.dut

    with allure.step('Copy to dut a script that triggers SDK health event'):
        cp_sdk_event_trigger_script_to_dut_syncd(duthost)

    logger.debug("Running show techsupport ... ")
    with allure.step('STEP1: Count number of SDK extended dumps at dut before test'):
        number_of_sdk_error_before = count_sdk_dumps(duthost)

    with allure.step('STEP2: Trigger SDK health event at dut'):
        duthost.run_cmd('docker exec -it syncd python mellanox_sdk_trigger_event_script.py')
        loganalyzer.expect_regex.extend(["Health event happened, severity"])

    with allure.step('STEP3: Count number of SDK extended dumps at dut after event occurred'):
        number_of_sdk_error_after = count_sdk_dumps(duthost)

    with allure.step('Validate that the tecsupport file contain one more SDK extended dump'):
        assert number_of_sdk_error_after == number_of_sdk_error_before + 1


def cp_sdk_event_trigger_script_to_dut_syncd(engine):
    dst = os.path.join('/tmp', 'mellanox_sdk_trigger_event_script.py')
    engine.copy_file(source_file=os.path.join(FILES_DIR, 'mellanox_sdk_trigger_event_script.py'),
                     dest_file='mellanox_sdk_trigger_event_script.py',
                     file_system='/tmp',
                     direction='put'
    )
    engine.run_cmd('docker cp {} {}'.format(dst, 'syncd:/'))


def count_sdk_dumps(engine):
    sdk_dump_dir = 'sai_sdk_dump'
    sdk_file_pattern = 'sai-dfw-.*'

    output_lines = engine.run_cmd('show techsupport').split('\n')

    tar_file = output_lines[len(output_lines)-1]
    tarball_file_name = str(tar_file.replace('/var/dump/', ''))
    tarball_dir_name = str(tarball_file_name.replace('.tar.gz', ''))

    sdk_dump_pattern = '{}/{}/{}'.format(tarball_dir_name, sdk_dump_dir, sdk_file_pattern )

    engine.copy_file(source_file=tar_file, dest_file=tarball_file_name, file_system='/tmp/', direction='get')

    t = tarfile.open(tarball_file_name, "r")

    filenames = t.getnames()
    r = re.compile(sdk_dump_pattern)

    after_list = list(filter(r.match, filenames))

    engine.run_cmd("rm -rf {}".format(tar_file))
    return len(after_list)

