#!/usr/bin/env python
"""
Analyze SONiC logs with defined checkers and expected results.

Command example:

PYTHONPATH=/devts:/root/mars/workspace/sonic-mgmt/ /ngts_venv/bin/pytest --setup_name=r-leopard-01_setup --rootdir=/root/mars/workspace/sonic-mgmt//ngts
 -c /root/mars/workspace/sonic-mgmt//ngts/pytest.ini --log-level=INFO --disable_loganalyzer --clean-alluredir --alluredir=/tmp/allure-results
/root/mars/workspace/sonic-mgmt/ngts/scripts/log_profiler/log_profiler.py --test_files fast_reboot --syslog_start_line /sbin/kexec
 --sairedis_start_line INIT_VIEW /root/mars/workspace/sonic-mgmt/ngts/scripts/log_profiler/log_profiler.py

This script is executed on the STM node. It establishes SSH connection to the DUT and gets the two latest 'syslog' and 'sairedis.rec'
files output. Purpose is to check software components performance by calculating execution time between log prints timestamps.
The execution time will be the time difference between two log prints patterns provided by the checker and the result criteria determined
by the expected result of this checker (by platform).

The checker will provide:
"check_type": The type of test we run on the log.
"first_pattern": First pattern to search in the log.
"second_pattern": Second pattern to search in the log.
"file_to_parse": Which file to parse syslog/sairedis.
"debug_hint": A string to print as part of the test result if it fail, to help understanding what might be wrong.
"word_pattern_offset": A word offset in a log file line which help to compare multiple lines with one checker (for 'elapsed_time_between_two_patterns_iterate' type)

Example:

Checker:
    "ASIC_RESET_TIME": {
        "check_type": "elapsed_time_between_two_patterns",
        "first_pattern": "ready for reset",
        "second_pattern": "ready after reset",
        "file_to_parse": "syslog",
        "debug_hint": "Reset the ASIC execution time is longer than expected",
        "word_pattern_offset": "N/A"
    }

Expected Result:
    "MSN2700": {
        "ASIC_RESET_TIME": "2"
    }

The test will search for two lines in the log(file_to_parse) - one contain first pattern and the second contain second pattern.
Then it will calculate the time diff between the two lines and consider it as the test result value.
If the result value is higher than expected result value the test will fail.

Output example:

Fail - Test ASIC_RESET_TIME failed with result: 2.044028, Expected result is: 2.0, Reason: Reset the ASIC execution time is longer than expected
Pass - Test ASIC_RESET_TIME passed with result: 1.535945, Expected result is: 2.0

Supported checkers:

"elapsed_time_between_first_to_last_one_pattern" - Elapsed time between first and last pattern printed to the log. This pattern will appear more than once,
the test will measure elapsed time between first and last.

"elapsed_time_between_first_to_last_two_patterns" - Elapsed time between two patterns printed to the log. Each pattern will appear more than once, this
test will measure elapsed time between first appearance of the first pattern and last appearance of the second pattern.

"elapsed_time_between_two_patterns" - Elapsed time between two patterns printed to the log.

"elapsed_time_between_two_patterns_iterate" - Elapsed time between two patterns printed to the log with a shared word multiple times. This test will
iteratively measure elapsed time between appearance of the first pattern and appearance of the second pattern by a shared word printed on both lines,
for example ADMIN to OPER state for all interfaces.
Example of one iteration would be the time elapsed between admin to oper up on interface 0x1003D.

"presence" - Check that a certain pattern does not appear in the log.

"""

# Builtin libs
import argparse
import pytest
import os
import json
import allure
import logging
from datetime import datetime

logger = logging.getLogger()

timestamp_translator = {"syslog": "%b %d %H:%M:%S.%f",
                        "sairedis": "%Y-%m-%d.%H:%M:%S.%f"}

log_file_path_dict = {"syslog": "/var/log/",
                      "sairedis.rec": "/var/log/swss/"}


def elapsed_time_between_two_patterns(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut):
    first_pattern_time_stamp = None
    second_pattern_time_stamp = None

    for line in log_to_parse:
        if first_pattern in line:
            date_string = get_date_string(file_to_parse, line)
            first_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
            break
    if not first_pattern_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, first_pattern))
        return

    for line in log_to_parse:
        if second_pattern in line:
            date_string = get_date_string(file_to_parse, line)
            second_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
            break
    if not second_pattern_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, second_pattern))
        return

    expected_result = float(expected_results_data[platform][test])
    time_diff = second_pattern_time_stamp - first_pattern_time_stamp
    if time_diff.total_seconds() > expected_result:
        test_fail_elements.append("Test {} failed with result: {}, Expected result is: {}, Reason: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test]), debug_hint))
    else:
        test_pass_elements.append("Test {} passed with result: {}, Expected result is: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test])))


def presence(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut):
    for line in log_to_parse:
        if first_pattern in line:
            test_fail_elements.append("Test {} failed, pattern [ {} ] appeared in the log".format(test, first_pattern))
            return

    test_pass_elements.append("Test {} passed, pattern [ {} ] did not appear in the log".format(test, first_pattern))


def elapsed_time_between_first_to_last_one_pattern(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut):
    pattern_first_time_stamp = None
    pattern_second_time_stamp = None

    # Exception for NEIGHBOR_ENTRIES_CREATION_TIME check, since neighbors can be created after fast-reboot already finished.
    # In this case we would like to ignore these neighbors and avoid missleading results.
    # Each neighbor created after the directly connected neighbors can be ignored.
    if "NEIGHBOR_ENTRIES_CREATION_TIME" in test:
        first_neighbor_found = False
        neighbors_ip_lines = dut.run_cmd("redis-cli -n 4 keys '*' | grep BGP_NEIGHBOR", validate=True, print_output=False).splitlines()
        neighbors_ip_list = []
        for neighbor_ip_line in neighbors_ip_lines:
            neighbors_ip_list.append(neighbor_ip_line.split('|')[1])
        if not len(neighbors_ip_list):
            test_fail_elements.append("Test {} failed, No directly connected neighbors found".format(test))
            return

    for line in log_to_parse:
        if first_pattern in line:
            date_string = get_date_string(file_to_parse, line)
            if pattern_first_time_stamp is None:
                pattern_first_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
            else:
                if "NEIGHBOR_ENTRIES_CREATION_TIME" in test:
                    if any(neighbor_ip in line for neighbor_ip in neighbors_ip_list):
                        first_neighbor_found = True
                        pattern_second_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
                        continue
                    if first_neighbor_found and "DST_MAC_ADDRESS" in line:
                        continue
                    if first_neighbor_found:
                        break

                pattern_second_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
    if not pattern_first_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, first_pattern))
        return

    if not pattern_second_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] appeared only once in the log".format(test, first_pattern))
        return

    expected_result = float(expected_results_data[platform][test])
    time_diff = pattern_second_time_stamp - pattern_first_time_stamp
    if time_diff.total_seconds() > expected_result:
        test_fail_elements.append("Test {} failed with result: {}, Expected result is: {}, Reason: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test]), debug_hint))
    else:
        test_pass_elements.append("Test {} passed with result: {}, Expected result is: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test])))


def elapsed_time_between_first_to_last_two_patterns(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut):
    first_pattern_time_stamp = None
    second_pattern_time_stamp = None

    for line in log_to_parse:
        if first_pattern in line:
            date_string = get_date_string(file_to_parse, line)
            first_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
            break
    if not first_pattern_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, first_pattern))
        return

    for line in log_to_parse:
        if second_pattern in line:
            date_string = get_date_string(file_to_parse, line)
            second_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])
    if not second_pattern_time_stamp:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, second_pattern))
        return

    expected_result = float(expected_results_data[platform][test])
    time_diff = second_pattern_time_stamp - first_pattern_time_stamp
    if time_diff.total_seconds() > expected_result:
        test_fail_elements.append("Test {} failed with result: {}, Expected result is: {}, Reason: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test]), debug_hint))
    else:
        test_pass_elements.append("Test {} passed with result: {}, Expected result is: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test])))


def elapsed_time_between_two_patterns_iterate(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut):
    first_pattern_lines = []
    second_pattern_lines = []
    first_pattern_time_stamp = None
    second_pattern_time_stamp = None

    expected_result = float(expected_results_data[platform][test])

    for line in log_to_parse:
        if first_pattern in line:
            first_pattern_lines.append(line)
        elif second_pattern in line:
            second_pattern_lines.append(line)

    if len(first_pattern_lines) == 0:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, first_pattern))
        return
    if len(second_pattern_lines) == 0:
        test_fail_elements.append("Test {} failed, pattern [ {} ] did not appear in the log".format(test, second_pattern))
        return

    for first_pattern_line in first_pattern_lines:
        two_patterns_match = False
        # Get shared word from line by offset param and remove ','
        shared_word = str(first_pattern_line.split()[int(word_pattern_offset)]).replace(',', '')
        # Replace lowercase letters with uppercase letters
        shared_word = shared_word.upper()

        date_string = get_date_string(file_to_parse, first_pattern_line)
        first_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])

        for second_pattern_line in second_pattern_lines:
            if shared_word in second_pattern_line:
                date_string = get_date_string(file_to_parse, second_pattern_line)
                second_pattern_time_stamp = datetime.strptime(date_string, timestamp_translator[file_to_parse])

                time_diff = second_pattern_time_stamp - first_pattern_time_stamp
                if time_diff.total_seconds() > expected_result:
                    test_fail_elements.append("Test {} failed with result: {}, Expected result is: {}, Shared word: {}, Reason: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test]), shared_word, debug_hint))
                    two_patterns_match = True
                    break
                else:
                    test_pass_elements.append("Test {} passed with result: {}, Expected result is: {}, Shared word: {}".format(test, str(time_diff.total_seconds()), float(expected_results_data[platform][test]), shared_word))
                    two_patterns_match = True
                    break
            else:
                continue

        # If inner loop finished, the shared word couldn't be found
        if not two_patterns_match:
            test_fail_elements.append("Test {} failed, shared word [ {} ] didn't appear in any of pattern [ {} ] lines".format(test, shared_word, second_pattern))


def get_log_lines(log_file_name, log_start_pattern, dut):
    log = ""
    test_log_files = []
    dut_log_files = dut.run_cmd("sudo ls -l " + log_file_path_dict[log_file_name], validate=True, print_output=False)

    log_file_suffix_list = ['.3.gz', '.2.gz', '.1', '']
    for log_file_suffix in log_file_suffix_list:
        if log_file_name + log_file_suffix in dut_log_files:
            test_log_files.append(log_file_name + log_file_suffix)

    for log_file in test_log_files:
        cmd = 'zcat' if 'gz' in log_file else 'cat'
        log = log + dut.run_cmd("sudo " + cmd + " " + log_file_path_dict[log_file_name] + log_file, validate=True, print_output=False)

    log_lines = log.splitlines()
    log_start_offset = None

    for i in range(0, len(log_lines)):
        if log_start_pattern in log_lines[i]:
            log_start_offset = i

    if log_start_offset is None:
        raise AssertionError("Could not find start test reference pattern in any " + log_file_name + " lines, pattern:[{}]".format(log_start_pattern))

    if log_start_offset != 0:
        del log_lines[0: log_start_offset]

    return log_lines


def load_test_files(test_data_files_path):
    try:
        with open(test_data_files_path + 'checkers.json') as checkers_file:
            checkers_data = json.load(checkers_file)
        checkers_file.close()

        with open(test_data_files_path + 'expected_results.json') as expected_results_file:
            expected_results_data = json.load(expected_results_file)
        expected_results_file.close()

        return checkers_data, expected_results_data
    except Exception as e:
        raise AssertionError(e)


def get_date_string(file_to_parse, line):
    if file_to_parse == "syslog":
        date_string = ' '.join(line.split()[:3])
    else:
        date_string = line.split('|')[0]

    return date_string


def test_run_log_profiler(topology_obj, test_files, syslog_start_line, sairedis_start_line):

    with allure.step('Starting log profiler...'):
        test_data_files_path = os.path.dirname(os.path.abspath(__file__)) + '/' + test_files + '/'
        dut = topology_obj.players['dut']['engine']
        test_pass_elements = []
        test_fail_elements = []

    with allure.step('Fetching platform name from DUT'):
        platform = dut.run_cmd("cat /sys/devices/virtual/dmi/id/product_name", validate=True, print_output=False)

    with allure.step('Parsing syslog files'):
        # Parse syslog files into lines object from beggining of test
        syslog_lines = get_log_lines("syslog", syslog_start_line, dut)

    with allure.step('Parsing sairedis files'):
        # Parse sairedis files into lines object from beggining of test
        sairedis_lines = get_log_lines("sairedis.rec", sairedis_start_line, dut)

    with allure.step('Loading test files'):
        # Load test list, arguments and expected results data
        checkers_data, expected_results_data = load_test_files(test_data_files_path)

    # If platform is not covered in the expected results file - fallback to default results
    if platform not in expected_results_data.keys():
        platform = "DEFAULT"

    # Tests loop
    with allure.step('Running profiler loop'):
        for test, arguments in checkers_data.items():
            check_type = arguments["check_type"]
            first_pattern = arguments["first_pattern"]
            second_pattern = arguments["second_pattern"]
            file_to_parse = arguments["file_to_parse"]
            debug_hint = arguments["debug_hint"]
            word_pattern_offset = arguments["word_pattern_offset"]
            if file_to_parse == "syslog":
                log_to_parse = syslog_lines
            else:
                log_to_parse = sairedis_lines

            with allure.step('Running profiler for: {}'.format(test)):
                # Test call wrapper
                eval('{check_type}(check_type, first_pattern, second_pattern, file_to_parse, debug_hint, word_pattern_offset, log_to_parse, \
                                    expected_results_data, platform, test, test_pass_elements, test_fail_elements, dut)'.format(check_type=check_type))

    with allure.step('Gather results summary'):
        for pass_result in test_pass_elements:
            logger.info(pass_result)

        for fail_result in test_fail_elements:
            logger.error(fail_result)

    if test_fail_elements:
        pytest.fail("Some checkers have failed, please check the profiler log")


if __name__ == "__main__":
    main()
